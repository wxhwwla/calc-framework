#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一数据加载层

此模块提供角色和武器数据的统一加载接口，支持数据缓存机制，
避免重复读取文件。同时支持数据类型元数据管理，确保数据的双向一致性。

主要功能：
1. 加载 JSON 数据文件
2. 提供角色和武器数据的获取接口（带缓存）
3. 支持检查并保存数据到 JSON 文件
4. 数据类型元数据管理（整数/小数/百分比）
5. 数据双向转换（存储/还原）

数据处理规则：
- 整数数据：直接按公式计算
- 小数数据：乘10→整数计算→除10→存储
- 百分比数据：移除%符号→按小数/整数处理→存储

数据文件路径：
- 角色数据：character_weapon_equipment/character_data/characters.json
- 武器数据：character_weapon_equipment/weapon_data/weapons.json
"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from utils.path_utils import get_resource_path

# 数据类型标识
DATA_TYPE_INTEGER = 'integer'
DATA_TYPE_DECIMAL = 'decimal'
DATA_TYPE_PERCENTAGE = 'percentage'

# 元数据字段名
METADATA_KEY = '_metadata'
DATA_TYPE_KEY = 'data_type'

# 缓存数据
_characters: Optional[List[Dict[str, Any]]] = None
_weapons: Optional[List[Dict[str, Any]]] = None

# 数据文件路径配置
CHARACTERS_JSON_PATH: str = "character_weapon_equipment/character_data/characters.json"
WEAPONS_JSON_PATH: str = "character_weapon_equipment/weapon_data/weapons.json"


def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    """加载 JSON 文件并返回数据列表

    Args:
        filepath: 相对于项目根目录的路径

    Returns:
        JSON 数据列表，如果文件不存在或解析失败返回空列表
    """
    try:
        full_path = get_resource_path(filepath)
        if not full_path.exists():
            return []

        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
    except Exception:
        return []


def get_characters() -> List[Dict[str, Any]]:
    """获取所有角色数据（带缓存）

    Returns:
        角色数据列表
    """
    global _characters
    if _characters is None:
        _characters = load_json_file(CHARACTERS_JSON_PATH)
    return _characters


def get_weapons() -> List[Dict[str, Any]]:
    """获取所有武器数据（带缓存）

    Returns:
        武器数据列表
    """
    global _weapons
    if _weapons is None:
        _weapons = load_json_file(WEAPONS_JSON_PATH)
    return _weapons


def reload_characters() -> None:
    """重新加载角色数据（清除缓存）"""
    global _characters
    _characters = None


def reload_weapons() -> None:
    """重新加载武器数据（清除缓存）"""
    global _weapons
    _weapons = None


def save_characters(data: List[Dict[str, Any]]) -> bool:
    """保存角色数据到 JSON 文件

    Args:
        data: 要保存的角色数据列表

    Returns:
        是否保存成功
    """
    try:
        full_path = get_resource_path(CHARACTERS_JSON_PATH)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_characters()
        return True
    except Exception:
        return False


def save_weapons(data: List[Dict[str, Any]]) -> bool:
    """保存武器数据到 JSON 文件

    Args:
        data: 要保存的武器数据列表

    Returns:
        是否保存成功
    """
    try:
        full_path = get_resource_path(WEAPONS_JSON_PATH)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        reload_weapons()
        return True
    except Exception:
        return False


def check_and_save_characters(characters: List[Dict[str, Any]]) -> None:
    """检查并保存角色数据（仅在数据有变化时保存）"""
    if not characters:
        return

    current_data = get_characters()
    if not current_data:
        save_characters(characters)
        return

    if characters != current_data:
        save_characters(characters)


def check_and_save_weapons(weapons: List[Dict[str, Any]]) -> None:
    """检查并保存武器数据（仅在数据有变化时保存）"""
    if not weapons:
        return

    current_data = get_weapons()
    if not current_data:
        save_weapons(weapons)
        return

    if weapons != current_data:
        save_weapons(weapons)


# ==================== 数据类型处理函数 ====================

def detect_data_type(value: Union[int, float, str]) -> str:
    """
    检测单个数据的值类型

    Args:
        value: 待检测的值，可以是整数、小数或带%符号的字符串

    Returns:
        数据类型标识: 'integer', 'decimal', 或 'percentage'
    """
    if isinstance(value, str):
        # 检查是否为百分比字符串
        if value.strip().endswith('%'):
            return DATA_TYPE_PERCENTAGE
        # 尝试解析为数字
        try:
            float_val = float(value)
            if float_val == int(float_val):
                return DATA_TYPE_INTEGER
            else:
                return DATA_TYPE_DECIMAL
        except ValueError:
            return DATA_TYPE_INTEGER  # 默认视为整数类型
    
    elif isinstance(value, float):
        if value == int(value):
            return DATA_TYPE_INTEGER
        return DATA_TYPE_DECIMAL
    
    elif isinstance(value, int):
        return DATA_TYPE_INTEGER
    
    return DATA_TYPE_INTEGER


