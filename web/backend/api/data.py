import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/api/data", tags=["data"])

DATA_ROOT = Path(__file__).resolve().parents[3] / "adapters" / "endfield" / "data"

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


# ── 角色 ──────────────────────────────────────────────


@router.get("/characters", summary="获取所有角色列表（精简）")
async def list_characters():
    """返回所有角色的摘要信息（不含成长曲线数组）。"""
    raw = _load_json(CHARACTERS_PATH)
    result = []
    for c in raw:
        result.append({
            "名称": c.get("名称"),
            "类型": c.get("类型"),
            "星级": c.get("星级"),
            "武器": c.get("武器"),
            "主能力": c.get("主能力"),
            "副能力": c.get("副能力"),
        })
    return result


@router.get("/characters/{name}", summary="获取指定角色完整数据")
async def get_character(name: str):
    """返回指定名称角色的完整 JSON 数据（含成长曲线）。"""
    name = name.strip()
    raw = _load_json(CHARACTERS_PATH)
    for c in raw:
        if c.get("名称") == name:
            return c
    raise HTTPException(status_code=404, detail=f"角色 '{name}' 未找到")


@router.get("/characters/detail/all", summary="获取所有角色完整数据")
async def list_characters_full():
    """返回所有角色的完整 JSON 数据。"""
    return _load_json(CHARACTERS_PATH)


# ── 武器 ──────────────────────────────────────────────


@router.get("/weapons", summary="获取所有武器列表（精简）")
async def list_weapons():
    """返回所有武器的摘要信息（不含成长曲线数组）。"""
    raw = _load_json(WEAPONS_PATH)
    result = []
    for w in raw:
        entry = {
            "名称": w.get("名称"),
            "类型": w.get("类型"),
            "星级": w.get("星级"),
        }
        if "附加属性" in w:
            entry["附加属性"] = w["附加属性"]
        if "武器技能" in w:
            entry["武器技能"] = w["武器技能"]
        if "普通技能" in w:
            entry["普通技能"] = w["普通技能"]
        if "特殊技能" in w:
            entry["特殊技能"] = w["特殊技能"]
        result.append(entry)
    return result


@router.get("/weapons/{name}", summary="获取指定武器完整数据")
async def get_weapon(name: str):
    """返回指定名称武器的完整 JSON 数据（含成长曲线）。"""
    name = name.strip()
    raw = _load_json(WEAPONS_PATH)
    for w in raw:
        if w.get("名称") == name:
            return w
    raise HTTPException(status_code=404, detail=f"武器 '{name}' 未找到")


@router.get("/weapons/detail/all", summary="获取所有武器完整数据")
async def list_weapons_full():
    """返回所有武器的完整 JSON 数据。"""
    return _load_json(WEAPONS_PATH)


# ── 装备 ──────────────────────────────────────────────


@router.get("/equipments", summary="获取所有装备列表（精简）")
async def list_equipments():
    """返回所有装备的摘要信息。"""
    raw = _load_json(EQUIPMENTS_PATH)
    result = []
    for e in raw:
        result.append({
            "名称": e.get("名称"),
            "装备种类": e.get("装备种类"),
            "部位": e.get("部位"),
            "稀有度": e.get("稀有度"),
            "所属套组": e.get("所属套组"),
            "属性词条": e.get("属性词条", []),
            "三件套效果": e.get("三件套效果", []),
        })
    return result


@router.get("/equipments/{name}", summary="获取指定装备完整数据")
async def get_equipment(name: str):
    """返回指定名称装备的完整 JSON 数据。"""
    name = name.strip()
    raw = _load_json(EQUIPMENTS_PATH)
    for e in raw:
        if e.get("名称") == name:
            return e
    raise HTTPException(status_code=404, detail=f"装备 '{name}' 未找到")


@router.get("/equipments/detail/all", summary="获取所有装备完整数据")
async def list_equipments_full():
    """返回所有装备的完整 JSON 数据。"""
    return _load_json(EQUIPMENTS_PATH)


# ── 装备过滤与分类 ────────────────────────────────────


@router.get("/equipments/set/{set_name}", summary="按套组名称过滤装备")
async def get_equipment_by_set(set_name: str):
    """返回指定套组名称下的所有装备。"""
    raw = _load_json(EQUIPMENTS_PATH)
    result = [e for e in raw if e.get("所属套组") == set_name or e.get("套装") == set_name]
    if not result:
        raise HTTPException(status_code=404, detail=f"套组 '{set_name}' 未找到")
    return result


@router.get("/equipments/slot/{slot}", summary="按部位过滤装备")
async def get_equipment_by_slot(slot: str):
    """返回指定部位的装备列表（护手/护甲/配件）。"""
    raw = _load_json(EQUIPMENTS_PATH)
    return [e for e in raw if e.get("部位") == slot]


# ── 摘要统计 ──────────────────────────────────────────


@router.get("/summary", summary="数据摘要统计")
async def data_summary():
    """返回角色/武器/装备的数量统计。"""
    chars = _load_json(CHARACTERS_PATH)
    weps = _load_json(WEAPONS_PATH)
    equips = _load_json(EQUIPMENTS_PATH)
    return {
        "characters_count": len(chars),
        "weapons_count": len(weps),
        "equipments_count": len(equips),
        "equipment_sets": list({e.get("所属套组") for e in equips if e.get("所属套组")}),
        "character_types": list({c.get("类型") for c in chars if c.get("类型")}),
        "weapon_types": list({w.get("类型") for w in weps if w.get("类型")}),
    }
