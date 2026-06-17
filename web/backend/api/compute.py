# SPDX-License-Identifier: AGPL-3.0
"""DAG 计算引擎 API — 快照/配装/对比/预设导出。"""

from typing import Any

from api.internal.errors import raise_http_from_exc
from api.internal.json_utils import ADAPTER_ROOT, ENDFIELD_DATA_ROOT, load_json
from api.search_lib.loadout_schemas import WebLoadoutBody
from calc_framework.config.manager import AdapterManager
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

ENDFIELD_ADAPTER_NAME = "终末地伤害计算（Calc Framework）"

router = APIRouter(prefix="/api/compute", tags=["compute"])

_manager = AdapterManager(ADAPTER_ROOT)

_DATA = ENDFIELD_DATA_ROOT


class EvaluateRequest(BaseModel):
    """DAG 求值请求。"""

    adapter: str
    """适配器名称。"""
    context: dict
    """求值上下文（DataContext 兼容格式）。"""


class EvaluateResponse(BaseModel):
    """DAG 求值响应。"""

    outputs: dict[str, float]
    """命名输出值（key 为输出名，value 为计算结果）。"""
    node_values: dict[str, float | str | None]
    """所有节点的中间值（用于调试展示）。"""
    execution_order: list[str]
    """节点执行顺序。"""


def evaluate_payload(req: EvaluateRequest) -> EvaluateResponse:
    """加载适配器并执行 DAG 求值。"""
    try:
        pkg = _manager.load(req.adapter)
    except KeyError as e:
        raise_http_from_exc(e, status_code=404, public_message="适配器不存在")
    except Exception as e:
        raise_http_from_exc(e, status_code=500)

    try:
        result = pkg.dag_service.evaluate(req.context)
    except Exception as e:
        raise_http_from_exc(e, status_code=400)

    return EvaluateResponse(
        outputs=result.outputs,
        node_values={k: v for k, v in result.node_values.items()},
        execution_order=result.execution_order,
    )


@router.post("/evaluate", response_model=EvaluateResponse)
def evaluate(req: EvaluateRequest):
    return evaluate_payload(req)


class LoadoutPreviewRequest(WebLoadoutBody):
    pass


class LoadoutSnapshotRequest(WebLoadoutBody):
    pass


class PresetExportRequest(WebLoadoutBody):
    pass


def _build_loadout_context(req: LoadoutPreviewRequest) -> dict[str, Any]:
    """WebLoadoutBody → DAG adapter context。"""
    from api.search_lib.catalog import resolve_equipment_catalog

    from games.endfield.data_loading.web_loadout_bridge import (
        build_adapter_context_from_loadout,
        build_loadout_state_from_web,
    )

    body = req.to_loadout_dict()
    layout_mode = str(body.get("calc_mode") or body.get("calculation_mode") or "zone_snapshot")
    if layout_mode.endswith("_search"):
        layout_mode = "zone_snapshot"
    loadout = build_loadout_state_from_web(
        char_data=req.char_data,
        weapon_data=req.weapon_data,
        body=body,
    )
    catalog = req.equipment_catalog
    if catalog is None:
        catalog = resolve_equipment_catalog(
            None,
            equipment_scope_label=str(body.get("equipment_scope_label") or "全部装备"),
        )
    return build_adapter_context_from_loadout(
        loadout,
        layout_calc_mode=layout_mode,
        equipment_catalog=catalog,
    )


@router.post("/evaluate-loadout", response_model=EvaluateResponse)
def evaluate_loadout(req: LoadoutPreviewRequest):
    """经 LoadoutState 构建 context 后求值（与桌面确认路径对齐）。"""
    try:
        ctx = _build_loadout_context(req)
        pkg = _manager.load(ENDFIELD_ADAPTER_NAME)
        result = pkg.dag_service.evaluate(ctx)
        return EvaluateResponse(
            outputs=result.outputs,
            node_values={k: v for k, v in result.node_values.items()},
            execution_order=result.execution_order,
        )
    except KeyError as exc:
        raise_http_from_exc(exc, status_code=404)
    except Exception as exc:
        raise_http_from_exc(exc, status_code=400)


class LoadoutContextResponse(BaseModel):
    context: dict[str, Any]


@router.post("/loadout-context", response_model=LoadoutContextResponse)
def loadout_context(req: LoadoutPreviewRequest):
    """返回配装 DAG 求值上下文（供浏览器 wasm 本地求值）。"""
    try:
        return LoadoutContextResponse(context=_build_loadout_context(req))
    except KeyError as exc:
        raise_http_from_exc(exc, status_code=404)
    except Exception as exc:
        raise_http_from_exc(exc, status_code=400)


