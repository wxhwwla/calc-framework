# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""OCR 图片识别 API — 上传截图后调用 OCR 引擎检测。"""

import os
import tempfile
from pathlib import Path

from api.internal.errors import raise_http_from_exc
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/detect")
async def detect(file: UploadFile = File(...)):
    """OCR 截图检测 — 上传图片并返回识别结果。"""
    suffix = Path(file.filename or "image.png").suffix or ".png"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            from games.endfield.gui.controls.ocr.ocr_detect import ocr_detect_from_file

            result = ocr_detect_from_file(tmp_path)
            return result
        except ImportError:
            raise HTTPException(status_code=501, detail="OCR 引擎未部署")
        finally:
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        raise_http_from_exc(e, status_code=500)


__all__: list[str] = []
