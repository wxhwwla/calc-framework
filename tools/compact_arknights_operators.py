#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""从 ``属性里程碑`` 批量反推干员 ``成长参数.segments[]`` 并写回 parsed JSON。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from calc_framework.inverse.curve import GROWTH_PARAM_SEGMENTS_KEY

from games.arknights.calc.inverse.materialize import materialize_operator_entity
from games.arknights.calc.inverse.milestones import GROWTH_PARAM_KEY, fit_operator_growth_params
from games.arknights.operator_catalog import DEFAULT_PARSED_DIR, SKIP_STEMS

DEFAULT_MAX_ERROR = 0.05


def _has_milestones(operator: dict[str, Any]) -> bool:
    ms = operator.get("属性里程碑") or (operator.get("基础属性") or {}).get("属性里程碑")
    return isinstance(ms, dict) and bool(ms)


def _growth_for_storage(raw: dict[str, Any]) -> dict[str, Any]:
    """去掉拟合过程字段，保留可持久化的 ``成长参数`` 内容。"""
    stored: dict[str, Any] = {}
    segments = raw.get(GROWTH_PARAM_SEGMENTS_KEY)
    if segments:
        stored[GROWTH_PARAM_SEGMENTS_KEY] = segments
    skill_sp = raw.get("技能SP")
    if skill_sp:
        stored["技能SP"] = skill_sp
    return stored


def compact_operator(
    operator: dict[str, Any],
    *,
    max_error: float = DEFAULT_MAX_ERROR,
) -> tuple[dict[str, Any], list[str]]:
    """对单个干员反推 ``成长参数``；无里程碑时原样返回。

    Returns:
        (更新后的干员 dict, 警告/错误消息列表)。
    """
    name = str(operator.get("名称", "?"))
    if not _has_milestones(operator):
        return operator, [f"{name}: 无属性里程碑，跳过"]

    fitted = fit_operator_growth_params(operator, max_error=max_error)
    fit_errors = list(fitted.pop("_errors", []) or [])
    warnings = [f"{name}: {msg}" for msg in fit_errors]
    stored = _growth_for_storage(fitted)
    if not stored:
        warnings.append(f"{name}: 未产生有效 segments/技能SP")
        return operator, warnings

    out = dict(operator)
    out[GROWTH_PARAM_KEY] = stored
    verify = materialize_operator_entity(out)
    if not verify.get("段曲线"):
        warnings.append(f"{name}: 物化校验未生成段曲线")
    return out, warnings


def compact_parsed_dir(
    parsed_dir: Path,
    *,
    max_error: float = DEFAULT_MAX_ERROR,
    apply: bool = False,
) -> dict[str, Any]:
    """遍历 parsed 目录，为含里程碑的干员写入 ``成长参数``。"""
    if not parsed_dir.is_dir():
        return {"success": False, "error": f"目录不存在: {parsed_dir}"}

    stats = {
        "total": 0,
        "compacted": 0,
        "skipped": 0,
        "warnings": 0,
    }
    all_warnings: list[str] = []
    operators: list[dict[str, Any]] = []

    for path in sorted(parsed_dir.glob("*.json")):
        if path.stem in SKIP_STEMS:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            all_warnings.append(f"{path.name}: 读取失败 {exc}")
            continue
        if not isinstance(raw, dict) or not raw.get("名称"):
            continue

        stats["total"] += 1
        compacted, warns = compact_operator(raw, max_error=max_error)
        all_warnings.extend(warns)
        if warns and any("跳过" in w for w in warns):
            stats["skipped"] += 1
        elif GROWTH_PARAM_KEY in compacted and compacted.get(GROWTH_PARAM_KEY) != raw.get(GROWTH_PARAM_KEY):
            stats["compacted"] += 1
        elif GROWTH_PARAM_KEY in compacted:
            stats["compacted"] += 1

        if apply:
            path.write_text(json.dumps(compacted, ensure_ascii=False, indent=2), encoding="utf-8")
        operators.append(compacted)

    aggregate_path = parsed_dir / "operators.json"
    if apply and operators:
        aggregate_path.write_text(
            json.dumps(operators, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    stats["warnings"] = len(all_warnings)
    stats["warning_samples"] = all_warnings[:50]
    stats["success"] = True
    stats["parsed_dir"] = str(parsed_dir)
    stats["apply"] = apply
    return stats


def _run(*, apply: bool, max_error: float, parsed_dir: Path, write_standard: bool) -> int:
    stats = compact_parsed_dir(parsed_dir, max_error=max_error, apply=apply)
    if not stats.get("success"):
        print(f"[错误] {stats.get('error')}")
        return 1

    mode = "已写入" if apply else "dry-run"
    print(
        f"[{mode}] parsed={stats['parsed_dir']} "
        f"总计={stats['total']} 压缩={stats['compacted']} 跳过={stats['skipped']} 警告={stats['warnings']}"
    )
    for w in stats.get("warning_samples", []):
        print(f"  [警告] {w}")
    extra = stats["warnings"] - len(stats.get("warning_samples", []))
    if extra > 0:
        print(f"  ... 另有 {extra} 条警告")

    if write_standard and apply:
        from tools.data_pipeline.transformers.from_arknights_scout import convert_all

        conv = convert_all(parsed_dir)
        if conv.get("success"):
            print(f"[完成] operators_standard.json: {conv['converted']} 干员 → {conv['output_file']}")
        else:
            print(f"[错误] 标准 JSON 转换失败: {conv.get('error')}")
            return 1
    elif write_standard and not apply:
        print("[提示] --write-standard 需配合 --apply")

    return 0


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="明日方舟干员成长参数批量反推")
    parser.add_argument(
        "--parsed-dir",
        type=Path,
        default=DEFAULT_PARSED_DIR,
        help="arknights_scout parsed 目录",
    )
    parser.add_argument("--apply", action="store_true", help="写回 parsed/*.json（默认 dry-run）")
    parser.add_argument("--max-error", type=float, default=DEFAULT_MAX_ERROR, help="段内拟合允许最大误差")
    parser.add_argument(
        "--write-standard",
        action="store_true",
        help="--apply 后额外生成 games/arknights/data/operators_standard.json",
    )
    args = parser.parse_args()
    raise SystemExit(
        _run(
            apply=args.apply,
            max_error=args.max_error,
            parsed_dir=args.parsed_dir,
            write_standard=args.write_standard,
        )
    )


if __name__ == "__main__":
    main()
