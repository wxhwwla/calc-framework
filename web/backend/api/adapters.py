# SPDX-License-Identifier: AGPL-3.0
"""适配器元数据 API — 列表/元信息/layout/DAG/数据摘要/打包导出。"""

import json
from pathlib import Path

from api.adapter_lib.assets import (
    data_entity_summary,
    get_adapter_dag,
    get_adapter_layout,
    get_pack_export_bundle,
)
from api.internal.json_utils import ADAPTER_ROOT
from calc_framework.config.manager import AdapterManager
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/adapters", tags=["adapters"])

_manager = AdapterManager(ADAPTER_ROOT)


class AdapterInfoResponse(BaseModel):
    """适配器摘要信息。"""

    id: str = Field(description="适配器目录名")
    name: str = Field(description="适配器显示名")
    game: str = Field(description="关联游戏")
    version: str = Field(description="版本号")
    description: str = Field(description="描述")


class AdapterMetaResponse(BaseModel):
    """适配器完整元数据。"""

    id: str = Field(description="适配器目录名")
    meta: dict = Field(description="meta.json 完整内容")


class AdapterAttrResponse(BaseModel):
    """属性定义。"""

    name: str = Field(description="属性名")
    type: str = Field(description="属性类型（float/bool/select 等）")
    source: str = Field(description="数据来源键")
    default: float | bool | None = Field(default=None, description="默认值")
    description: str = Field(default="", description="描述")


class AdapterSchemaResponse(BaseModel):
    """属性 schema 列表。"""

    attributes: list[AdapterAttrResponse] = Field(description="属性定义列表")


@router.get("", response_model=list[AdapterInfoResponse])
async def list_adapters():
    results: list[AdapterInfoResponse] = []
    for path in Path(ADAPTER_ROOT).iterdir():
        meta_file = path / "meta.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        results.append(
            AdapterInfoResponse(
                id=path.name,
                name=meta.get("name", path.name),
                game=meta.get("game", ""),
                version=meta.get("version", ""),
                description=meta.get("description", ""),
            )
        )
    return results


@router.get("/{adapter_id}/meta", response_model=AdapterMetaResponse)
async def get_adapter_meta(adapter_id: str):
    meta_file = ADAPTER_ROOT / adapter_id / "meta.json"
    if not meta_file.is_file():
        raise HTTPException(status_code=404, detail=f"adapter not found: {adapter_id}")
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    return AdapterMetaResponse(id=adapter_id, meta=meta)


@router.get("/{adapter_id}/layout")
async def get_adapter_layout_route(adapter_id: str):
    return get_adapter_layout(adapter_id)


@router.get("/{adapter_id}/dag")
async def get_adapter_dag_route(adapter_id: str):
    return get_adapter_dag(adapter_id)


@router.get("/{adapter_id}/data-summary")
async def get_adapter_data_summary(adapter_id: str):
    """获取适配器关联的游戏数据实体摘要（类型 / 条数 / 只读）。"""
    return {"entities": data_entity_summary(adapter_id)}


@router.get("/{adapter_id}/pack-bundle")
async def get_adapter_pack_bundle(adapter_id: str):
    """获取适配器的完整打包导出内容（meta + layout + DAG + data_files）。"""
    return get_pack_export_bundle(adapter_id)


@router.get("/{name}/schema", response_model=AdapterSchemaResponse)
async def get_schema(name: str):
    try:
        pkg = _manager.load(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if pkg.attr_schema is None:
        return AdapterSchemaResponse(attributes=[])

    return AdapterSchemaResponse(attributes=[AdapterAttrResponse(**a.to_dict()) for a in pkg.attr_schema.attributes])


__all__: list[str] = []
