#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""BWIKI 一键同步入口：干员 + 武器 + 装备。

用法::

    python -m tools.bwiki_scout                    # 预览（默认）
    python -m tools.bwiki_scout --apply            # 写入本地 JSON/seed
    python -m tools.bwiki_scout --apply --new      # 同时导入本地尚无条目
    python -m tools.bwiki_scout --only-operators 陈千语
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.bwiki_scout.sync_all import main

if __name__ == "__main__":
    sys.exit(main())
