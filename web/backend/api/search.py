# SPDX-License-Identifier: AGPL-3.0
import json

import asyncio

import time

from typing import Any, AsyncGenerator


from fastapi import APIRouter, HTTPException

from fastapi.responses import StreamingResponse

from pydantic import BaseModel



router = APIRouter(prefix="/api/search", tags=["search"])





class SearchRequest(BaseModel):

    char_data: dict[str, Any]

    char_level: int = 90

    weapon_level: int = 90

    trust_level: int = 12

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

    top_n: int = 10

    max_workers: int = 4

    use_manual_multi_skill_counts: bool = False

    manual_counts: dict[str, int] | None = None

    skill_1_level: int = 0

    skill_2_level: int = 0

    skill_3_level: int = 0

    use_expected_crit: bool = False

    extra_crit_rate: float = 0.0

    extra_crit_damage: float = 0.0





class EstimateRequest(BaseModel):

    char_data: dict[str, Any]

    char_level: int = 90

    weapon_level: int = 90

    trust_level: int = 12

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

        from calc_framework.config.adapter import AdapterPackage



        from games.endfield.calc.loadout.optimizer import optimizer_config_for_character

        from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection

        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

        from games.endfield.calc.search.plan.controller import prepare_search_job

        from games.endfield.calc.search.plan.estimate import (

            preview_search_workload,

            estimate_search_duration,

        )

        from games.endfield.calc.loadout.attack_eval import final_attack_details_for_loadout

    except ImportError as e:

        raise HTTPException(status_code=500, detail=f"导入搜索引擎失败: {e}")



    try:

        fixed_loadout = FixedLoadoutSelection(**req.fixed_loadout) if req.fixed_loadout else FixedLoadoutSelection()



        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)



        job, err = prepare_search_job(inputs)

        if err or job is None:

            return {"total_combinations": 0, "estimated_seconds": 0, "warning": err or "作业组装失败"}



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

        from games.endfield.calc.search.run.runner import SearchRunner

        from games.endfield.calc.search.plan.controller import prepare_search_job, optimizer_config_for_search_job

        from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection

        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError as e:

        raise HTTPException(status_code=500, detail=f"导入搜索引擎失败: {e}")



    try:

        fixed_loadout = FixedLoadoutSelection(**req.fixed_loadout) if req.fixed_loadout else FixedLoadoutSelection()



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

            top_results.append(LoadoutResult(

                weapon_name=score.weapon_name,

                chest=score.loadout_names.get("chest", ""),

                gloves=score.loadout_names.get("gloves", ""),

                accessory_a=score.loadout_names.get("accessory_a", ""),

                accessory_b=score.loadout_names.get("accessory_b", ""),

                final_damage=float(score.final_damage),

                segment_breakdown=dict(score.segment_breakdown) if score.segment_breakdown else None,

            ))



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
    """获取敌方参数列表（含插件敌人与全字段默认）。"""
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

async def get_equipment_catalog():

    """获取装备目录（分部位列表）。"""

    try:

        from games.endfield.data_loading.equipment_catalog import get_equipment_catalog

        catalog = get_equipment_catalog()

        return {

            key: [{"名称": e.get("名称", ""), "部位": e.get("部位", ""), "所属套组": e.get("所属套组", ""), "稀有度": e.get("稀有度", "")} for e in entries]

            for key, entries in catalog.items()

        }

    except Exception as e:

        raise HTTPException(status_code=500, detail=f"获取装备目录失败: {e}")





async def _search_stream_generator(req: SearchRequest) -> AsyncGenerator[str, None]:

    """生成 SSE 事件流：progress → chunks → done。"""

    try:

        from games.endfield.calc.search.run.runner import SearchRunner

        from games.endfield.calc.search.plan.controller import (

            prepare_search_job,

            optimizer_config_for_search_job,

        )

        from games.endfield.calc.loadout.slot_search import FixedLoadoutSelection

        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError as e:

        yield f"data: {json.dumps({'type': 'error', 'message': f'导入搜索引擎失败: {e}'})}\n\n"

        return



    try:

        fixed_loadout = FixedLoadoutSelection(**req.fixed_loadout) if req.fixed_loadout else FixedLoadoutSelection()

        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)



        job, err = prepare_search_job(inputs)

        if err or job is None:

            yield f"data: {json.dumps({'type': 'error', 'message': err or '作业组装失败'})}\n\n"

            return



        config = optimizer_config_for_search_job(job, top_n=req.top_n)

        total_combinations = config.total_combinations if hasattr(config, 'total_combinations') else 0



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

                    top_results.append({

                        "weapon_name": score.weapon_name,

                        "chest": score.loadout_names.get("chest", ""),

                        "gloves": score.loadout_names.get("gloves", ""),

                        "accessory_a": score.loadout_names.get("accessory_a", ""),

                        "accessory_b": score.loadout_names.get("accessory_b", ""),

                        "final_damage": float(score.final_damage),

                        "segment_breakdown": dict(score.segment_breakdown) if score.segment_breakdown else None,

                    })



                asyncio.run_coroutine_threadsafe(

                    queue.put({

                        "type": "done",

                        "top_results": top_results,

                        "total_combinations": result.total_combinations,

                        "searched_combinations": result.processed_combinations,

                        "cancelled": result.cancelled,

                        "elapsed_seconds": round(elapsed, 1),

                    }),

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

                    chunk = results[i:i + CHUNK_SIZE]

                    yield f"data: {json.dumps({'type': 'chunk', 'results': chunk, 'chunk_index': i // CHUNK_SIZE, 'total_chunks': (len(results) + CHUNK_SIZE - 1) // CHUNK_SIZE})}\n\n"



                yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"

                break



            elif msg["type"] == "error":

                yield f"data: {json.dumps({'type': 'error', 'message': msg['message']})}\n\n"

                break



        await task



    except Exception as e:

        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"





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


# 搜索历史（内存 Ring Buffer，最近 10 次）
_search_history: list[dict] = []


@router.get("/history")
def list_search_history():
    """获取搜索历史列表。"""
    return list(reversed(_search_history))


@router.post("/history")
def save_search_history(entry: dict):
    """保存一次搜索记录。"""
    _search_history.append(entry)
    while len(_search_history) > 10:
        _search_history.pop(0)
    return {"message": "ok"}

