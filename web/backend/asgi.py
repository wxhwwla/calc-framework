# SPDX-License-Identifier: AGPL-3.0
"""PythonAnywhere ASGI 入口 — 替代直接 uvicorn main:app"""
from ._path_setup import setup_paths

setup_paths()

from .main import app  # noqa: E402

# PythonAnywhere 要求 ASGI application 名为 application
application = app
