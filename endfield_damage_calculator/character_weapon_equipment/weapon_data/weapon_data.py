#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武器数据模块

此模块负责加载和管理游戏中的武器数据。

设计理念：
    通过配置驱动的方式，武器数据（包括成长参数）存储在 JSON 文件中，
    添加新武器时只需修改 JSON 配置文件，无需修改代码。

武器数据结构（JSON格式）：
{
    "名称": str,           # 武器名称
    "类型": str,           # 武器类型（如单手剑、双手剑等）
    "星级": int,           # 武器稀有度（3-6星）
    "等级": List[int],     # 可升级等级列表（1-90）
    "潜能": List[int],     # 精炼等级列表（0-5）
    "基础攻击力": List[int], # 各等级基础攻击力
    "属性+": List[float],   # 武器附加属性（如敏捷+、攻击力+等）
    "特殊能力": List        # 特殊能力配置（[是否启用, 能力名称, 等级列表]）
}

特殊能力格式说明：
- 未启用: [False]
- 已启用: [True, "属性名称+", [等级1值, 等级2值, ...]]
"""
import sys
import json
from pathlib import Path

# 添加路径以便导入公式模块
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from calculation.formula import (
    levels, talent
)


def load_weapons_from_json(file_path: str) -> list:
    """
    从 JSON 文件加载武器数据

    参数：
        file_path: JSON 文件路径

    返回：
        武器数据列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def process_weapon_data(raw_data: dict) -> dict:
    """
    处理单个武器数据，确保数据结构一致

    参数：
        raw_data: 原始武器数据（来自JSON）

    返回：
        完整的武器数据（包含所有必要字段）
    """
    # 基础信息
    processed = {
        "名称": raw_data.get("名称", ""),
        "类型": raw_data.get("类型", ""),
        "星级": raw_data.get("星级", 0),
        "等级": levels,
        "潜能": talent,
    }

    # 基础攻击力（等级相关属性）
    if "基础攻击力" in raw_data:
        processed["基础攻击力"] = raw_data["基础攻击力"]
    else:
        processed["基础攻击力"] = []

    # 附加属性（以+结尾的属性）
    bonus_attrs = [key for key in raw_data.keys() if key.endswith('+')]
    for attr_name in bonus_attrs:
        processed[attr_name] = raw_data[attr_name]

    # 特殊能力
    if "特殊能力" in raw_data:
        processed["特殊能力"] = raw_data["特殊能力"]
    else:
        processed["特殊能力"] = [False]

    return processed


def load_and_process_weapons(json_path: str | None = None) -> list:
    """
    加载并处理所有武器数据

    参数：
        json_path: JSON 文件路径，默认为同目录下的 weapons.json

    返回：
        处理后的武器数据列表
    """
    if json_path is None:
        json_path = str(Path(__file__).parent / "weapons.json")
    
    raw_weapons = load_weapons_from_json(json_path)
    return [process_weapon_data(weapon) for weapon in raw_weapons]

