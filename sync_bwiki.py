#!/usr/bin/env python3
"""BWIKI 一键同步工具：干员 + 武器 + 装备。

用法::

    python sync_bwiki.py                    # 预览（默认）
    python sync_bwiki.py --apply            # 写入本地 JSON/seed
    python sync_bwiki.py --apply --new      # 同时导入本地尚无条目

等价命令：python tools/bwiki_scout/sync_all.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.bwiki_scout.sync_all import main

if __name__ == "__main__":
    sys.exit(main())
