# SPDX-License-Identifier: AGPL-3.0
"""为 scripts/ 目录下的入口脚本提供项目根路径设置。

用法::

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _path_setup import ensure_root
    ensure_root()

"""
import sys
from pathlib import Path


def ensure_root() -> None:
    """将项目根目录（scripts/ 的父目录）加入 sys.path。"""
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
