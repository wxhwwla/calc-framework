# SPDX-License-Identifier: AGPL-3.0
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from calc_framework.config.manager import AdapterManager

router = APIRouter(prefix="/api/adapters", tags=["adapters"])

ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters"
_manager = AdapterManager(ADAPTER_ROOT)


class AdapterInfoResponse(BaseModel):
    name: str
    game: str
    version: str
    description: str


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
                name=meta.get("name", path.name),
                game=meta.get("game", ""),
                version=meta.get("version", ""),
                description=meta.get("description", ""),
            )
        )
    return results


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