class SnapshotRequest(BaseModel):
    """伤害快照计算请求（直接参数，不走 LoadoutState）。"""

    char_name: str
    weapon_name: str
    char_level: int = 90
    weapon_level: int = 90
    trust_level: int = 0
    skill_1_level: int = 8
    skill_2_level: int = 8
    skill_3_level: int = 8
    normal_skill_1_level: int = 1
    normal_skill_2_level: int = 1
    normal_skill_3_level: int = 0
    special_skill_1_level: int = 1
    special_skill_1_stack: int = 0
    special_skill_2_level: int = 1
    special_skill_2_stack: int = 0
    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    is_unbalanced: bool = False
    is_true_damage: bool = False
    combo_stacks: int = 0
    break_defense_stacks: int = 0
    damage_component_mode: str = "skill_and_abnormal"
    extra_crit_rate: float = 0.0
    extra_crit_damage: float = 0.0


_CHARACTERS_PATH = _DATA / "characters.json"

_WEAPONS_PATH = _DATA / "weapons.json"


def snapshot_payload(req: SnapshotRequest) -> dict:
    from games.endfield.gui.presentation.damage_snapshot import build_damage_snapshot

    chars = load_json(_CHARACTERS_PATH) or []

    char_data = next((c for c in chars if c.get("名称") == req.char_name), None)

    if not char_data:
        raise HTTPException(status_code=404, detail=f"角色不存在: {req.char_name}")

    weapons = load_json(_WEAPONS_PATH) or []

    weapon_data = next((w for w in weapons if w.get("名称") == req.weapon_name), None)

    if not weapon_data:
        raise HTTPException(status_code=404, detail=f"武器不存在: {req.weapon_name}")

    skill_counts: dict[str, int] = {}

    raw_skills = char_data.get("战技倍率", [])

    conn_skills = char_data.get("连携技倍率", [])

    ult_skills = char_data.get("终结技倍率", [])

    for seg_idx in range(max(len(raw_skills), len(conn_skills), len(ult_skills))):
        for st, arr in [("战技", raw_skills), ("连携技", conn_skills), ("终结技", ult_skills)]:
            if seg_idx < len(arr) and len(arr[seg_idx]) > 0:
                key = f"{st}:{seg_idx + 1}"

                skill_counts[key] = 1

    try:
        result = build_damage_snapshot(
            char_data=char_data,
            weapon_data=weapon_data,
            char_level=req.char_level,
            weapon_level=req.weapon_level,
            trust_level=req.trust_level,
            skill_levels=(req.skill_1_level, req.skill_2_level, req.skill_3_level),
            skill_counts=skill_counts,
            use_manual_counts=False,
            normal_skill_1_level=req.normal_skill_1_level,
            normal_skill_2_level=req.normal_skill_2_level,
            normal_skill_3_level=req.normal_skill_3_level,
            special_skill_1_level=req.special_skill_1_level,
            special_skill_1_stack=req.special_skill_1_stack,
            special_skill_2_level=req.special_skill_2_level,
            special_skill_2_stack=req.special_skill_2_stack,
            enemy_defense=req.enemy_defense,
            enemy_resistance=req.enemy_resistance,
            ignore_resistance=req.ignore_resistance,
            imbalance_vulnerability_coeff=req.imbalance_vulnerability_coeff,
            is_unbalanced=req.is_unbalanced,
            is_true_damage=req.is_true_damage,
            combo_stacks=req.combo_stacks,
            break_defense_stacks=req.break_defense_stacks,
        )

        return dict(
            segment_damage=result.segment_damage,
            segment_counts=result.segment_counts,
            segment_totals=result.segment_totals,
            skill_type_totals=result.skill_type_totals,
            weighted_total_damage=result.weighted_total_damage,
            rotation_share_percent=result.rotation_share_percent,
            zone_share_percent=result.zone_share_percent,
            selected_skill_label=result.selected_skill_label,
        )

    except Exception as e:
        raise_http_from_exc(e, status_code=400)


@router.post("/snapshot")
def snapshot(req: SnapshotRequest):
    """旧版快照计算（直接参数，不走 loadout）。"""
    return snapshot_payload(req)


class CompareEntry(BaseModel):
    """配装对比条目。"""

    label: str
    """显示标签。"""
    char_name: str
    weapon_name: str
    char_level: int = 90
    weapon_level: int = 90
    trust_level: int = 0
    skill_1_level: int = 8
    skill_2_level: int = 8
    skill_3_level: int = 8
    normal_skill_1_level: int = 1
    normal_skill_2_level: int = 1
    normal_skill_3_level: int = 0
    special_skill_1_level: int = 1
    special_skill_1_stack: int = 0
    special_skill_2_level: int = 1
    special_skill_2_stack: int = 0
    enemy_defense: float = 100.0
    enemy_resistance: float = 0.0
    ignore_resistance: float = 0.0
    imbalance_vulnerability_coeff: float = 1.3
    is_unbalanced: bool = False
    is_true_damage: bool = False
    combo_stacks: int = 0
    break_defense_stacks: int = 0


class CompareRequest(BaseModel):
    """多方案配装对比请求。"""

    entries: list[CompareEntry]


