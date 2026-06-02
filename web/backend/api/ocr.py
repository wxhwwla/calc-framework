# SPDX-License-Identifier: AGPL-3.0
"""OCR 图片识别 API — 上传截图后调用 OCR 引擎检测。"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import os
import tempfile

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
        raise HTTPException(status_code=500, detail=str(e))
