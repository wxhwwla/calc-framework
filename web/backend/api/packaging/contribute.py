# SPDX-License-Identifier: AGPL-3.0
"""数据贡献 API — 校验和暂存用户提交的 EntitySchema 数据。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from api.internal.safe_paths import build_contribute_filename, write_json_to_staging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/contribute", tags=["contribute"])

STAGING_DIR = Path(__file__).resolve().parent / ".staging"


def _ensure_staging_dir() -> Path:
    """确保暂存目录存在并返回路径。"""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    return STAGING_DIR


class ValidateRequest(BaseModel):
    """前端提交的校验请求。"""

    pass


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str]


class SubmitResponse(BaseModel):
    message: str
    filename: str


def _validate_entity(entity: dict[str, Any]) -> list[str]:
    """校验 EntitySchema 格式。"""
    errors: list[str] = []
    name = entity.get("名称", "")
    if not name or not isinstance(name, str):
        errors.append("缺少必填字段 '名称'")
    elif not name.strip():
        errors.append("'名称' 不能为空")

    star = entity.get("星级")
    if star is not None:
        if not isinstance(star, int) or star < 3 or star > 6:
            errors.append(f"'星级' 须为 3~6 的整数, 实际 {star}")

    skills = entity.get("技能", [])
    if not isinstance(skills, list):
        errors.append("'技能' 须为数组")
        return errors

    if len(skills) == 0:
        errors.append("'技能' 列表不能为空")

    for i, skill in enumerate(skills):
        _validate_skill(skill, name or f"技能[{i}]", i, errors)

    return errors


def _validate_skill(skill: dict[str, Any], entity_name: str, index: int, errors: list[str]) -> None:
    prefix = f"'{entity_name}'.技能[{index}]"
    sname = skill.get("名称", "")
    if not sname or not isinstance(sname, str):
        errors.append(f"{prefix}: 缺少 '名称'")
        sname = f"技能[{index}]"

    label = skill.get("标签", "")
    if label not in ("主动", "被动"):
        errors.append(f"{prefix}.名称='{sname}': '标签' 须为 '主动' 或 '被动', 实际 '{label}'")

    if "百分比" not in skill:
        errors.append(f"{prefix}.名称='{sname}': 缺少 '百分比'")
    elif not isinstance(skill["百分比"], bool):
        errors.append(f"{prefix}.名称='{sname}': '百分比' 须为布尔值")

    segments = skill.get("段", [])
    if not isinstance(segments, list):
        errors.append(f"{prefix}.名称='{sname}': '段' 须为数组")
        return

    if len(segments) == 0:
        errors.append(f"{prefix}.名称='{sname}': '段' 列表不能为空")

    for j, seg in enumerate(segments):
        _validate_segment(seg, entity_name, sname, j, errors)


def _validate_segment(
    seg: dict[str, Any],
    entity_name: str,
    skill_name: str,
    index: int,
    errors: list[str],
) -> None:
    prefix = f"'{entity_name}'.技能'{skill_name}'.段[{index}]"
    rates = seg.get("倍率", [])
    if not rates or not isinstance(rates, list):
        errors.append(f"{prefix}: '倍率' 须为非空数组")
    else:
        for v in rates:
            if not isinstance(v, int):
                errors.append(f"{prefix}: 倍率值须为整数, 实际 {type(v).__name__} ({v})")

    dtype = seg.get("伤害类型")
    if dtype is not None and not isinstance(dtype, str):
        errors.append(f"{prefix}: '伤害类型' 须为字符串")


@router.post("/validate", response_model=ValidateResponse)
async def validate_contribute(payload: dict[str, Any]):
    """校验提交的数据是否符合 EntitySchema 格式。"""
    errors = _validate_entity(payload)
    return ValidateResponse(valid=len(errors) == 0, errors=errors)


@router.post("/submit", response_model=SubmitResponse)
async def submit_contribute(payload: dict[str, Any]):
    """将用户提交的数据暂存到服务器。"""
    errors = _validate_entity(payload)
    if errors:
        raise HTTPException(
            status_code=400,
            detail=f"数据校验失败: {'; '.join(errors)}",
        )

    name = payload.get("名称", "unknown")
    filename = build_contribute_filename(str(name))

    staging = _ensure_staging_dir()
    meta = {
        "_meta": {
            "submitted_at": datetime.now().isoformat(),
            "source": "web_contribute",
        }
    }
    record = {**meta, **payload}
    write_json_to_staging(staging, filename, record)

    return SubmitResponse(
        message="提交成功",
        filename=filename,
    )


__all__: list[str] = []
