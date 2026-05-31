# SPDX-License-Identifier: AGPL-3.0
"""Calc Hub 在线市场 API。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from hub.storage import (
    create_pack,
    delete_pack,
    get_pack,
    get_pack_file_path,
    increment_download,
    list_packs,
    rate_pack,
    save_pack_file,
    update_pack,
)

router = APIRouter(prefix="/api/hub", tags=["hub"])


class PackCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=20)
    description: str = Field(default="", max_length=2000)
    author: str = Field(default="", max_length=100)
    tags: list[str] = Field(default_factory=list)


class PackUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    version: str | None = Field(default=None, min_length=1, max_length=20)
    description: str | None = Field(default=None, max_length=2000)
    author: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = None


class RateRequest(BaseModel):
    score: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=500)


class PackListResponse(BaseModel):
    packs: list[dict[str, Any]]
    total: int
    offset: int
    limit: int


@router.get("/packs", response_model=PackListResponse)
async def list_packs_endpoint(
    search: str = Query(default="", max_length=100),
    tag: str = Query(default="", max_length=50),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc", pattern="^(asc|desc)$"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
):
    packs, total = list_packs(
        search=search, tag=tag, sort=sort, order=order,
        offset=offset, limit=limit,
    )
    return PackListResponse(packs=packs, total=total, offset=offset, limit=limit)


@router.get("/packs/{pack_id}")
async def get_pack_endpoint(pack_id: str):
    pack = get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="包不存在")
    return pack


@router.post("/packs", status_code=201)
async def create_pack_endpoint(pack: PackCreate):
    result = create_pack(
        name=pack.name,
        version=pack.version,
        description=pack.description,
        author=pack.author,
        tags=pack.tags,
    )
    return {
        "id": result.id,
        "name": result.name,
        "version": result.version,
        "message": "上传成功",
    }


@router.put("/packs/{pack_id}")
async def update_pack_endpoint(pack_id: str, update: PackUpdate):
    kwargs = {k: v for k, v in update.model_dump().items() if v is not None}
    result = update_pack(pack_id, **kwargs)
    if result is None:
        raise HTTPException(status_code=404, detail="包不存在")
    return result


@router.delete("/packs/{pack_id}", status_code=204)
async def delete_pack_endpoint(pack_id: str):
    if not delete_pack(pack_id):
        raise HTTPException(status_code=404, detail="包不存在")


@router.post("/packs/{pack_id}/upload")
async def upload_pack_file(pack_id: str, file: UploadFile):
    pack = get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="包不存在")
    content = await file.read()
    filename = file.filename or f"{pack_id}.calcpack"
    saved = save_pack_file(pack_id, content, filename)
    update_pack(pack_id, file_size=saved.stat().st_size)
    return {"filename": filename, "size": saved.stat().st_size}


@router.get("/packs/{pack_id}/download/{filename}")
async def download_pack_file(pack_id: str, filename: str):
    pack = get_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="包不存在")
    file_path = get_pack_file_path(pack_id, filename)
    if file_path is None:
        raise HTTPException(status_code=404, detail="文件不存在")
    increment_download(pack_id)
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@router.post("/packs/{pack_id}/rate")
async def rate_pack_endpoint(pack_id: str, rate: RateRequest):
    result = rate_pack(pack_id, score=rate.score, comment=rate.comment)
    if result is None:
        raise HTTPException(status_code=404, detail="包不存在")
    return {"rating": result["rating"], "rating_count": result["rating_count"]}


@router.get("/stats")
async def hub_stats():
    packs, total = list_packs(limit=0)
    return {
        "total_packs": total,
        "db_path": str(Path(__file__).resolve().parent.parent / "data" / "hub" / "catalog.db"),
    }
