#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据生成器

此模块提供角色和武器属性的统一生成接口，通过模式参数区分不同类型的数据生成逻辑。
"""
from typing import Dict, List, Any, Union
from calculation.damage.formula import calculate_growth_curve, calculate_skill_curve, calculate_bonus_attribute

# 角色普通属性列表
CHARACTER_NORMAL_ATTRS = ["力量", "敏捷", "智识", "意志", "基础攻击力"]

# 角色技能属性列表
CHARACTER_SKILL_ATTRS = ["战技倍率", "连携技倍率", "终结技倍率"]


def generate_attributes(
    growth_params: Dict[str, Any],
    mode: str = "character"
) -> Dict[str, Union[List[float], List[List[float]]]]:
    """
    根据成长参数配置生成属性（统一接口）

    参数：
        growth_params: 成长参数配置字典
        mode: 生成模式，可选值: "character" | "weapon"

    返回：
        包含所有属性成长曲线的字典
    """
    if mode == "character":
        return generate_character_attributes(growth_params)
    elif mode == "weapon":
        return generate_weapon_attributes(growth_params)
    else:
        raise ValueError(f"不支持的生成模式: {mode}")


def generate_character_attributes(
    growth_params: Dict[str, Any]
) -> Dict[str, Union[List[float], List[List[float]]]]:
    """
    根据成长参数配置生成角色所有属性

    参数：
        growth_params: 成长参数配置字典，格式如下：
        {
            "力量": {"base": int, "growth": int, "divisor": int, "offset": int},
            "敏捷": {"base": int, "growth": int, "divisor": int, "offset": int},
            "智识": {"base": int, "growth": int, "divisor": int, "offset": int},
            "意志": {"base": int, "growth": int, "divisor": int, "offset": int},
            "基础攻击力": {"base": int, "growth": int, "divisor": int, "offset": int},
            "战技倍率": [
                {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]}
            ],
            "连携技倍率": [
                {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]},
                {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]}
            ],
            "终结技倍率": [
                {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]},
                {"base": int, "growth": int, "divisor": int, "offset": int, "special": [int, int, int]}
            ]
        }

    返回：
        包含所有属性成长曲线的字典
        - 普通属性返回 List[float]（90个值）
        - 技能倍率返回 List[List[float]]（每段12个值）
    """
    attributes: Dict[str, Union[List[float], List[List[float]]]] = {}

    for attr_name in CHARACTER_NORMAL_ATTRS:
        if attr_name in growth_params:
            params = growth_params[attr_name]
            attributes[attr_name] = calculate_growth_curve(
                base=params.get("base", 0),
                growth=params.get("growth", 0),
                divisor=params.get("divisor", 1),
                offset=params.get("offset", 0)
            )

    for attr_name in CHARACTER_SKILL_ATTRS:
        if attr_name in growth_params:
            segments = growth_params[attr_name]
            if isinstance(segments, list):
                curves: List[List[float]] = []
                for seg_params in segments:
                    special: List[float] | None = seg_params.get("special")
                    curves.append(calculate_skill_curve(
                        base=seg_params.get("base", 0),
                        growth=seg_params.get("growth", 0),
                        divisor=seg_params.get("divisor", 1),
                        offset=seg_params.get("offset", 0),
                        special_values=special
                    ))
                attributes[attr_name] = curves
            elif isinstance(segments, dict):
                special: List[float] | None = segments.get("special")
                attributes[attr_name] = [calculate_skill_curve(
                    base=segments.get("base", 0),
                    growth=segments.get("growth", 0),
                    divisor=segments.get("divisor", 1),
                    offset=segments.get("offset", 0),
                    special_values=special
                )]

    return attributes


def generate_weapon_attributes(
    growth_params: Dict[str, Any]
) -> Dict[str, Union[List[float], List[List[float]]]]:
    """
    根据成长参数配置生成武器所有属性

    参数：
        growth_params: 成长参数配置字典，格式如下：
        {
            "基础攻击力": {"base": float | int, "growth": float | int, "divisor": float | int, "offset": float | int},
            "敏捷+": {"base": float | int, "growth": float | int, "divisor": float | int, "offset": float | int, "special": list},
            "攻击力+": {"base": float | int, "growth": float | int, "divisor": float | int, "offset": float | int, "special": list},
            ...
        }

    返回：
        包含所有属性成长曲线的字典
    """
    attributes: Dict[str, Union[List[float], List[List[float]]]] = {}

    for attr_name, params in growth_params.items():
        if attr_name == "基础攻击力":
            attributes[attr_name] = calculate_growth_curve(
                base=params.get("base", 0),
                growth=params.get("growth", 0),
                divisor=params.get("divisor", 1),
                offset=params.get("offset", 0)
            )
        elif attr_name.endswith('+'):
            if isinstance(params.get("curve"), list):
                attributes[attr_name] = [float(v) for v in params["curve"]]
            else:
                special: List[float | int] | None = params.get("special")
                attributes[attr_name] = calculate_bonus_attribute(
                    base=params.get("base", 0),
                    growth=params.get("growth", 0),
                    divisor=params.get("divisor", 1),
                    offset=params.get("offset", 0),
                    special=special,
                )

    return attributes