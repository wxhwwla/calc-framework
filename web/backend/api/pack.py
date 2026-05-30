"""配置包设计器 API — 主题管理 + .calcpack 导出。"""

import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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
    meta: dict[str, Any]
    dag: dict[str, Any]
    layout: dict[str, Any]
    theme: dict[str, Any] | None = None
    data_files: dict[str, list[dict[str, Any]]] | None = None
    filename: str = "config.calcpack"


@router.get("/theme/default")
async def get_default_theme():
    return DEFAULT_THEME


@router.post("/export")
async def export_calcpack(req: ExportRequest):
    try:
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
        buf.seek(0)

        filename = req.filename
        if not filename.endswith(".calcpack"):
            filename += ".calcpack"

        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {e}")


@router.post("/export/preview")
async def export_preview(req: ExportRequest):
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
