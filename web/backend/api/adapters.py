# SPDX-License-Identifier: AGPL-3.0
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calc_framework.config.manager import AdapterManager

from api.adapter_assets import (
    data_entity_summary,
    get_adapter_dag,
    get_adapter_layout,
    get_data_files_for_export,
    get_pack_export_bundle,
)

router = APIRouter(prefix="/api/adapters", tags=["adapters"])

ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters"
_manager = AdapterManager(ADAPTER_ROOT)


class AdapterInfoResponse(BaseModel):
    id: str
    name: str
    game: str
    version: str
    description: str


class AdapterMetaResponse(BaseModel):
    id: str
    meta: dict


class AdapterAttrResponse(BaseModel):
    name: str
    type: str
    source: str
    default: float | bool | None = None
    description: str = ""


class AdapterSchemaResponse(BaseModel):
    attributes: list[AdapterAttrResponse]


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
    return {"entities": data_entity_summary(adapter_id)}


@router.get("/{adapter_id}/pack-bundle")
async def get_adapter_pack_bundle(adapter_id: str):
    return get_pack_export_bundle(adapter_id)


@router.get("/{name}/schema", response_model=AdapterSchemaResponse)
async def get_schema(name: str):
    try:
        pkg = _manager.load(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if pkg.attr_schema is None:
        return AdapterSchemaResponse(attributes=[])

    return AdapterSchemaResponse(
        attributes=[AdapterAttrResponse(**a.to_dict()) for a in pkg.attr_schema.attributes]
    )
