# SPDX-License-Identifier: AGPL-3.0
"""Web 多段逆推 payload — SegmentCurveEngine / AK 里程碑 / 终末地兼容层。"""

from __future__ import annotations

from typing import Any

from calc_framework.inverse.curve import GROWTH_PARAM_SEGMENTS_KEY, CurveBlueprint, SegmentCurveEngine
from fastapi import HTTPException

from games.endfield.calc.damage.formula import calculate_growth_curve, calculate_skill_curve
from games.endfield.calc.damage.inverse.adapter import EndfieldInverseAdapter
from games.endfield.calc.damage.inverse.blueprints import (
    ENDFIELD_ATTRIBUTE_BLUEPRINT,
    ENDFIELD_SKILL_9_BLUEPRINT,
    ENDFIELD_SKILL_12_BLUEPRINT,
)

DEFAULT_MAX_ERROR = 0.05


def _formula_text(params: dict[str, Any]) -> str:
    growth = params.get("growth", 0)
    divisor = params.get("divisor", 1)
    offset = params.get("offset", 0)
    return f"base + floor(({growth} * (lv - 1) + {offset}) / {divisor})"


def _special_from_params(params: dict[str, Any]) -> list[float] | None:
    raw = params.get("special_values")
    if not isinstance(raw, list) or not raw:
        return None
    return [float(x) for x in raw]


def fit_result_to_inverse_response(
    result: Any,
    *,
    max_error: float = DEFAULT_MAX_ERROR,
    original: list[float] | None = None,
) -> dict[str, Any]:
    """将 ``FitResult`` 转为 Designer 兼容的逆推响应 dict。"""
    params = dict(result.params or {})
    special = _special_from_params(params)
    valid = bool(params) and float(result.max_error) <= max_error
    details = result.summary()
    if original and params:
        base = int(params.get("base", 0))
        growth = int(params.get("growth", 0))
        divisor = int(params.get("divisor", 1))
        offset = int(params.get("offset", 0))
        if len(original) == 90:
            preview = calculate_growth_curve(base, growth, divisor, offset)[:10]
        elif len(original) in (9, 12):
            preview = calculate_skill_curve(
                base=float(base),
                growth=float(growth),
                divisor=divisor,
                offset=offset,
                special_values=special,
            )[:10]
        else:
            preview = result.computed[:10] if result.computed else []
        if preview:
            preview_text = ", ".join(str(x) for x in preview)
            details = f"{details}\n生成曲线（前10级）: {preview_text}…"
    return {
        "base": float(params.get("base", 0)),
        "growth": float(params.get("growth", 0)),
        "divisor": int(params.get("divisor", 1)),
        "offset": float(params.get("offset", 0)),
        "special": special,
        "formula": _formula_text(params) if params else "",
        "valid": valid,
        "max_error": float(result.max_error),
        "details": details,
        "params": params,
    }


def resolve_blueprint(game: str, blueprint_id: str, *, rarity: int = 6) -> CurveBlueprint:
    """按游戏与 blueprint_id 解析 ``CurveBlueprint``。"""
    game_key = game.strip().lower()
    bp_id = blueprint_id.strip().lower()
    if game_key == "endfield":
        mapping: dict[str, CurveBlueprint] = {
            "attr_90": ENDFIELD_ATTRIBUTE_BLUEPRINT,
            "skill_12": ENDFIELD_SKILL_12_BLUEPRINT,
            "skill_9": ENDFIELD_SKILL_9_BLUEPRINT,
        }
        bp = mapping.get(bp_id)
        if bp is not None:
            return bp
        raise HTTPException(status_code=400, detail=f"未知终末地 blueprint_id: {blueprint_id}")
    if game_key == "arknights":
        from games.arknights.calc.inverse.adapter import SKILL_SP_BLUEPRINT, blueprint_for_rarity

        if bp_id in ("attributes", "attr"):
            return blueprint_for_rarity(int(rarity))
        if bp_id in ("skill_sp", "sp"):
            return SKILL_SP_BLUEPRINT
        raise HTTPException(status_code=400, detail=f"未知明日方舟 blueprint_id: {blueprint_id}")
    raise HTTPException(status_code=400, detail=f"不支持的游戏: {game}")


