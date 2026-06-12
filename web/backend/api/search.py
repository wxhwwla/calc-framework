# SPDX-License-Identifier: AGPL-3.0
"""配装搜索 API — 工作量预估/全量搜索/SSE 流式搜索/敌人数值/装备目录/搜索历史。"""

import asyncio
import json
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRequest(BaseModel):
    """全量搜索请求体。"""

    char_data: dict[str, Any] = Field(description="角色数据")
    char_level: int = Field(default=90, description="角色等级")
    weapon_level: int = Field(default=90, description="武器等级")
    trust_level: int = Field(default=0, description="信赖等级")
    skill_name: str = Field(description="技能名称")
    skill_type: str = Field(description="技能类型（战技/连携技/终结技）")
    skill_multiplier: float = Field(description="技能倍率")
    damage_type: str = Field(description="伤害类型")
    weapon_scope_label: str = Field(default="同类型", description="武器搜索范围标签")
    equipment_scope_label: str = Field(default="全部", description="装备搜索范围标签")
    all_weapons: list[dict[str, Any]] = Field(description="全部武器候选列表")
    current_weapon: dict[str, Any] = Field(description="当前选定武器")
    equipment_catalog: dict[str, list[dict[str, Any]]] = Field(description="装备目录")
    fixed_loadout: dict[str, Any] | None = Field(default=None, description="固定配装字段")
    fixed_equipment_names: dict[str, str | None] = Field(default_factory=dict, description="固定装备名称")
    weapon_skill_values: dict[str, Any] = Field(default_factory=dict, description="武器技能值")
    enemy_defense: float = Field(default=100.0, description="敌方防御力")
    enemy_resistance: float = Field(default=0.0, description="敌方抗性")
    ignore_resistance: float = Field(default=0.0, description="忽略抗性")
    imbalance_vulnerability_coeff: float = Field(default=1.3, description="失衡易伤系数")
    is_unbalanced: bool = Field(default=False, description="是否失衡")
    is_true_damage: bool = Field(default=False, description="是否真实伤害")
    combo_stacks: int = Field(default=0, description="连击层数")
    break_defense_stacks: int = Field(default=0, description="破防层数")
    attached_effect_multiplier: float = Field(default=1.0, description="附着效果倍率")
    corrosion_duration_seconds: float = Field(default=15.0, description="侵蚀持续时间（秒）")
    physical_abnormal_counts: dict[str, int] | None = Field(default=None, description="物理异常状态层数")
    spell_abnormal_counts: dict[str, int] | None = Field(default=None, description="法术异常状态层数")
    damage_component_mode: str = Field(default="skill_and_abnormal", description="伤害组件模式")
    top_n: int = Field(default=10, description="返回前 N 个结果")
    max_workers: int = Field(default=4, description="并行线程数")
    use_manual_multi_skill_counts: bool = Field(default=False, description="是否手动指定多段技能计数")
    manual_counts: dict[str, int] | None = Field(default=None, description="手动技能计数")
    skill_1_level: int = Field(default=0, description="技能 1 等级")
    skill_2_level: int = Field(default=0, description="技能 2 等级")
    skill_3_level: int = Field(default=0, description="技能 3 等级")
    use_expected_crit: bool = Field(default=False, description="是否使用期望暴击")
    include_conditional_equipment_crit: bool = Field(default=False, description="是否计入条件触发暴击")
    extra_crit_rate: float = Field(default=0.0, description="额外暴击率")
    extra_crit_damage: float = Field(default=0.0, description="额外暴击伤害")


