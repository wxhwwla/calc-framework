# SPDX-License-Identifier: AGPL-3.0
"""计算包查看器 CLI 入口。

用法::

    python -m calc_framework.ui             # 启动 GUI（可选文件参数）
    python -m calc_framework.ui path/游戏.calcpack
"""

from __future__ import annotations

import sys
import os

_src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)

from calc_framework.ui.viewer import main

if __name__ == "__main__":
    main()
