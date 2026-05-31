# SPDX-License-Identifier: AGPL-3.0
"""PythonAnywhere ASGI 入口 — 替代直接 uvicorn main:app"""
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRAMEWORK_SRC = _REPO_ROOT / "framework" / "src"
for _p in [str(_FRAMEWORK_SRC), str(_REPO_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from .main import app

# PythonAnywhere 要求 ASGI application 名为 application
application = app