class EstimateRequest(BaseModel):
    char_data: dict[str, Any]

    char_level: int = 90

    weapon_level: int = 90

    trust_level: int = 0

    skill_name: str

    skill_type: str

    skill_multiplier: float

    damage_type: str

    weapon_scope_label: str = "同类型"

    equipment_scope_label: str = "全部"

    all_weapons: list[dict[str, Any]]

    current_weapon: dict[str, Any]

    equipment_catalog: dict[str, list[dict[str, Any]]]

    fixed_loadout: dict[str, Any] | None = None

    fixed_equipment_names: dict[str, str | None] = {}

    weapon_skill_values: dict[str, Any] = {}

    enemy_defense: float = 100.0

    enemy_resistance: float = 0.0

    ignore_resistance: float = 0.0

    imbalance_vulnerability_coeff: float = 1.3

    is_unbalanced: bool = False

    is_true_damage: bool = False

    combo_stacks: int = 0

    break_defense_stacks: int = 0

    attached_effect_multiplier: float = 1.0

    corrosion_duration_seconds: float = 15.0

    physical_abnormal_counts: dict[str, int] | None = None

    spell_abnormal_counts: dict[str, int] | None = None

    damage_component_mode: str = "skill_and_abnormal"

    use_manual_multi_skill_counts: bool = False

    manual_counts: dict[str, int] | None = None

    skill_1_level: int = 0

    skill_2_level: int = 0

    skill_3_level: int = 0

    use_expected_crit: bool = False

    include_conditional_equipment_crit: bool = False

    extra_crit_rate: float = 0.0

    extra_crit_damage: float = 0.0


def _prepare_search_req(req: SearchRequest | EstimateRequest) -> tuple[Any, Any]:
    """归一化技能字段与固定配装字典（与 GUI 桌面端保持一致）。"""
    from games.endfield.data_loading.web_search_bridge import (
        enrich_search_request_fields,
        resolve_search_fixed_loadout,
    )

    enriched = req.model_copy(update=enrich_search_request_fields(req))
    fixed = resolve_search_fixed_loadout(enriched)
    return enriched, fixed


class LoadoutResult(BaseModel):
    weapon_name: str

    chest: str

    gloves: str

    accessory_a: str

    accessory_b: str

    final_damage: float

    segment_breakdown: dict[str, float] | None = None


