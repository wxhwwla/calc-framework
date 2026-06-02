# SPDX-License-Identifier: AGPL-3.0
from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import os
import tempfile

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/detect")
async def detect(file: UploadFile = File(...)):
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
