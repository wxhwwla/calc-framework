#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
角色数据模块

此模块负责加载和管理游戏中的角色数据。

设计理念：
    通过配置驱动的方式，角色数据（包括成长参数）存储在 JSON 文件中，
    添加新角色时只需修改 JSON 配置文件，无需修改代码。

运行时数据入口：
    GUI / 计算 / 测试应使用 ``data.loader.get_characters()``。
    本模块的 ``process_character_data`` / ``load_and_process_characters`` 仅供
    ``add_character`` 等录入脚本在写入 JSON 前补全缺省字段，不是运行时加载路径。

角色数据结构（JSON格式）：
{
    "名称": str,           # 角色名称
    "类型": str,           # 角色类型（如近卫、狙击等）
    "星级": int,           # 角色稀有度（3-6星）
    "主能力": str,          # 主能力属性名称（力量/敏捷/智识/意志）
    "副能力": str,          # 副能力属性名称（力量/敏捷/智识/意志）
    "成长参数": {           # 属性成长参数配置（可选，若不提供则使用默认值）
        "力量": {"base": int, "growth": int, "divisor": int, "offset": int},
        "敏捷": {"base": int, "growth": int, "divisor": int, "offset": int},
        "智识": {"base": int, "growth": int, "divisor": int, "offset": int},
        "意志": {"base": int, "growth": int, "divisor": int, "offset": int},
        "基础攻击力": {"base": int, "growth": int, "divisor": int, "offset": int},
        "战技倍率": [{"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]}],
        "连携技倍率": [
            {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]},
            {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]}
        ],
        "终结技倍率": [
            {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]},
            {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]}
        ]
    },
    "属性": {              # 预计算的属性值（可选，优先级高于成长参数）
        "力量": List[int],
        "敏捷": List[int],
        ...
    }
}
"""
import json
from pathlib import Path

from calculation.formula import levels, talent, trust, trust_add
from .formula import generate_character_attributes, DEFAULT_GROWTH_PARAMS


def load_characters_from_json(file_path: str) -> list:
    """
    从 JSON 文件加载角色数据

    参数：
        file_path: JSON 文件路径

    返回：
        角色数据列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def process_character_data(raw_data: dict) -> dict:
    """
    处理单个角色数据，自动计算属性成长曲线

    参数：
        raw_data: 原始角色数据（来自JSON）

    返回：
        完整的角色数据（包含计算后的属性曲线）
    """
    # 基础信息
    processed = {
        "名称": raw_data.get("名称", ""),
        "类型": raw_data.get("类型", ""),
        "星级": raw_data.get("星级", 0),
        "武器": raw_data.get("武器", ""),
        "等级": levels,
        "潜能": talent,
        "信赖": trust,
        "信赖加成": trust_add,
        "主能力": raw_data.get("主能力", ""),
        "副能力": raw_data.get("副能力", ""),
    }

    # 如果有预计算的属性值（无论是"属性"字段还是顶层键），直接使用
    if "属性" in raw_data:
        for attr_name, values in raw_data["属性"].items():
            processed[attr_name] = values
    else:
        # 检查是否有顶层属性键
        attr_keys = ["力量", "敏捷", "智识", "意志", "基础攻击力", "战技倍率", "连携技倍率", "终结技倍率"]
        has_top_level_attrs = any(key in raw_data for key in attr_keys)
        if has_top_level_attrs:
            # 直接使用顶层属性值
            for key in attr_keys:
                if key in raw_data:
                    processed[key] = raw_data[key]
        else:
            # 使用成长参数生成属性曲线
            growth_params = raw_data.get("成长参数", DEFAULT_GROWTH_PARAMS)
            attributes = generate_character_attributes(growth_params)
            processed.update(attributes)

    # 保持向后兼容性：添加旧版字段名
    if "战技倍率" in processed and isinstance(processed["战技倍率"], list):
        processed["战技倍率1"] = processed["战技倍率"][0] if len(processed["战技倍率"]) > 0 else None
    if "连携技倍率" in processed and isinstance(processed["连携技倍率"], list):
        processed["连携技倍率1"] = processed["连携技倍率"][0] if len(processed["连携技倍率"]) > 0 else None
        processed["连携技倍率2"] = processed["连携技倍率"][1] if len(processed["连携技倍率"]) > 1 else None
    if "终结技倍率" in processed and isinstance(processed["终结技倍率"], list):
        processed["终结技倍率1"] = processed["终结技倍率"][0] if len(processed["终结技倍率"]) > 0 else None
        processed["终结技倍率2"] = processed["终结技倍率"][1] if len(processed["终结技倍率"]) > 1 else None

    return processed


def load_and_process_characters(json_path: str | None = None) -> list:
    """
    加载并处理所有角色数据

    参数：
        json_path: JSON 文件路径，默认为同目录下的 characters.json

    返回：
        处理后的角色数据列表
    """
    if json_path is None:
        json_path = str(Path(__file__).parent / "characters.json")
    
    raw_characters = load_characters_from_json(json_path)
    return [process_character_data(char) for char in raw_characters]
