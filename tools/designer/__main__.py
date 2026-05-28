#!/usr/bin/env python3
"""开发者工具 CLI 入口。

用法::

    python -m tools.designer                     # 启动 GUI
    python -m tools.designer --help              # 帮助
"""

from __future__ import annotations

import sys
import os

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.designer.app import main

if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)
    main()
