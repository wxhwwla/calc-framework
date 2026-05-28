import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "framework" / "src"))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from calc_framework.config.manager import AdapterManager

router = APIRouter(prefix="/api/adapters", tags=["adapters"])

ADAPTER_ROOT = Path(__file__).resolve().parents[3] / "framework" / "adapters"
_manager = AdapterManager(ADAPTER_ROOT)


class AdapterInfo(BaseModel):
    name: str
    game: str
    version: str
    description: str


class AdapterAttr(BaseModel):
    name: str
    type: str
    source: str
    default: float | bool | None = None
    description: str = ""


class AdapterSchema(BaseModel):
    attributes: list[AdapterAttr]


@router.get("", response_model=list[AdapterInfo])
async def list_adapters():
    results: list[AdapterInfo] = []
    for path in Path(ADAPTER_ROOT).iterdir():
        meta_file = path / "meta.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        results.append(
            AdapterInfo(
                name=meta.get("name", path.name),
                game=meta.get("game", ""),
                version=meta.get("version", ""),
                description=meta.get("description", ""),
            )
        )
    return results


@router.get("/{name}/schema", response_model=AdapterSchema)
async def get_schema(name: str):
    try:
        pkg = _manager.load(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if pkg.attr_schema is None:
        return AdapterSchema(attributes=[])

    return AdapterSchema(
        attributes=[AdapterAttr(**a.to_dict()) for a in pkg.attr_schema.attributes]
    )
