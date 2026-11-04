# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""计算器生成引擎 — 基于模板 + 用户声明的变量/公式步骤/输出 → 生成完整适配器包文件。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.generator.data_files import (
    DATA_FILE_BY_SOURCE,
    bound_entity_sources,
    normalize_data_files,
    serialize_data_file,
)
from tools.generator.layout_sections import build_attr_schema, build_layout
from tools.generator.selectors import normalize_entity_selectors

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ADAPTERS_DIR = _REPO_ROOT / "framework" / "adapters"


# ── 模板信息 ──────────────────────────────────────────


def list_templates() -> dict[str, dict[str, str]]:
    """扫描 framework/adapters/ 下所有有效适配器作为生成模板。"""
    templates: dict[str, dict[str, str]] = {}
    if not _ADAPTERS_DIR.is_dir():
        return templates
    for d in sorted(_ADAPTERS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        meta_fp = d / "meta.json"
        if not meta_fp.exists():
            continue
        try:
            meta = json.loads(meta_fp.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        templates[d.name] = {
            "name": meta.get("name", d.name),
            "description": meta.get("description", ""),
        }
    return templates


# ── 生成请求/响应结构 ─────────────────────────────────


@dataclass
class VarDef:
    name: str
    type: str = "float"
    source: str = "user_input"
    default: float | bool | int | str = 0
    description: str = ""
    min: float | int | None = None
    max: float | int | None = None
    ui_control: dict[str, Any] = field(default_factory=dict)


@dataclass
class StepDef:
    id: str
    op: str = "+"  # + - * / condition expr
    lhs: str = ""
    rhs: str = ""
    cond: str = ""
    true_val: str = ""
    false_val: str = ""
    expr: str = ""
    input_map: dict[str, str] = field(default_factory=dict)
    label: str = ""


@dataclass
class OutputDef:
    name: str
    node: str = ""
    label: str = ""
    format: str = ""
    is_primary: bool = True


# ── 生成引擎 ──────────────────────────────────────────


class GeneratorEngine:
    """将用户声明的变量/公式/输出转换为完整的适配器包文件。

    用法::

        engine = GeneratorEngine()
        files = engine.generate(
            template_id="card_rpg",
            game_name="我的游戏",
            variables=[...],
            formula_steps=[...],
            outputs=[...],
        )
        # files = {"meta.json": ..., "dag/<name>.dag.json": ..., ...}
    """

    def __init__(self, adapters_dir: str | Path | None = None) -> None:
        """初始化生成引擎。

        Args:
            adapters_dir: 模板根目录；默认使用仓库的 ``framework/adapters/``。
        """
        self._adapters_dir = Path(adapters_dir) if adapters_dir else _ADAPTERS_DIR

    def generate(
        self,
        template_id: str | None = None,
        game_name: str = "",
        *,
        variables: list[dict] | None = None,
        formula_steps: list[dict] | None = None,
        outputs: list[dict] | None = None,
        data_files: dict[str, list[dict]] | None = None,
        entity_selectors: list[dict] | None = None,
        entity_detail: dict | None = None,
        entity_input_rules: list[dict] | None = None,
        output_dir: str | None = None,
    ) -> dict[str, str]:
        """生成适配器包的所有文件，返回 {相对路径: 文件内容}。

        Args:
            template_id: 模板目录名；为 None 时使用通用默认值，不复制模板函数。
            game_name: 游戏/计算器名称。
            variables: 变量声明列表；可含 ``min``/``max``/``ui_control``。
            formula_steps: 公式步骤列表。
            outputs: 输出声明列表。
            data_files: 实体数据文件声明，键仅允许 character/weapon/equipment/enemy；
                仅非空记录列表视为绑定，绑定来源的变量保留原命名空间、其值由实体选择提供；
                空列表按未绑定处理，对应变量改写为 user_input。
            entity_selectors: 级联选择器声明，写入 ``meta.entity_selectors``；
                依赖非空 data_files，末级 field 必须为 ``名称``。
            entity_detail: 实体详情面板声明，写入 ``meta.entity_detail``。
            entity_input_rules: 条件禁用输入规则，写入 ``meta.entity_input_rules``。
            output_dir: 保留参数（当前不写盘，由调用方负责）。

        Returns:
            相对路径到文件内容的映射；没有公式步骤时返回空字典。
        """
        vars_ = [VarDef(**v) if isinstance(v, dict) else v for v in (variables or [])]
        steps = [StepDef(**s) if isinstance(s, dict) else s for s in (formula_steps or [])]
        outs = [OutputDef(**o) if isinstance(o, dict) else o for o in (outputs or [])]

        if not steps:
            return {}

        template = self._load_template(template_id) if template_id else {}

        normalized_data_files, _data_warnings = normalize_data_files(data_files)
        normalized_selectors = normalize_entity_selectors(entity_selectors, normalized_data_files)
        effective_sources = self._effective_sources(vars_, bound_entity_sources(normalized_data_files))
        dag_json = self._build_dag(game_name, vars_, steps, outs, effective_sources)
        layout_json = build_layout(game_name, vars_, effective_sources, outs)
        attr_schema = build_attr_schema(vars_, effective_sources)

        safe_name = game_name.replace(" ", "_").lower()
        dag_filename = f"{safe_name}.dag.json"

        meta = {
            "name": game_name,
            "game": game_name,
            "description": f"自动生成的计算器: {game_name}",
            "version": "0.1.0",
            "schema_version": template.get("schema_version", "dag-v1"),
            "entry_dag": "dag/" + dag_filename,
            "ui_layout": "ui/layout.json",
            "attr_schema": "attr_schema.json",
            "functions": template.get("functions", {}),
        }

        entry_data = [
            DATA_FILE_BY_SOURCE[source] for source in DATA_FILE_BY_SOURCE if normalized_data_files.get(source)
        ]
        if entry_data:
            meta["entry_data"] = entry_data
        if normalized_selectors:
            meta["entity_selectors"] = normalized_selectors
        if entity_detail:
            meta["entity_detail"] = entity_detail
        if entity_input_rules:
            meta["entity_input_rules"] = entity_input_rules

        files: dict[str, str] = {
            "meta.json": json.dumps(meta, ensure_ascii=False, indent=2),
            "dag/" + dag_filename: json.dumps(dag_json, ensure_ascii=False, indent=2),
            "ui/layout.json": json.dumps(layout_json, ensure_ascii=False, indent=2),
            "attr_schema.json": json.dumps(attr_schema, ensure_ascii=False, indent=2),
        }
        for source in DATA_FILE_BY_SOURCE:
            if source in normalized_data_files:
                files[DATA_FILE_BY_SOURCE[source]] = serialize_data_file(normalized_data_files[source])

        func_src = template.get("_template_dir")
        if func_src:
            func_path = Path(func_src) / "functions.py"
            if func_path.exists():
                files["functions.py"] = func_path.read_text(encoding="utf-8")

        return files

    # ── 内部实现 ────────────────────────────────────

    def _load_template(self, template_id: str) -> dict[str, Any]:
        d = self._adapters_dir / template_id
        if not d.is_dir():
            raise ValueError(f"模板不存在: {template_id}")
        meta_fp = d / "meta.json"
        if not meta_fp.exists():
            raise ValueError(f"模板缺少 meta.json: {template_id}")
        meta = json.loads(meta_fp.read_text(encoding="utf-8"))
        meta["_template_dir"] = str(d)
        return meta

    def _build_dag(
        self,
        game_name: str,
        variables: list[VarDef],
        steps: list[StepDef],
        outputs: list[OutputDef],
        effective_sources: dict[str, str],
    ) -> dict:
        dag_vars: dict[str, dict] = {}
        dag_nodes: dict[str, dict] = {}
        dag_outputs: dict[str, dict] = {}

        for v in variables:
            source = effective_sources[v.name]
            var_path = f"{source}.{v.name}"
            var_entry: dict[str, Any] = {
                "type": v.type,
                "source": source,
                "default": v.default,
                "description": v.description,
            }
            if v.min is not None:
                var_entry["min"] = v.min
            if v.max is not None:
                var_entry["max"] = v.max
            if v.ui_control:
                var_entry["ui_control"] = dict(v.ui_control)
            dag_vars[var_path] = var_entry
            node_id = self._safe_id(v.name)
            dag_nodes[node_id] = {
                "type": "var",
                "path": var_path,
                "label": v.description or v.name,
            }

        for s in steps:
            nid = self._safe_id(s.id) if s.id else f"step_{len(dag_nodes)}"
            step_label = s.label or s.id or nid

            if s.op in ("+", "-", "*", "/"):
                dag_nodes[nid] = {
                    "type": "binary",
                    "op": s.op,
                    "lhs": self._resolve_ref(s.lhs, dag_nodes),
                    "rhs": self._resolve_ref(s.rhs, dag_nodes),
                    "label": step_label,
                }
            elif s.op == "condition":
                dag_nodes[nid] = {
                    "type": "condition",
                    "cond": self._resolve_ref(s.cond, dag_nodes),
                    "true_val": self._resolve_ref(s.true_val, dag_nodes),
                    "false_val": self._resolve_ref(s.false_val, dag_nodes),
                    "label": step_label,
                }
            elif s.op == "expr":
                input_map = {}
                if s.input_map:
                    input_map = {k: self._resolve_ref(v, dag_nodes) for k, v in s.input_map.items()}
                dag_nodes[nid] = {
                    "type": "expr",
                    "expr": s.expr,
                    "inputs": input_map,
                    "label": step_label,
                }

        self._inject_const_nodes(dag_nodes, steps)

        for o in outputs:
            ref = self._resolve_ref(o.node, dag_nodes) if o.node else ""
            dag_outputs[o.name] = {
                "node": ref,
                "label": o.label or o.name,
                "format": o.format or "",
                "is_primary": o.is_primary,
            }

        if not dag_outputs and steps:
            last_step = self._safe_id(steps[-1].id) if steps[-1].id else f"step_{len(dag_nodes) - 1}"
            dag_outputs["最终结果"] = {
                "node": last_step,
                "label": "最终结果",
                "format": "",
                "is_primary": True,
            }

        return {
            "schema_version": "dag-v1",
            "name": game_name,
            "description": f"自动生成的 {game_name} 伤害公式",
            "variables": dag_vars,
            "subgraphs": {},
            "nodes": dag_nodes,
            "outputs": dag_outputs,
        }

    @staticmethod
    def _effective_sources(variables: list[VarDef], bound_sources: frozenset[str]) -> dict[str, str]:
        """计算每个变量的生成后来源。

        规则：

        - ``input`` 别名归一为 ``user_input``；
        - ``user_input`` / ``computed`` 保持不变；
        - 其他来源（角色/武器/装备/敌人等）若数据文件提供非空记录则保留，
          否则（未提供或空列表）改写为 ``user_input``，使其在 UI 中成为可编辑输入。
        """
        effective: dict[str, str] = {}
        for v in variables:
            normalized = "user_input" if v.source == "input" else v.source
            if normalized in ("user_input", "computed") or normalized in bound_sources:
                effective[v.name] = normalized
            else:
                effective[v.name] = "user_input"
        return effective

    # ── 工具方法 ────────────────────────────────────

    @staticmethod
    def _safe_id(name: str) -> str:
        return name.strip().replace(" ", "_").replace(".", "_").lower() or "unnamed"

    def _resolve_ref(self, ref: str, existing_nodes: dict[str, dict]) -> str:
        if not ref:
            return ""
        if ref in existing_nodes:
            return ref
        safe = self._safe_id(ref)
        if safe in existing_nodes:
            return safe
        try:
            float(ref)
            return f"const_{safe}"
        except ValueError:
            pass
        return safe

    def _inject_const_nodes(self, nodes: dict[str, dict], steps: list[StepDef]) -> None:
        seen_consts: set[str] = set()
        for _nid, node in list(nodes.items()):
            for key in ("lhs", "rhs", "cond", "true_val", "false_val"):
                val = node.get(key, "")
                if not isinstance(val, str) or not val:
                    continue
                try:
                    num = float(val)
                    const_id = f"const_{self._safe_id(val)}"
                    if const_id not in nodes and const_id not in seen_consts:
                        nodes[const_id] = {"type": "const", "value": num, "label": val}
                        seen_consts.add(const_id)
                    node[key] = const_id
                except ValueError:
                    pass

        for s in steps:
            for attr in ("lhs", "rhs"):
                raw = getattr(s, attr, "")
                if not raw:
                    continue
                try:
                    float(raw)
                    const_id = f"const_{self._safe_id(raw)}"
                    if const_id not in nodes:
                        nodes[const_id] = {"type": "const", "value": float(raw), "label": raw}
                except ValueError:
                    pass
