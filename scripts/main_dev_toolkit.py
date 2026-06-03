# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱入口 — 整合所有框架开发工具的单一 GUI。"""

from __future__ import annotations

import sys
from pathlib import Path

# ── 路径设置 ──────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 框架 src
_FRAMEWORK_SRC = _ROOT / "framework" / "src"
if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))


def main() -> None:
    from calc_framework.dev_toolkit import main as toolkit_main

    toolkit_main()


if __name__ == "__main__":
    main()