def inverse_segment_payload(
    *,
    game: str,
    blueprint_id: str,
    segment_key: str,
    values: list[float],
    rarity: int = 6,
    max_error: float = DEFAULT_MAX_ERROR,
) -> dict[str, Any]:
    """按 blueprint 段 key 拟合单段曲线。"""
    blueprint = resolve_blueprint(game, blueprint_id, rarity=rarity)
    seg_key = segment_key.strip()
    spec = blueprint.get(seg_key)
    if spec is None:
        keys = ", ".join(blueprint.keys())
        raise HTTPException(
            status_code=400,
            detail=f"段 key '{segment_key}' 不在 blueprint '{blueprint_id}' 中（可选: {keys}）",
        )
    data = [float(x) for x in values]
    if len(data) != spec.length:
        raise HTTPException(
            status_code=400,
            detail=f"段 '{seg_key}' 需要 {spec.length} 个值，当前 {len(data)} 个",
        )
    engine = SegmentCurveEngine()
    try:
        result = engine.fit_segment(data, spec)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    out = fit_result_to_inverse_response(result, max_error=max_error, original=data)
    out.update(
        {
            "game": game.strip().lower(),
            "blueprint_id": blueprint_id.strip().lower(),
            "segment_key": seg_key,
            "length": spec.length,
        }
    )
    return out


def inverse_milestones_payload(
    operator: dict[str, Any],
    *,
    max_error: float = DEFAULT_MAX_ERROR,
) -> dict[str, Any]:
    """从干员 ``属性里程碑`` 批量反推 ``成长参数``。"""
    from games.arknights.calc.inverse.milestones import fit_operator_growth_params

    if not isinstance(operator, dict):
        raise HTTPException(status_code=400, detail="operator 须为 object")
    growth = fit_operator_growth_params(operator, max_error=max_error)
    errors = list(growth.pop("_errors", []) or [])
    segments = growth.get(GROWTH_PARAM_SEGMENTS_KEY) or []
    return {
        "growth_params": growth,
        "errors": errors,
        "segment_count": len(segments),
        "skill_sp_count": len(growth.get("技能SP") or {}),
    }


def inverse_formula_payload(
    type_: str,
    values: list[float],
    *,
    max_error: float = DEFAULT_MAX_ERROR,
) -> dict[str, Any]:
    """终末地 legacy 反推（``attribute`` / ``skill``）— 内部走 ``EndfieldInverseAdapter``。"""
    try:
        adapter = EndfieldInverseAdapter()
    except ImportError as exc:
        raise HTTPException(status_code=500, detail=f"逆推引擎导入失败: {exc}") from exc

    data = [float(x) for x in values]
    if type_ == "attribute":
        if len(data) == 94:
            result = adapter.fit_from_94(data)
            check_len = 90
        elif len(data) == 90:
            result = adapter.fit_attribute_90(data)
            check_len = 90
        else:
            raise HTTPException(status_code=400, detail=f"属性数据需要90或94个值，当前{len(data)}个")
        return fit_result_to_inverse_response(result, max_error=max_error, original=data[:check_len])

    if type_ == "skill":
        if len(data) >= 12:
            result = adapter.fit_skill_12(data[:12])
            original = data[:12]
        elif len(data) >= 9:
            result = adapter.fit_skill_9(data[:9])
            original = data[:9]
        else:
            raise HTTPException(status_code=400, detail=f"技能数据需要9或12个值，当前{len(data)}个")
        return fit_result_to_inverse_response(result, max_error=max_error, original=original)

    raise HTTPException(status_code=400, detail=f"不支持的逆推类型: {type_}")