@router.post("/compare")
def compare(req: CompareRequest):
    """多方案配装对比，返回按总伤排序的结果列表。"""
    from games.endfield.data_loading.web_loadout_bridge import (
        build_loadout_state_from_web,
    )
    from games.endfield.gui.app.loadout_evaluation import build_snapshot_from_loadout

    chars = load_json(_CHARACTERS_PATH) or []
    weapons = load_json(_WEAPONS_PATH) or []

    results: list[dict] = []
    for entry in req.entries:
        char_data = next((c for c in chars if c.get("名称") == entry.char_name), None)
        weapon_data = next((w for w in weapons if w.get("名称") == entry.weapon_name), None)
        if not char_data or not weapon_data:
            results.append({"label": entry.label, "error": "角色或武器不存在", "total": 0})
            continue

        try:
            body = entry.model_dump()
            body.update(
                {
                    "enemy_defense": entry.enemy_defense,
                    "enemy_resistance": entry.enemy_resistance,
                    "ignore_resistance": entry.ignore_resistance,
                    "imbalance_vulnerability_coeff": entry.imbalance_vulnerability_coeff,
                    "is_unbalanced": entry.is_unbalanced,
                    "is_true_damage": entry.is_true_damage,
                    "combo_stacks": entry.combo_stacks,
                    "break_defense_stacks": entry.break_defense_stacks,
                    "skill_1_level": entry.skill_1_level,
                    "skill_2_level": entry.skill_2_level,
                    "skill_3_level": entry.skill_3_level,
                    "weapon_skill_values": {
                        "normal_skill_1_level": entry.normal_skill_1_level,
                        "normal_skill_2_level": entry.normal_skill_2_level,
                        "normal_skill_3_level": entry.normal_skill_3_level,
                        "special_skill_1_level": entry.special_skill_1_level,
                        "special_skill_1_stack": entry.special_skill_1_stack,
                        "special_skill_2_level": entry.special_skill_2_level,
                        "special_skill_2_stack": entry.special_skill_2_stack,
                    },
                }
            )
            loadout = build_loadout_state_from_web(
                char_data=char_data,
                weapon_data=weapon_data,
                body=body,
            )
            sn = build_snapshot_from_loadout(loadout)
            results.append({"label": entry.label, "total": sn.weighted_total_damage})
        except Exception as e:
            from web.backend.bridge import get_logger

            get_logger(__name__).warning("配装对比计算失败: %s", e)
            results.append({"label": entry.label, "error": "计算异常", "total": 0})

    results.sort(key=lambda r: r.get("total", 0), reverse=True)
    return results


@router.post("/preview")
def loadout_preview(req: LoadoutPreviewRequest) -> dict[str, list[str]]:
    """返回配装搜索前预览行（描述当前选定装备范围的文字）。"""
    from games.endfield.data_loading.equipment_catalog import get_equipment_catalog
    from games.endfield.data_loading.web_loadout_bridge import build_loadout_state_from_web
    from games.endfield.gui.app.loadout_evaluation import build_search_preview_lines

    catalog = req.equipment_catalog or get_equipment_catalog()
    try:
        loadout = build_loadout_state_from_web(
            char_data=req.char_data,
            weapon_data=req.weapon_data,
            body=req.to_loadout_dict(),
        )
        lines = build_search_preview_lines(loadout, equipment_catalog=catalog)
        return {"lines": lines}
    except Exception as exc:
        raise_http_from_exc(exc, status_code=400)


@router.post("/snapshot-full")
def loadout_snapshot(req: LoadoutSnapshotRequest) -> dict[str, Any]:
    """通过 LoadoutState 计算完整伤害快照（与桌面确认路径对齐）。"""
    from games.endfield.data_loading.web_loadout_bridge import build_loadout_state_from_web
    from games.endfield.gui.app.loadout_evaluation import build_snapshot_from_loadout

    try:
        loadout = build_loadout_state_from_web(
            char_data=req.char_data,
            weapon_data=req.weapon_data,
            body=req.to_loadout_dict(),
        )
        result = build_snapshot_from_loadout(loadout)
        return dict(
            segment_damage=result.segment_damage,
            segment_counts=result.segment_counts,
            segment_totals=result.segment_totals,
            skill_type_totals=result.skill_type_totals,
            weighted_total_damage=result.weighted_total_damage,
            rotation_share_percent=result.rotation_share_percent,
            zone_share_percent=result.zone_share_percent,
            selected_skill_label=result.selected_skill_label,
        )
    except Exception as exc:
        raise_http_from_exc(exc, status_code=400)


@router.post("/preset-export")
def preset_export(req: PresetExportRequest) -> dict[str, Any]:
    """将当前配装导出为可保存的预设 JSON。"""
    from games.endfield.data_loading.web_loadout_bridge import (
        build_loadout_state_from_web,
        loadout_state_to_web_preset,
    )

    loadout = build_loadout_state_from_web(
        char_data=req.char_data,
        weapon_data=req.weapon_data,
        body=req.to_loadout_dict(),
    )
    return loadout_state_to_web_preset(loadout)


__all__: list[str] = []
