#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""配置包设计器 — 已整合到开发者工具箱。

重导向到 scripts/tools/_deprecated_toolkit.py。

用法::
    推荐：python scripts/启动.bat 工具箱
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _path_setup import ensure_root  # noqa: E402

ensure_root()

from scripts.tools._deprecated_toolkit import redirect  # noqa: E402

if __name__ == "__main__":
    redirect("main_pack_designer")
