# SPDX-License-Identifier: AGPL-3.0
"""配置包设计器 API — 主题管理 + .calcpack 导出。"""

import base64
import io
import json
import zipfile
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/pack", tags=["pack"])


DEFAULT_THEME = {
    "schema_version": "theme-v1",
    "name": "默认深色",
    "font": {"family": "Microsoft YaHei", "size": 12, "weight": "normal"},
    "colors": {
        "primary": "#0078D4",
        "background": "#1E1E1E",
        "surface": "#2D2D2D",
        "text": "#F0F0F0",
        "text_secondary": "#A0A0A0",
        "border": "#3D3D3D",
        "success": "#4ECDC4",
        "warning": "#FFD700",
        "error": "#E74C3C",
    },
    "spacing": {"padding": 8, "gap": 4},
}


class ExportRequest(BaseModel):
    """配置包导出请求体。"""

    meta: dict[str, Any] = Field(description="包元数据")
    dag: dict[str, Any] = Field(description="DAG 定义")
    layout: dict[str, Any] = Field(description="UI 布局")
    theme: dict[str, Any] | None = Field(default=None, description="主题配置")
    data_files: dict[str, list[dict[str, Any]]] | None = Field(default=None, description="附加数据文件")
    asset_files: dict[str, str] | None = Field(default=None, description="资产文件 {文件名: base64内容}")
    filename: str = Field(default="config.calcpack", description="导出文件名")


@router.get("/theme/default")
async def get_default_theme():
    """获取默认主题配置。"""
    return DEFAULT_THEME


def export_calcpack_bytes(req: ExportRequest) -> tuple[bytes, str]:
    """生成 .calcpack 字节内容与文件名（WSGI 同步路由用）。"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        _write_json_in_zip(zf, "meta.json", req.meta)
        _write_json_in_zip(zf, "dag/formula.dag.json", req.dag)
        _write_json_in_zip(zf, "ui/layout.json", req.layout)
        if req.theme:
            _write_json_in_zip(zf, "ui/theme.json", req.theme)
        if req.data_files:
            for key, records in req.data_files.items():
                _write_json_in_zip(zf, f"data/{key}.json", records)
        if req.asset_files:
            for name, b64_content in req.asset_files.items():
                try:
                    raw = base64.b64decode(b64_content)
                    zf.writestr(f"assets/{name}", raw)
                except Exception:
                    pass  # skip invalid base64
    filename = req.filename if req.filename.endswith(".calcpack") else f"{req.filename}.calcpack"
    return buf.getvalue(), filename


@router.post("/export")
async def export_calcpack(req: ExportRequest):
    """导出 .calcpack 配置包文件（ZIP 格式下载）。"""
    try:
        body, filename = export_calcpack_bytes(req)
        return StreamingResponse(
            iter([body]),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {e}") from e


@router.post("/export/preview")
def export_preview(req: ExportRequest):
    """返回导出包的 JSON 内容预览（不返回文件下载）。"""

    try:
        manifest = {
            "meta": req.meta,
            "dag_nodes": len(req.dag.get("nodes", {})),
            "layout_sections": len(req.layout.get("sections", [])),
            "has_theme": req.theme is not None,
            "data_files": {k: len(v) for k, v in (req.data_files or {}).items()},
        }

        return manifest

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览失败: {e}")


def _write_json_in_zip(zf: zipfile.ZipFile, arcname: str, data: Any) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    zf.writestr(arcname, content)


__all__: list[str] = []
