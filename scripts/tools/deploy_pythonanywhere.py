#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""PythonAnywhere 自动化部署 — 委托入口。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _path_setup import ensure_root  # noqa: E402

ensure_root()

from web.scripts.deploy_pythonanywhere import main  # noqa: E402

if __name__ == "__main__":
    main()