def parse_percentage(value: str) -> Tuple[Union[int, float], str]:
    """
    解析百分比字符串，提取数值并确定数据类型

    Args:
        value: 百分比字符串，如 "156%" 或 "3.3%"

    Returns:
        (数值, 数据类型标识)
    """
    match = re.match(r'^\s*([\d.]+)\s*%', value)
    if match:
        num_str = match.group(1)
        if '.' in num_str:
            return (float(num_str), DATA_TYPE_DECIMAL)
        else:
            return (int(num_str), DATA_TYPE_INTEGER)
    return (0, DATA_TYPE_INTEGER)


def process_input_data(data: Union[int, float, str]) -> Tuple[Union[int, float], str, int]:
    """
    处理输入数据，根据类型进行转换

    数据处理规则：
    - 整数数据：直接返回
    - 小数数据：乘10转换为整数
    - 百分比数据：移除%符号后按小数/整数处理

    Args:
        data: 输入数据（整数、小数或百分比字符串）

    Returns:
        (处理后的值, 原始数据类型, 缩放因子)
    """
    if isinstance(data, str):
        if data.strip().endswith('%'):
            # 百分比数据
            num_val, data_type = parse_percentage(data)
            if data_type == DATA_TYPE_DECIMAL:
                return (num_val * 10, DATA_TYPE_PERCENTAGE, 10)
            else:
                return (num_val, DATA_TYPE_PERCENTAGE, 1)
        else:
            # 普通字符串，尝试解析
            try:
                num_val = float(data)
                if num_val == int(num_val):
                    return (int(num_val), DATA_TYPE_INTEGER, 1)
                else:
                    return (num_val * 10, DATA_TYPE_DECIMAL, 10)
            except ValueError:
                return (data, DATA_TYPE_INTEGER, 1)
    
    elif isinstance(data, float):
        if data == int(data):
            return (int(data), DATA_TYPE_INTEGER, 1)
        else:
            return (data * 10, DATA_TYPE_DECIMAL, 10)
    
    elif isinstance(data, int):
        return (data, DATA_TYPE_INTEGER, 1)
    
    return (data, DATA_TYPE_INTEGER, 1)


def restore_data(processed_value: Union[int, float], data_type: str, scale_factor: int) -> Union[int, float, str]:
    """
    还原处理后的数据，确保双向一致性

    Args:
        processed_value: 处理后的值
        data_type: 原始数据类型标识
        scale_factor: 缩放因子（1或10）

    Returns:
        还原后的数据，如果是百分比类型则添加%符号
    """
    if scale_factor == 10:
        restored = processed_value / 10
    else:
        restored = processed_value
    
    # 如果是整数且缩放后仍是整数，返回整数类型
    if isinstance(restored, float) and restored == int(restored):
        restored = int(restored)
    
    # 如果是百分比类型，添加%符号
    if data_type == DATA_TYPE_PERCENTAGE:
        return f"{restored}%"
    
    return restored


def add_metadata_to_value(value: Union[int, float, str], key: str = DATA_TYPE_KEY) -> Dict[str, Any]:
    """
    为单个值添加元数据

    Args:
        value: 原始值
        key: 元数据键名

    Returns:
        包含元数据的字典
    """
    processed, data_type, scale_factor = process_input_data(value)
    
    if scale_factor == 1:
        # 整数数据，直接存储值
        return {
            key: data_type,
            'value': processed
        }
    else:
        # 小数数据，存储缩放后的值和缩放因子
        return {
            key: data_type,
            'value': processed,
            'scale_factor': scale_factor
        }


def extract_value_from_metadata(metadata_dict: Dict[str, Any]) -> Union[int, float, str]:
    """
    从元数据字典中提取并还原原始值

    Args:
        metadata_dict: 包含元数据的字典

    Returns:
        还原后的原始值
    """
    data_type = metadata_dict.get(DATA_TYPE_KEY, DATA_TYPE_INTEGER)
    value = metadata_dict.get('value', 0)
    scale_factor = metadata_dict.get('scale_factor', 1)
    
    return restore_data(value, data_type, scale_factor)


def process_list_with_metadata(data_list: List[Union[int, float, str]]) -> List[Dict[str, Any]]:
    """
    处理列表数据，为每个元素添加元数据

    Args:
        data_list: 原始数据列表

    Returns:
        包含元数据的字典列表
    """
    result = []
    for value in data_list:
        result.append(add_metadata_to_value(value))
    return result


def restore_list_from_metadata(metadata_list: List[Dict[str, Any]]) -> List[Union[int, float, str]]:
    """
    从元数据列表中还原原始数据列表

    Args:
        metadata_list: 包含元数据的字典列表

    Returns:
        还原后的原始数据列表
    """
    result = []
    for item in metadata_list:
        result.append(extract_value_from_metadata(item))
    return result