# SPDX-License-Identifier: AGPL-3.0
"""游戏数据查询 API — 角色/武器/装备的 CRUD 路由 + 摘要统计 + 公式反推 + 多游戏 profile。"""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ._json_utils import ENDFIELD_DATA_ROOT, load_json

router = APIRouter(prefix="/api/data", tags=["data"])


DATA_ROOT = ENDFIELD_DATA_ROOT


CHARACTERS_PATH = DATA_ROOT / "characters.json"

WEAPONS_PATH = DATA_ROOT / "weapons.json"

EQUIPMENTS_PATH = DATA_ROOT / "equipments.json"


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
    raw = load_json(CHARACTERS_PATH)

    result = []

    for c in raw:
        result.append(
            {
                "名称": c.get("名称"),
                "类型": c.get("类型"),
                "星级": c.get("星级"),
                "武器": c.get("武器"),
                "主能力": c.get("主能力"),
                "副能力": c.get("副能力"),
            }
        )

    return result


@router.get("/characters/{name}", summary="获取指定角色完整数据")
async def get_character(name: str):
    name = name.strip()

    raw = load_json(CHARACTERS_PATH)

    for c in raw:
        if c.get("名称") == name:
            return c

    raise HTTPException(status_code=404, detail=f"角色 '{name}' 未找到")


@router.get("/characters/detail/all", summary="获取所有角色完整数据")
async def list_characters_full():
    return load_json(CHARACTERS_PATH)


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
    raw = load_json(WEAPONS_PATH)

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

    raw = load_json(WEAPONS_PATH)

    for w in raw:
        if w.get("名称") == name:
            return w

    raise HTTPException(status_code=404, detail=f"武器 '{name}' 未找到")


@router.get("/weapons/detail/all", summary="获取所有武器完整数据")
async def list_weapons_full():
    return load_json(WEAPONS_PATH)


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
    raw = load_json(EQUIPMENTS_PATH)

    result = []

    for e in raw:
        result.append(
            {
                "名称": e.get("名称"),
                "装备种类": e.get("装备种类"),
                "部位": e.get("部位"),
                "稀有度": e.get("稀有度"),
                "所属套组": e.get("所属套组"),
                "属性词条": e.get("属性词条", []),
                "三件套效果": e.get("三件套效果", []),
            }
        )

    return result


@router.get("/equipments/{name}", summary="获取指定装备完整数据")
async def get_equipment(name: str):
    name = name.strip()

    raw = load_json(EQUIPMENTS_PATH)

    for e in raw:
        if e.get("名称") == name:
            return e

    raise HTTPException(status_code=404, detail=f"装备 '{name}' 未找到")


@router.get("/equipments/detail/all", summary="获取所有装备完整数据")
async def list_equipments_full():
    return load_json(EQUIPMENTS_PATH)


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
    raw = load_json(EQUIPMENTS_PATH)

    result = [e for e in raw if e.get("所属套组") == set_name or e.get("套装") == set_name]

    if not result:
        raise HTTPException(status_code=404, detail=f"套组 '{set_name}' 未找到")

    return result


@router.get("/equipments/slot/{slot}", summary="按部位过滤装备")
async def get_equipment_by_slot(slot: str):
    raw = load_json(EQUIPMENTS_PATH)

    return [e for e in raw if e.get("部位") == slot]


# ── 摘要统计 ──────────────────────────────────────────


@router.get("/summary", summary="数据摘要统计")
async def data_summary():
    chars = load_json(CHARACTERS_PATH)

    weps = load_json(WEAPONS_PATH)

    equips = load_json(EQUIPMENTS_PATH)

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


# ── DAG 验证（数据编辑器 → 跑 DAG 看结果对不对）─────────

from pydantic import Field as PydanticField


class DagVerifyRequest(BaseModel):
    profile_id: str = PydanticField(default="endfield", description="数据模板 ID（endfield / arknights）")
    entity_key: str = PydanticField(default="characters", description="实体类型（characters / weapons / equipments）")
    entity_name: str = PydanticField(description="实体名称（如 '佩丽卡'）")
    level: int = PydanticField(default=90, ge=1, le=99, description="等级")


class DagVerifyResponse(BaseModel):
    entity_name: str
    level: int
    outputs: dict[str, float]
    node_values: dict[str, float]
    node_count: int


_PROFILE_ADAPTER_MAP: dict[str, str] = {
    "endfield": "终末地伤害计算",
    "arknights": "明日方舟",
}


def _extract_level_curve_value(entity: dict, attr_name: str, level: int) -> float:
    """从实体 JSON 中提取指定属性在指定等级的值（level curve 数组）。"""
    arr = entity.get(attr_name, [])
    if isinstance(arr, list) and len(arr) >= level:
        return float(arr[level - 1])
    # fallback: try as scalar
    val = entity.get(attr_name, 0)
    return float(val) if val else 0.0


