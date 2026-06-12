#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""布局同步一致性验证脚本。



验证 layout.json 与 DAG JSON 的结构一致性：

- section 结构完整性

- input 变量引用有效性

- output 引用有效性

- 覆盖度统计



可在 CI 或 pre-commit 中运行。



用法:

    python tools/validate_layout_sync.py

    python tools/validate_layout_sync.py --json  # JSON 格式输出

    python tools/validate_layout_sync.py --exit-zero  # 忽略错误退出码

"""

from __future__ import annotations


import json

import sys

from pathlib import Path

from typing import Any


_VALID_SECTION_TYPES = frozenset({"inputs", "outputs", "widget"})


ADAPTER_ROOT = Path(__file__).resolve().parent.parent / "framework" / "adapters" / "endfield"

DAG_PATH = (
    Path(__file__).resolve().parent.parent
    / "framework"
    / "src"
    / "calc_framework"
    / "configs"
    / "endfield_full.dag.json"
)

LAYOUT_PATH = ADAPTER_ROOT / "ui" / "layout.json"

ATTR_SCHEMA_PATH = ADAPTER_ROOT / "attr_schema.json"


def load_json(path: Path) -> dict:
    """加载 JSON 文件，文件不存在时直接退出。

    Args:
        path: JSON 文件路径

    Returns:
        解析后的字典

    Raises:
        SystemExit: 文件不存在
    """
    if not path.exists():
        print(f"[ERROR] 文件不存在: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate_layout(
    layout: dict[str, Any], dag: dict[str, Any], attr_schema: dict[str, Any] | None = None
) -> dict[str, Any]:
    """校验 layout.json 与 DAG JSON 的一致性。

    检查 sections 结构完整性、变量引用有效性、output 引用有效性。

    Args:
        layout: layout.json 内容字典
        dag: DAG JSON 内容字典
        attr_schema: 可选的 attr_schema.json 内容

    Returns:
        包含 valid 布尔值、issues 问题列表和 stats 统计信息的字典
    """
    issues: list[dict[str, Any]] = []

    sections = layout.get("sections", [])

    dag_variables = dag.get("variables", {})

    dag_outputs = dag.get("outputs", {})

    attr_names: set[str] = set()

    if attr_schema:
        for attr in attr_schema.get("attributes", []):
            if isinstance(attr, dict):
                attr_names.add(attr.get("name", ""))

    if not isinstance(sections, list):
        return {"valid": False, "issues": [{"severity": "error", "message": "sections 必须是数组"}], "stats": {}}

    section_types: dict[str, int] = {}

    seen_ids: set[str] = set()

    referenced_vars: set[str] = set()

    referenced_outputs: set[str] = set()

    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            issues.append({"severity": "error", "message": f"sections[{i}] 不是对象"})

            continue

        sid = section.get("id", f"<sections[{i}]>")

        stype = section.get("type", "")

        title = section.get("title", "")

        if not sid or not isinstance(sid, str):
            issues.append({"severity": "error", "section_id": sid, "message": f"sections[{i}] 缺少 id"})

        if sid in seen_ids:
            issues.append({"severity": "error", "section_id": sid, "message": f"重复的 section id: {sid}"})

        seen_ids.add(sid)

        if stype not in _VALID_SECTION_TYPES:
            issues.append(
                {"severity": "error", "section_id": sid, "field": "type", "message": f"无效 section type: {stype!r}"}
            )

        if not title:
            issues.append({"severity": "warning", "section_id": sid, "field": "title", "message": "缺少 title"})

        section_types[stype] = section_types.get(stype, 0) + 1

        if stype == "inputs":
            variables = section.get("variables", [])

            if not variables:
                issues.append(
                    {
                        "severity": "warning",
                        "section_id": sid,
                        "field": "variables",
                        "message": "input section 没有 variables",
                    }
                )

            for v in variables:
                referenced_vars.add(v)

                if v.startswith("user_input."):
                    continue

                if v in dag_variables:
                    var_def = dag_variables[v]

                    if not isinstance(var_def, dict) or "source" not in var_def:
                        issues.append(
                            {
                                "severity": "warning",
                                "section_id": sid,
                                "field": "variables",
                                "message": f"变量 {v!r} 定义不完整",
                            }
                        )

                else:
                    short_name = v.split(".", 1)[1] if "." in v else v

                    if short_name in attr_names:
                        continue

                    issues.append(
                        {
                            "severity": "error",
                            "section_id": sid,
                            "field": "variables",
                            "message": f"变量 {v!r} 既不在 DAG variables 中，也不在 attr_schema 或 user_input 中",
                        }
                    )

        if stype == "outputs":
            outputs = section.get("outputs", [])

            if not outputs:
                issues.append(
                    {
                        "severity": "warning",
                        "section_id": sid,
                        "field": "outputs",
                        "message": "output section 没有 outputs",
                    }
                )

            for o in outputs:
                referenced_outputs.add(o)

                if o not in dag_outputs:
                    issues.append(
                        {
                            "severity": "error",
                            "section_id": sid,
                            "field": "outputs",
                            "message": f"输出 {o!r} 不在 DAG outputs 中",
                        }
                    )

        if stype == "widget":
            widget_type = section.get("widget_type", "")

            if not widget_type:
                issues.append(
                    {
                        "severity": "warning",
                        "section_id": sid,
                        "field": "widget_type",
                        "message": "widget section 缺少 widget_type",
                    }
                )

    total_vars = len(dag_variables)

    total_outputs = len(dag_outputs)

    used_vars = len(referenced_vars)

    used_outputs = len(referenced_outputs)

    if used_vars < total_vars:
        uncovered = set(dag_variables.keys()) - referenced_vars

        issues.append(
            {
                "severity": "info",
                "message": f"layout 未覆盖 {len(uncovered)}/{total_vars} 个 DAG variables: {', '.join(sorted(uncovered)[:10])}",
            }
        )

    if used_outputs < total_outputs:
        uncovered = set(dag_outputs.keys()) - referenced_outputs

        issues.append(
            {
                "severity": "info",
                "message": f"layout 未覆盖 {len(uncovered)}/{total_outputs} 个 DAG outputs: {', '.join(sorted(uncovered)[:10])}",
            }
        )

    has_error = any(i["severity"] == "error" for i in issues)

    return {
        "valid": not has_error,
        "issues": issues,
        "stats": {
            "sections": len(sections),
            "inputs_sections": section_types.get("inputs", 0),
            "outputs_sections": section_types.get("outputs", 0),
            "widget_sections": section_types.get("widget", 0),
            "dag_variables": total_vars,
            "layout_variables": used_vars,
            "dag_outputs": total_outputs,
            "layout_outputs": used_outputs,
        },
    }


def main() -> None:
    """CLI 入口：加载配置文件并执行 layout 一致性验证。"""
    use_json = "--json" in sys.argv

    exit_zero = "--exit-zero" in sys.argv

    layout = load_json(LAYOUT_PATH)

    dag = load_json(DAG_PATH)

    attr_schema = load_json(ATTR_SCHEMA_PATH) if ATTR_SCHEMA_PATH.exists() else None

    result = validate_layout(layout, dag, attr_schema)

    if use_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        status = "✅ 验证通过" if result["valid"] else "❌ 验证失败"

        print(f"=== Layout 一致性验证: {status} ===")

        print(
            f"  Section 数: {result['stats']['sections']} (inputs={result['stats']['inputs_sections']}, outputs={result['stats']['outputs_sections']}, widget={result['stats']['widget_sections']})"
        )

        print(f"  DAG variables 覆盖: {result['stats']['layout_variables']}/{result['stats']['dag_variables']}")

        print(f"  DAG outputs 覆盖: {result['stats']['layout_outputs']}/{result['stats']['dag_outputs']}")

        print()

        if result["issues"]:
            for issue in result["issues"]:
                tag = issue["severity"].upper()

                sid = f"[{issue.get('section_id', '')}]" if issue.get("section_id") else ""

                print(f"  [{tag}] {sid} {issue['message']}")

        print()

        print(f"结果: {'✅ 通过' if result['valid'] else '❌ 失败'}")

    if not result["valid"] and not exit_zero:
        sys.exit(1)


if __name__ == "__main__":
    main()
