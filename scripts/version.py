#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""项目版本号（从 games/endfield/please_read_me.py 反向导入，保证单源）。"""



import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root
ensure_root()

from games.endfield.please_read_me import _VERSION, _EXE_VERSION  # noqa: F401



__all__ = ["_VERSION", "_EXE_VERSION"]

