#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""发布入口：委托到 ``tools.generate_endfield_zone_package``。

历史上这里有一份逐字节复制的生成器，两处独立修改会导致包内容漂移。
实际实现只保留在 ``tools/generate_endfield_zone_package.py``。
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.generate_endfield_zone_package import (
    ALL_ZONE_BUILDERS,
    OUTPUT_DIR,
    PACKAGE_NAME,
    REPO_ROOT,
    build_package,
    main,
)

__all__ = [
    "ALL_ZONE_BUILDERS",
    "OUTPUT_DIR",
    "PACKAGE_NAME",
    "REPO_ROOT",
    "build_package",
    "main",
]

if __name__ == "__main__":
    main()
