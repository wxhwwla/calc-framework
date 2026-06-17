#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 arknights_scout 输出 → 标准 EntitySchema 迁移器。

将 ``tools/arknights_scout/output/parsed/`` 下的单个干员 JSON
合并转换为标准 EntitySchema 格式，输出到 ``framework/adapters/arknights/data/``。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# 确保项目根在 sys.path 中
_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from utils.game_data_paths import (
    ARKNIGHTS_OPERATORS_STANDARD,
    ARKNIGHTS_PARSED_DIR,
)

PARSED_DIR = ARKNIGHTS_PARSED_DIR
OUTPUT_DIR = ARKNIGHTS_OPERATORS_STANDARD.parent
OUTPUT_FILE = ARKNIGHTS_OPERATORS_STANDARD


def _build_skills(raw_operator: dict[str, Any]) -> list[dict[str, Any]]:
    """将原始干员 JSON 中的技能列表转换为 EntitySchema 技能格式。

    明日方舟技能多为被动加成（攻击速度+、攻击力+ 等），
    描述文本中不含数值倍率数组，因此段列表为空。

    Args:
        raw_operator: 原始干员数据 dict。

    Returns:
        含游戏特有字段的技能 dict 列表。
    """
    skills: list[dict[str, Any]] = []
    raw_skills = raw_operator.get("技能", [])
    for s in raw_skills:
        skill: dict[str, Any] = {
            "名称": s.get("name", ""),
            "标签": "主动",
            "百分比": False,
            "段": [],
        }
        sp_type = s.get("sp_type", "")
        trigger = s.get("trigger", "")
        levels = s.get("levels", [])
        if sp_type:
            skill["技能类型"] = sp_type
        if trigger:
            skill["备注"] = trigger
        if levels:
            # 提取各等级 SP 消耗作为数值参考
            sp_values = []
            for lv in levels:
                sp_cost = lv.get("sp_cost", 0)
                if isinstance(sp_cost, (int, float)) and sp_cost > 0:
                    sp_values.append(sp_cost)
            if sp_values:
                skill["SP消耗"] = sp_values
        skills.append(skill)
    return skills


def _convert_operator(raw: dict[str, Any]) -> dict[str, Any]:
    """将单个原始干员 JSON 转换为 EntitySchema 兼容格式。

    Args:
        raw: 原始干员 dict（来自 arknights_scout 解析）。

    Returns:
        含 EntitySchema 标准字段 + 游戏特有字段的 dict。
    """
    entity: dict[str, Any] = {
        "名称": str(raw.get("名称", "")),
        "技能": _build_skills(raw),
        "_entity_type": "operator",
    }

    # 透传顶层字段
    for key in ("星级", "职业", "分支", "标签", "特性", "天赋", "潜能", "模组"):
        if key in raw:
            entity[key] = raw[key]

    # 基础属性平铺为顶层字段
    base_stats = raw.get("基础属性", {})
    if base_stats:
        entity["基础属性"] = base_stats
        if "hp" in base_stats:
            entity["生命上限"] = base_stats["hp"]
        if "atk" in base_stats:
            entity["攻击力"] = base_stats["atk"]
        if "def" in base_stats:
            entity["防御力"] = base_stats["def"]
        if "res" in base_stats:
            entity["法术抗性"] = base_stats["res"]

    ms = raw.get("属性里程碑") or base_stats.get("属性里程碑")
    if ms:
        entity["属性里程碑"] = ms

    growth = raw.get("成长参数")
    if growth:
        entity["成长参数"] = growth

    # 信赖加成
    trust = raw.get("信赖加成", {})
    if trust:
        entity["信赖加成"] = trust

    # 来源标记
    entity["_source"] = raw.get("_source", "arknights_bwiki")
    entity["_updated_at"] = raw.get("_updated_at", "")

    return entity


def convert_all(
    parsed_dir: Path = PARSED_DIR,
    output_file: Path = OUTPUT_FILE,
) -> dict[str, Any]:
    """将所有干员 JSON 转换为标准 EntitySchema 格式并写入文件。

    Args:
        parsed_dir: arknights_scout parsed/ 目录路径。
        output_file: 输出文件路径。

    Returns:
        包含统计信息的 dict。
    """
    if not parsed_dir.is_dir():
        return {"success": False, "error": f"目录不存在: {parsed_dir}"}

    output_file.parent.mkdir(parents=True, exist_ok=True)

    operators: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for f in sorted(parsed_dir.iterdir()):
        if f.suffix != ".json":
            continue
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(raw, dict) or not raw.get("名称"):
                continue
            converted = _convert_operator(raw)
            operators.append(converted)
        except Exception as exc:
            errors.append({"file": f.name, "error": str(exc)})

    output_file.write_text(
        json.dumps(operators, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stats = {
        "success": True,
        "total_files": len(list(parsed_dir.glob("*.json"))),
        "converted": len(operators),
        "errors": len(errors),
        "output_file": str(output_file),
    }
    if errors:
        stats["error_details"] = errors

    return stats


def main() -> int:
    """CLI 入口。"""
    stats = convert_all()
    if stats["success"]:
        print(f"转换完成: {stats['converted']}/{stats['total_files']} 个干员")
        print(f"输出: {stats['output_file']}")
        if stats.get("errors"):
            print(f"失败: {stats['errors']} 个")
            for e in stats.get("error_details", []):
                print(f"  {e['file']}: {e['error']}")
        return 0
    else:
        print(f"错误: {stats.get('error')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