def _build_dag_verify_context(entity: dict, entity_key: str, level: int) -> dict:
    """构建 DAG 验证用的上下文 dict（对齐桌面 DataEditorPanel._dag_verify）。"""
    if entity_key == "characters":
        char_attrs = {
            "基础攻击": _extract_level_curve_value(entity, "基础攻击力", level),
            "力量": _extract_level_curve_value(entity, "力量", level),
            "敏捷": _extract_level_curve_value(entity, "敏捷", level),
            "智识": _extract_level_curve_value(entity, "智识", level),
            "意志": _extract_level_curve_value(entity, "意志", level),
            "暴击率": 0.05,
            "暴击伤害": 1.5,
        }
    else:
        char_attrs = {
            "基础攻击": 100,
            "力量": 100,
            "敏捷": 100,
            "智识": 100,
            "意志": 100,
            "暴击率": 0.05,
            "暴击伤害": 1.5,
        }

    return {
        "character": char_attrs,
        "weapon": {"基础攻击": 0, "攻击力+": 0, "附加攻击力+": 0},
        "equipment": {"攻击力平值": 0},
        "enemy": {"防御": 100},
        "computed": {
            "主能力平值加算": 0,
            "副能力平值加算": 0,
            "主能力百分比": 0,
            "副能力百分比": 0,
            "技能倍率": 1.0,
            "伤害加成": 0,
            "伤害减免": 0,
            "增幅": 0,
            "虚弱": 0,
            "庇护": 0,
            "脆弱": 0,
            "易伤": 0,
            "失衡易伤": 0,
            "抗性": 0,
            "非主控减伤": 0,
            "连击增伤": 0,
            "特殊乘区": 0,
            "力量加成值": 0,
            "敏捷加成值": 0,
            "智识加成值": 0,
            "意志加成值": 0,
        },
    }


@router.post("/dag-verify", summary="DAG 验证 — 加载数据 → 跑 DAG 看计算结果", response_model=DagVerifyResponse)
async def dag_verify(req: DagVerifyRequest):
    """用于数据编辑器验证：选中角色/武器 → 一键跑 DAG 查看乘区输出是否合理。"""
    from api.data_profiles import get_entity, list_entity_rows

    get_entity(req.profile_id, req.entity_key)  # validate entity exists
    rows = list_entity_rows(req.profile_id, req.entity_key, full=True)

    entity = next((r for r in rows if r.get("名称") == req.entity_name), None)
    if entity is None:
        raise HTTPException(status_code=404, detail=f"未找到实体: {req.entity_name}")

    adapter_name = _PROFILE_ADAPTER_MAP.get(req.profile_id)
    if not adapter_name:
        raise HTTPException(status_code=400, detail=f"不支持的 profile: {req.profile_id}")

    from calc_framework.config.manager import AdapterManager

    from ._json_utils import ADAPTER_ROOT

    manager = AdapterManager(ADAPTER_ROOT)
    try:
        pkg = manager.load(adapter_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"加载适配器失败: {e}")

    context = _build_dag_verify_context(entity, req.entity_key, req.level)

    try:
        result = pkg.dag_service.evaluate(context)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DAG 求值失败: {e}")

    return DagVerifyResponse(
        entity_name=req.entity_name,
        level=req.level,
        outputs=result.outputs,
        node_values={k: v for k, v in result.node_values.items() if isinstance(v, int | float)},
        node_count=len(result.node_values),
    )


# ── 数据验证 ──────────────────────────────────────────


class ValidateRequest(BaseModel):
    profile_id: str = PydanticField(default="endfield", description="数据模板 ID")
    entity_key: str = PydanticField(default="characters", description="实体类型")


class ValidateResponse(BaseModel):
    profile_id: str
    entity_key: str
    total: int
    valid: int
    errors: list[dict]  # [{index, name, messages}]


# 各实体类型的必填字段
_REQUIRED_FIELDS: dict[str, list[str]] = {
    "characters": ["名称", "类型", "星级", "武器", "主能力", "副能力"],
    "weapons": ["名称", "类型", "星级"],
    "equipments": ["名称", "部位", "稀有度"],
    "operators": ["名称", "职业", "星级", "分支"],
}

# 各实体类型的数值等级曲线字段（需检查数组长度 ≥ 90）
_LEVEL_CURVE_FIELDS: dict[str, list[str]] = {
    "characters": ["基础攻击力", "力量", "敏捷", "智识", "意志"],
    "weapons": ["基础攻击力"],
}


@router.post("/validate", summary="数据校验 — 检查必填字段、等级曲线完整性", response_model=ValidateResponse)
async def validate_data(req: ValidateRequest):
    """批量校验数据实体：检查必填字段、等级曲线长度等。"""
    from api.data_profiles import list_entity_rows

    rows = list_entity_rows(req.profile_id, req.entity_key, full=True)
    required = _REQUIRED_FIELDS.get(req.entity_key, ["名称"])
    curves = _LEVEL_CURVE_FIELDS.get(req.entity_key, [])

    error_list: list[dict] = []
    valid_count = 0

    for i, entity in enumerate(rows):
        name = entity.get("名称", f"[{i}]")
        messages: list[str] = []

        # 检查必填字段
        for field in required:
            val = entity.get(field)
            if val is None or val == "":
                messages.append(f"缺少必填字段 '{field}'")

        # 检查等级曲线长度
        for field in curves:
            arr = entity.get(field, [])
            if isinstance(arr, list):
                if len(arr) < 80:
                    messages.append(f"等级曲线 '{field}' 长度不足 ({len(arr)}，期望 ≥80)")

        if messages:
            error_list.append({"index": i, "name": str(name), "messages": messages})
        else:
            valid_count += 1

    return ValidateResponse(
        profile_id=req.profile_id,
        entity_key=req.entity_key,
        total=len(rows),
        valid=valid_count,
        errors=error_list,
    )


__all__: list[str] = []
