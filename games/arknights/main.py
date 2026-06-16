# SPDX-License-Identifier: AGPL-3.0
"""明日方舟桌面伤害计算器入口点。

用法：
    python games/arknights/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """启动明日方舟桌面伤害计算器。"""
    _REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    _FW_SRC = _REPO_ROOT / "framework" / "src"

    if str(_FW_SRC) not in sys.path:
        sys.path.insert(0, str(_FW_SRC))
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    from calc_framework.logging import setup_logging

    log_dir = _REPO_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(level="INFO", log_file=str(log_dir / "arknights.log"))

    from games.arknights.gui.ArknightsDamageApp import ArknightsDamageApp

    app = ArknightsDamageApp()
    app.run()


if __name__ == "__main__":
    main()