@router.post("/estimate")
async def estimate_search(req: EstimateRequest):
    """预估搜索工作量（组合总数 + 预计耗时）。"""

    try:
        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.plan.estimate import (
            estimate_search_duration,
            preview_search_workload,
        )
        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError:
        raise HTTPException(status_code=500, detail="搜索引擎加载失败，请确认完整项目环境已安装")

    try:
        req, fixed_loadout = _prepare_search_req(req)

        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)

        job, err = prepare_search_job(inputs)

        if err or job is None:
            from web.backend.bridge import get_logger

            if err:
                get_logger(__name__).warning("搜索作业组装失败: %s", err)
            return {"total_combinations": 0, "estimated_seconds": 0, "warning": "搜索作业组装失败"}

        from games.endfield.calc.search.plan.controller import optimizer_config_for_search_job

        config = optimizer_config_for_search_job(job, top_n=10)

        preview = preview_search_workload(
            weapons=list(job.weapon_candidates),
            equipment_catalog=dict(job.equipment_catalog),
            config=config,
        )

        duration = estimate_search_duration(total_combinations=preview.total_combinations, max_workers=req.max_workers)

        return {
            "total_combinations": preview.total_combinations,
            "weapon_count": preview.weapon_count,
            "loadout_combinations": preview.loadout_combinations,
            "estimated_seconds": duration.estimated_seconds,
            "warnings": list(preview.warnings),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预估失败: {e}")


@router.post("/run")
async def run_search(req: SearchRequest):
    """执行全量搜索并返回 Top-N 结果。"""

    try:
        from games.endfield.calc.search.plan.controller import optimizer_config_for_search_job, prepare_search_job
        from games.endfield.calc.search.run.runner import SearchRunner
        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError:
        raise HTTPException(status_code=500, detail="搜索引擎加载失败，请确认完整项目环境已安装")

    try:
        req, fixed_loadout = _prepare_search_req(req)

        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)

        job, err = prepare_search_job(inputs)

        if err or job is None:
            raise HTTPException(status_code=400, detail=err or "作业组装失败")

        config = optimizer_config_for_search_job(job, top_n=req.top_n)

        result = SearchRunner.run(
            base_context=job.base_context,
            weapons=list(job.weapon_candidates),
            equipment_catalog=dict(job.equipment_catalog),
            config=config,
            max_workers=req.max_workers,
        )

        top_results = []

        for score in result.top_results:
            top_results.append(
                LoadoutResult(
                    weapon_name=score.weapon_name,
                    chest=score.loadout_names.get("chest", ""),
                    gloves=score.loadout_names.get("gloves", ""),
                    accessory_a=score.loadout_names.get("accessory_a", ""),
                    accessory_b=score.loadout_names.get("accessory_b", ""),
                    final_damage=float(score.final_damage),
                    segment_breakdown=dict(score.segment_breakdown) if score.segment_breakdown else None,
                )
            )

        return {
            "top_results": [r.model_dump() for r in top_results],
            "total_combinations": result.total_combinations,
            "searched_combinations": result.processed_combinations,
            "cancelled": result.cancelled,
            "warnings": list(result.warnings) if hasattr(result, "warnings") else [],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


@router.get("/enemies")
def get_enemy_choices():
    """获取敌方参数列表（含插件敌人与全字段默认值）。"""
    from games.endfield.data_loading.enemy_params import (
        enemy_damage_context_overrides,
        list_plugin_enemy_choices,
    )

    rows: list[dict[str, object]] = []
    for label, enemy_id in list_plugin_enemy_choices():
        params = enemy_damage_context_overrides(enemy_id)
        rows.append(
            {
                "id": enemy_id,
                "name": label.split(" (防", 1)[0] if enemy_id else "默认敌人",
                "enemy_defense": float(params["enemy_defense"]),
                "enemy_resistance": float(params["enemy_resistance"]),
                "ignore_resistance": float(params["ignore_resistance"]),
                "imbalance_vulnerability_coeff": float(params["imbalance_vulnerability_coeff"]),
                "is_unbalanced": bool(params["is_unbalanced"]),
                "is_true_damage": bool(params["is_true_damage"]),
                "combo_stacks": int(params["combo_stacks"]),
                "break_defense_stacks": int(params["break_defense_stacks"]),
                "attached_effect_multiplier": float(params["attached_effect_multiplier"]),
                "corrosion_duration_seconds": float(params["corrosion_duration_seconds"]),
                "enemy_tier": str(params["enemy_tier"]),
                "imbalance_efficiency_bonus": float(params["imbalance_efficiency_bonus"]),
            }
        )
    return rows


@router.get("/catalog")
async def get_equipment_catalog(scope: str = "全部装备"):
    """获取装备目录（分部位列表；scope 与 GUI 装备范围文案一致）。"""

    try:
        from games.endfield.data_loading.equipment_catalog import get_equipment_catalog

        catalog = get_equipment_catalog(scope_label=scope)

        return {
            key: [
                {
                    "名称": e.get("名称", ""),
                    "部位": e.get("部位", ""),
                    "所属套组": e.get("所属套组", ""),
                    "稀有度": e.get("稀有度", ""),
                }
                for e in entries
            ]
            for key, entries in catalog.items()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取装备目录失败: {e}")


async def _search_stream_generator(req: SearchRequest) -> AsyncGenerator[str, None]:
    """生成 SSE 事件流：start → heartbeat → summary → chunk(s) → stream_end。"""

    try:
        from games.endfield.calc.search.plan.controller import (
            optimizer_config_for_search_job,
            prepare_search_job,
        )
        from games.endfield.calc.search.run.runner import SearchRunner
        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError:
        yield f"data: {json.dumps({'type': 'error', 'message': '搜索引擎加载失败，请确认完整项目环境已安装'})}\n\n"

        return

    try:
        req, fixed_loadout = _prepare_search_req(req)

        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)

        job, err = prepare_search_job(inputs)

        if err or job is None:
            from web.backend.bridge import get_logger

            if err:
                get_logger(__name__).warning("搜索作业组装失败: %s", err)
            yield f"data: {json.dumps({'type': 'error', 'message': '搜索作业组装失败'})}\n\n"

            return

        config = optimizer_config_for_search_job(job, top_n=req.top_n)

        total_combinations = config.total_combinations if hasattr(config, "total_combinations") else 0

        CHUNK_SIZE = 5

        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

        loop = asyncio.get_event_loop()

        def _run_search():
            try:
                start = time.time()

                result = SearchRunner.run(
                    base_context=job.base_context,
                    weapons=list(job.weapon_candidates),
                    equipment_catalog=dict(job.equipment_catalog),
                    config=config,
                    max_workers=req.max_workers,
                )

                elapsed = time.time() - start

                top_results = []

                for score in result.top_results:
                    top_results.append(
                        {
                            "weapon_name": score.weapon_name,
                            "chest": score.loadout_names.get("chest", ""),
                            "gloves": score.loadout_names.get("gloves", ""),
                            "accessory_a": score.loadout_names.get("accessory_a", ""),
                            "accessory_b": score.loadout_names.get("accessory_b", ""),
                            "final_damage": float(score.final_damage),
                            "segment_breakdown": dict(score.segment_breakdown) if score.segment_breakdown else None,
                        }
                    )

                asyncio.run_coroutine_threadsafe(
                    queue.put(
                        {
                            "type": "done",
                            "top_results": top_results,
                            "total_combinations": result.total_combinations,
                            "searched_combinations": result.processed_combinations,
                            "cancelled": result.cancelled,
                            "elapsed_seconds": round(elapsed, 1),
                        }
                    ),
                    loop,
                )

            except Exception as e:
                asyncio.run_coroutine_threadsafe(
                    queue.put({"type": "error", "message": str(e)}),
                    loop,
                )

        task = asyncio.get_event_loop().run_in_executor(None, _run_search)

        yield f"data: {json.dumps({'type': 'start', 'total_combinations': total_combinations})}\n\n"

        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=1.0)

            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"

                continue

            if msg["type"] == "done":
                results = msg.pop("top_results", [])

                yield f"data: {json.dumps({'type': 'summary', 'total_combinations': msg.get('total_combinations', 0), 'searched_combinations': msg.get('searched_combinations', 0), 'cancelled': msg.get('cancelled', False), 'elapsed_seconds': msg.get('elapsed_seconds', 0)})}\n\n"

                for i in range(0, len(results), CHUNK_SIZE):
                    chunk = results[i : i + CHUNK_SIZE]

                    yield f"data: {json.dumps({'type': 'chunk', 'results': chunk, 'chunk_index': i // CHUNK_SIZE, 'total_chunks': (len(results) + CHUNK_SIZE - 1) // CHUNK_SIZE})}\n\n"

                yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"

                break

            elif msg["type"] == "error":
                from web.backend.bridge import get_logger

                get_logger(__name__).warning("搜索错误: %s", msg.get("message", ""))
                yield f"data: {json.dumps({'type': 'error', 'message': '搜索过程中出现错误，请重试'})}\n\n"
                break

        await task

    except Exception as e:
        from web.backend.bridge import get_logger

        get_logger(__name__).warning("搜索异常: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'message': '搜索异常，请重试'})}\n\n"


@router.post("/run_stream")
async def run_search_stream(req: SearchRequest):
    """流式全量搜索 — 通过 SSE 逐步返回进度与结果。"""

    return StreamingResponse(
        _search_stream_generator(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# 搜索历史（文件持久化，最近 10 次）
from api.persistent_store import load_list, save_list

_SEARCH_STORE_KEY = "search_history"
_search_history: list[dict] = load_list(_SEARCH_STORE_KEY)


def list_search_history():
    """获取搜索历史列表。"""
    return list(reversed(_search_history))


def save_search_history(entry: dict):
    """保存一次搜索记录。"""
    global _search_history
    _search_history.append(entry)
    while len(_search_history) > 10:
        _search_history.pop(0)
    save_list(_SEARCH_STORE_KEY, _search_history)
    return {"message": "ok"}


@router.get("/history")
def list_search_history_route():
    """获取搜索历史列表。"""
    return list_search_history()


@router.post("/history")
def save_search_history_route(entry: dict):
    """保存一次搜索记录。"""
    return save_search_history(entry)


__all__: list[str] = []
