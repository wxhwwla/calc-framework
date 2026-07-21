# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""配装搜索 API — 工作量预估/全量搜索/SSE 流式搜索/敌人数值/装备目录/搜索历史。"""

import asyncio
import json
import threading
import time
from collections.abc import AsyncGenerator
from typing import Any

from api.internal.errors import raise_http_from_exc
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

router = APIRouter(prefix="/api/search", tags=["search"])

_MAX_JSON_DEPTH = 10
_MAX_HISTORY_ENTRY_BYTES = 1024 * 100  # 100KB 单条上限


def _check_depth(value: object, depth: int = 0) -> None:
    """递归检查 JSON 嵌套深度，超过 ``_MAX_JSON_DEPTH`` 时抛 ValueError。

    防止攻击者通过深度嵌套的 JSON payload 导致 Pydantic 解析栈溢出。
    """
    if depth > _MAX_JSON_DEPTH:
        raise ValueError(f"JSON 嵌套深度超过限制 ({_MAX_JSON_DEPTH})")
    if isinstance(value, dict):
        for v in value.values():
            _check_depth(v, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _check_depth(item, depth + 1)


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
    all_weapons: list[dict[str, Any]] | None = Field(
        default=None,
        description="武器候选列表（省略时服务端按 scope 从 catalog 加载）",
    )
    weapon_candidate_names: list[str] | None = Field(
        default=None,
        description="可选武器名称白名单（在 scope 过滤后再约束）",
    )
    current_weapon: dict[str, Any] = Field(description="当前选定武器")
    equipment_catalog: dict[str, list[dict[str, Any]]] | None = Field(
        default=None,
        description="装备目录（省略时服务端按 equipment_scope_label 加载）",
    )
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

    @model_validator(mode="before")
    @classmethod
    def _limit_json_depth(cls, data: object) -> object:
        """限制 JSON 嵌套深度，防止栈溢出/内存耗尽。"""
        _check_depth(data)
        return data


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

    all_weapons: list[dict[str, Any]] | None = None

    weapon_candidate_names: list[str] | None = None

    current_weapon: dict[str, Any]

    equipment_catalog: dict[str, list[dict[str, Any]]] | None = None

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

    include_catalog: bool = Field(
        default=False,
        description="为浏览器本地 TopN 搜索返回武器列表与完整装备目录",
    )

    max_workers: int = Field(default=4, description="并行线程数（仅用于耗时预估）")


def _prepare_search_req(req: SearchRequest | EstimateRequest) -> tuple[Any, Any]:
    """归一化技能字段、实体引用与 catalog（与 GUI 桌面端保持一致）。"""
    from api.search_lib.catalog import resolve_equipment_catalog, weapon_rows_for_search
    from api.search_lib.entity_refs import resolve_character_ref, resolve_weapon_ref

    from games.endfield.data_loading.web_search_bridge import (
        enrich_search_request_fields,
        resolve_search_fixed_loadout,
    )

    char_data = resolve_character_ref(
        req.char_data,
        char_level=int(req.char_level),
        trust_level=int(req.trust_level),
    )
    current_weapon = resolve_weapon_ref(req.current_weapon, weapon_level=int(req.weapon_level))
    all_weapons = weapon_rows_for_search(
        req.all_weapons,
        char_data=char_data,
        current_weapon=current_weapon,
        weapon_scope_label=str(req.weapon_scope_label),
        char_level=int(req.char_level),
        weapon_level=int(req.weapon_level),
        trust_level=int(req.trust_level),
        weapon_candidate_names=getattr(req, "weapon_candidate_names", None),
    )
    equipment_catalog = resolve_equipment_catalog(
        req.equipment_catalog,
        equipment_scope_label=str(req.equipment_scope_label),
    )
    normalized = req.model_copy(
        update={
            "char_data": char_data,
            "current_weapon": current_weapon,
            "all_weapons": all_weapons,
            "equipment_catalog": equipment_catalog,
        }
    )
    enriched = normalized.model_copy(update=enrich_search_request_fields(normalized))
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


class LoadoutComboItem(BaseModel):
    """单条配装组合（score-batch 用）。"""

    weapon_name: str
    chest: str = ""
    gloves: str = ""
    accessory_a: str = ""
    accessory_b: str = ""


class ScoreBatchRequest(BaseModel):
    """浏览器本地搜索 — 批量服务端评分（异常 parity）。"""

    params: SearchRequest
    loadouts: list[LoadoutComboItem] = Field(min_length=1, max_length=256)


@router.post("/score-batch")
async def score_search_batch(body: ScoreBatchRequest):
    """对多条配装返回与桌面全量搜索一致的 final_damage（含异常 compose）。"""

    try:
        from games.endfield.calc.search.evaluate.batch_score import score_search_loadouts_batch
        from games.endfield.calc.search.plan.controller import optimizer_config_for_search_job, prepare_search_job
        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError:
        raise HTTPException(status_code=503, detail="搜索引擎加载失败，请确认完整项目环境已安装")

    try:
        req, fixed_loadout = _prepare_search_req(body.params)
        inputs = build_search_job_inputs_from_request(req, fixed_loadout=fixed_loadout)
        job, err = prepare_search_job(inputs)
        if err or job is None:
            raise HTTPException(status_code=400, detail=err or "作业组装失败")
        config = optimizer_config_for_search_job(job, top_n=10)
        scores = score_search_loadouts_batch(
            job=job,
            loadouts=[item.model_dump() for item in body.loadouts],
            crit_mode=config.crit_mode,
        )
        return {"final_damage": scores}
    except HTTPException:
        raise
    except Exception as e:
        raise_http_from_exc(e, status_code=500, public_message="批量评分失败")


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
        raise HTTPException(status_code=503, detail="搜索引擎加载失败，请确认完整项目环境已安装")

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

        payload: dict[str, Any] = {
            "total_combinations": preview.total_combinations,
            "weapon_count": preview.weapon_count,
            "loadout_combinations": preview.loadout_combinations,
            "estimated_seconds": duration.estimated_seconds,
            "warnings": list(preview.warnings),
        }
        if getattr(req, "include_catalog", False):
            payload["weapons"] = list(req.all_weapons or [])
            payload["equipment_catalog"] = dict(req.equipment_catalog or {})
        return payload

    except Exception as e:
        raise_http_from_exc(e, status_code=500, public_message="预估失败")


@router.post("/run")
async def run_search(req: SearchRequest):
    """执行全量搜索并返回 Top-N 结果。"""

    try:
        from games.endfield.calc.search.plan.controller import optimizer_config_for_search_job, prepare_search_job
        from games.endfield.calc.search.run.runner import SearchRunner
        from games.endfield.data_loading.enemy_eval_params import build_search_job_inputs_from_request

    except ImportError:
        raise HTTPException(status_code=503, detail="搜索引擎加载失败，请确认完整项目环境已安装")

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
        raise_http_from_exc(e, status_code=500, public_message="搜索失败")


@router.get("/enemies")
def get_enemy_choices():
    """获取敌方参数列表（含插件敌人与全字段默认值）。"""
    from games.endfield.data_loading.enemy_params import (
        enemy_damage_context_overrides,
        list_plugin_enemy_choices,
    )

    rows: list[dict[str, Any]] = []
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
        raise_http_from_exc(e, status_code=500, public_message="获取装备目录失败")


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
                from web.backend.bridge import get_logger

                get_logger(__name__).warning("搜索执行异常: %s", e, exc_info=True)
                asyncio.run_coroutine_threadsafe(
                    queue.put({"type": "error", "message": "搜索过程中出现错误，请重试"}),
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
from api.internal.persistent_store import load_list, save_list

_SEARCH_STORE_KEY = "search_history"
_search_history: list[dict] = load_list(_SEARCH_STORE_KEY)
_search_history_lock = threading.Lock()


def list_search_history():
    """获取搜索历史列表。"""
    return list(reversed(_search_history))


def _validate_history_entry(entry: object) -> dict:
    """校验搜索历史记录条目的基本合法性。"""
    if not isinstance(entry, dict):
        raise HTTPException(status_code=400, detail="历史记录必须是一个 JSON 对象")
    raw = json.dumps(entry, ensure_ascii=False)
    if len(raw.encode("utf-8")) > _MAX_HISTORY_ENTRY_BYTES:
        raise HTTPException(status_code=413, detail=f"单条历史记录不能超过 {_MAX_HISTORY_ENTRY_BYTES // 1024}KB")
    return dict(entry)


def save_search_history(entry: dict):
    """保存一次搜索记录。"""
    global _search_history
    with _search_history_lock:
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
    validated = _validate_history_entry(entry)
    return save_search_history(validated)


__all__: list[str] = []
