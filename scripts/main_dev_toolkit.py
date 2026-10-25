# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱入口 — 整合所有框架开发工具的单一 GUI。"""

from __future__ import annotations

import sys
from pathlib import Path

# ── 路径设置 ──────────────────────────────────────────────
# 仓库根目录必须在 sys.path 最前面，否则 scripts/tools/ 会遮蔽 tools/
_ROOT = Path(__file__).resolve().parent.parent
_ROOT_STR = str(_ROOT)
while _ROOT_STR in sys.path:
    sys.path.remove(_ROOT_STR)
sys.path.insert(0, _ROOT_STR)

# 框架 src
_FRAMEWORK_SRC = _ROOT / "framework" / "src"
_FW_STR = str(_FRAMEWORK_SRC)
while _FW_STR in sys.path:
    sys.path.remove(_FW_STR)
sys.path.insert(0, _FW_STR)


def main() -> None:
    from calc_framework.dev_toolkit import main as toolkit_main

    toolkit_main()


if __name__ == "__main__":
    main()
