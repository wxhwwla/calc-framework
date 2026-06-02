# SPDX-License-Identifier: AGPL-3.0
"""游戏数据查询 API — 角色/武器/装备的 CRUD 路由 + 摘要统计 + 公式反推 + 多游戏 profile。"""

import json

from pathlib import Path

from typing import Any

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel



router = APIRouter(prefix="/api/data", tags=["data"])



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





class InverseRequest(BaseModel):

    type: str

    values: list[float]





class InverseResponse(BaseModel):

    base: float

    growth: float

    divisor: int

    offset: float

    special: list[float] | None = None

    formula: str

    valid: bool

    details: str





# ── 角色 ──────────────────────────────────────────────





@router.get("/characters", summary="获取所有角色列表（精简）")

async def list_characters():

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

    name = name.strip()

    raw = _load_json(CHARACTERS_PATH)

    for c in raw:

        if c.get("名称") == name:

            return c

    raise HTTPException(status_code=404, detail=f"角色 '{name}' 未找到")





@router.get("/characters/detail/all", summary="获取所有角色完整数据")

async def list_characters_full():

    return _load_json(CHARACTERS_PATH)





@router.post("/characters", summary="新增角色")

async def create_character(data: dict[str, Any]):

    from api.data_mutations import create_character as _create

    return _create(data)





@router.put("/characters/{name}", summary="更新角色")

async def update_character(name: str, data: dict[str, Any]):

    from api.data_mutations import update_character as _update

    return _update(name, data)





@router.delete("/characters/{name}", summary="删除角色")

async def delete_character(name: str):

    from api.data_mutations import delete_character as _delete

    return _delete(name)





# ── 武器 ──────────────────────────────────────────────





@router.get("/weapons", summary="获取所有武器列表（精简）")

async def list_weapons():

    raw = _load_json(WEAPONS_PATH)

    result = []

    for w in raw:

        entry = {

            "名称": w.get("名称"),

            "类型": w.get("类型"),

            "星级": w.get("星级"),

        }

        for k in ("附加属性", "武器技能", "普通技能", "特殊技能"):

            if k in w:

                entry[k] = w[k]

        result.append(entry)

    return result





@router.get("/weapons/{name}", summary="获取指定武器完整数据")

async def get_weapon(name: str):

    name = name.strip()

    raw = _load_json(WEAPONS_PATH)

    for w in raw:

        if w.get("名称") == name:

            return w

    raise HTTPException(status_code=404, detail=f"武器 '{name}' 未找到")





@router.get("/weapons/detail/all", summary="获取所有武器完整数据")

async def list_weapons_full():

    return _load_json(WEAPONS_PATH)





@router.post("/weapons", summary="新增武器")

async def create_weapon(data: dict[str, Any]):

    from api.data_mutations import create_weapon as _create

    return _create(data)





@router.put("/weapons/{name}", summary="更新武器")

async def update_weapon(name: str, data: dict[str, Any]):

    from api.data_mutations import update_weapon as _update

    return _update(name, data)





@router.delete("/weapons/{name}", summary="删除武器")

async def delete_weapon(name: str):

    from api.data_mutations import delete_weapon as _delete

    return _delete(name)





# ── 装备 ──────────────────────────────────────────────





@router.get("/equipments", summary="获取所有装备列表（精简）")

async def list_equipments():

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

    name = name.strip()

    raw = _load_json(EQUIPMENTS_PATH)

    for e in raw:

        if e.get("名称") == name:

            return e

    raise HTTPException(status_code=404, detail=f"装备 '{name}' 未找到")





@router.get("/equipments/detail/all", summary="获取所有装备完整数据")

async def list_equipments_full():

    return _load_json(EQUIPMENTS_PATH)





@router.post("/equipments", summary="新增装备")

async def create_equipment(data: dict[str, Any]):

    from api.data_mutations import create_equipment as _create

    return _create(data)





@router.put("/equipments/{name}", summary="更新装备")

async def update_equipment(name: str, data: dict[str, Any]):

    from api.data_mutations import update_equipment as _update

    return _update(name, data)





@router.delete("/equipments/{name}", summary="删除装备")

async def delete_equipment(name: str):

    from api.data_mutations import delete_equipment as _delete

    return _delete(name)





# ── 装备过滤与分类 ────────────────────────────────────





@router.get("/equipments/set/{set_name}", summary="按套组名称过滤装备")

async def get_equipment_by_set(set_name: str):

    raw = _load_json(EQUIPMENTS_PATH)

    result = [e for e in raw if e.get("所属套组") == set_name or e.get("套装") == set_name]

    if not result:

        raise HTTPException(status_code=404, detail=f"套组 '{set_name}' 未找到")

    return result





@router.get("/equipments/slot/{slot}", summary="按部位过滤装备")

async def get_equipment_by_slot(slot: str):

    raw = _load_json(EQUIPMENTS_PATH)

    return [e for e in raw if e.get("部位") == slot]





# ── 摘要统计 ──────────────────────────────────────────





@router.get("/summary", summary="数据摘要统计")

async def data_summary():

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





# ── 公式反推 ──────────────────────────────────────────





@router.post("/inverse", summary="公式反推", response_model=InverseResponse)

async def inverse_formula(req: InverseRequest):

    from api.data_mutations import inverse_formula_payload

    result = inverse_formula_payload(req.type, req.values)

    return InverseResponse(**result)


# ── 多游戏 profile（对齐桌面 data_editor/profiles.py）────────────────


@router.get("/profiles", summary="数据录入 profile 列表")
async def list_data_profiles():
    from api.data_profiles import profiles_metadata

    return profiles_metadata()


@router.get("/profiles/{profile_id}/{entity_key}", summary="按 profile 列出实体")
async def list_profile_entity(profile_id: str, entity_key: str):
    from api.data_profiles import list_entity_rows

    return list_entity_rows(profile_id, entity_key)


@router.get("/profiles/{profile_id}/{entity_key}/detail/all", summary="完整实体列表")
async def list_profile_entity_full(profile_id: str, entity_key: str):
    from api.data_profiles import list_entity_rows

    return list_entity_rows(profile_id, entity_key, full=True)


@router.post("/profiles/{profile_id}/{entity_key}", summary="新增实体")
async def create_profile_entity(profile_id: str, entity_key: str, data: dict[str, Any]):
    from api.data_profiles import create_entity_row

    return create_entity_row(profile_id, entity_key, data)


@router.put("/profiles/{profile_id}/{entity_key}/{name}", summary="更新实体")
async def update_profile_entity(profile_id: str, entity_key: str, name: str, data: dict[str, Any]):
    from api.data_profiles import update_entity_row

    return update_entity_row(profile_id, entity_key, name, data)


@router.delete("/profiles/{profile_id}/{entity_key}/{name}", summary="删除实体")
async def delete_profile_entity(profile_id: str, entity_key: str, name: str):
    from api.data_profiles import delete_entity_row

    return delete_entity_row(profile_id, entity_key, name)

