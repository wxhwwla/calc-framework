# SPDX-License-Identifier: AGPL-3.0
"""游戏 JSON 数据读写（FastAPI 与 WSGI 共用）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

DATA_ROOT = Path(__file__).resolve().parents[3] / "games" / "endfield" / "data"
CHARACTERS_PATH = DATA_ROOT / "characters.json"
WEAPONS_PATH = DATA_ROOT / "weapons.json"
EQUIPMENTS_PATH = DATA_ROOT / "equipments.json"


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"数据文件不存在: {path.name}")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise HTTPException(status_code=500, detail=f"数据格式错误: {path.name} 根节点不是数组")
        return data
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON 解析失败: {path.name}: {e}")


def _save_json(path: Path, data: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _find_by_name(data: list[dict[str, Any]], name: str) -> int | None:
    for i, item in enumerate(data):
        if item.get("名称") == name:
            return i
    return None


def create_character(data: dict[str, Any]) -> dict[str, str]:
    raw = _load_json(CHARACTERS_PATH)
    if _find_by_name(raw, data.get("名称", "")) is not None:
        raise HTTPException(status_code=409, detail=f"角色 '{data.get('名称')}' 已存在")
    raw.append(data)
    _save_json(CHARACTERS_PATH, raw)
    return {"message": "ok"}


def update_character(name: str, data: dict[str, Any]) -> dict[str, str]:
    raw = _load_json(CHARACTERS_PATH)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"角色 '{name}' 未找到")
    raw[idx] = data
    _save_json(CHARACTERS_PATH, raw)
    return {"message": "ok"}


def delete_character(name: str) -> dict[str, str]:
    raw = _load_json(CHARACTERS_PATH)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"角色 '{name}' 未找到")
    raw.pop(idx)
    _save_json(CHARACTERS_PATH, raw)
    return {"message": "ok"}


def create_weapon(data: dict[str, Any]) -> dict[str, str]:
    raw = _load_json(WEAPONS_PATH)
    if _find_by_name(raw, data.get("名称", "")) is not None:
        raise HTTPException(status_code=409, detail=f"武器 '{data.get('名称')}' 已存在")
    raw.append(data)
    _save_json(WEAPONS_PATH, raw)
    return {"message": "ok"}


def update_weapon(name: str, data: dict[str, Any]) -> dict[str, str]:
    raw = _load_json(WEAPONS_PATH)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"武器 '{name}' 未找到")
    raw[idx] = data
    _save_json(WEAPONS_PATH, raw)
    return {"message": "ok"}


def delete_weapon(name: str) -> dict[str, str]:
    raw = _load_json(WEAPONS_PATH)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"武器 '{name}' 未找到")
    raw.pop(idx)
    _save_json(WEAPONS_PATH, raw)
    return {"message": "ok"}


def create_equipment(data: dict[str, Any]) -> dict[str, str]:
    raw = _load_json(EQUIPMENTS_PATH)
    if _find_by_name(raw, data.get("名称", "")) is not None:
        raise HTTPException(status_code=409, detail=f"装备 '{data.get('名称')}' 已存在")
    raw.append(data)
    _save_json(EQUIPMENTS_PATH, raw)
    return {"message": "ok"}


def update_equipment(name: str, data: dict[str, Any]) -> dict[str, str]:
    raw = _load_json(EQUIPMENTS_PATH)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"装备 '{name}' 未找到")
    raw[idx] = data
    _save_json(EQUIPMENTS_PATH, raw)
    return {"message": "ok"}


def delete_equipment(name: str) -> dict[str, str]:
    raw = _load_json(EQUIPMENTS_PATH)
    idx = _find_by_name(raw, name)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"装备 '{name}' 未找到")
    raw.pop(idx)
    _save_json(EQUIPMENTS_PATH, raw)
    return {"message": "ok"}


def inverse_formula_payload(type_: str, values: list[float]) -> dict[str, Any]:
    try:
        from games.endfield.calc.damage.inverse import (
            fit_attribute_formula,
            fit_skill_formula,
            fit_skill_formula_no_special,
            remove_duplicates,
            validate_attribute_formula,
            validate_skill_formula,
        )
        from games.endfield.calc.damage.formula import calculate_growth_curve
    except ImportError as e:
        raise HTTPException(status_code=500, detail=f"逆推引擎导入失败: {e}") from e

    data = values
    if type_ == "attribute":
        if len(data) == 94:
            data = remove_duplicates(data)
        if len(data) != 90:
            raise HTTPException(status_code=400, detail=f"属性数据需要90个值，当前{len(data)}个")
        base, growth, divisor, offset = fit_attribute_formula(data)
        formula = f"base + floor(({growth} * (lv - 1) + {offset}) / {divisor})"
        valid = validate_attribute_formula(base, growth, divisor, offset, data)
        curve = calculate_growth_curve(base, growth, divisor, offset)
        details = (
            f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}\n"
            f"已验证: {'✓' if valid else '✗'}\n"
            f"生成曲线（前10级）: {', '.join(map(str, curve[:10]))}…"
        )
        return {
            "base": float(base),
            "growth": float(growth),
            "divisor": int(divisor),
            "offset": float(offset),
            "special": None,
            "formula": formula,
            "valid": valid,
            "details": details,
        }

    if type_ == "skill":
        if len(data) == 12:
            base, growth, divisor, offset, special = fit_skill_formula(data)
        elif len(data) == 9:
            base, growth, divisor, offset, special = fit_skill_formula_no_special(data)
        else:
            raise HTTPException(status_code=400, detail=f"技能数据需要9或12个值，当前{len(data)}个")
        formula = f"base + floor(({growth} * (lv - 1) + {offset}) / {divisor})"
        valid = validate_skill_formula(base, growth, divisor, offset, special, data)
        details = (
            f"参数: base={base}, growth={growth}, divisor={divisor}, offset={offset}, special={special}\n"
            f"已验证: {'✓' if valid else '✗'}"
        )
        return {
            "base": float(base),
            "growth": float(growth),
            "divisor": int(divisor),
            "offset": float(offset),
            "special": special,
            "formula": formula,
            "valid": valid,
            "details": details,
        }

    raise HTTPException(status_code=400, detail=f"不支持的逆推类型: {type_}")
