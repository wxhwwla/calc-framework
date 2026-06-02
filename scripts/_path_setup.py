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


def ensure_tools() -> None:
    """将 tools/ 加入 sys.path（endfield_designer 等包）。"""
    tools = Path(__file__).resolve().parent.parent / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))


def ensure_framework_src() -> None:
    """将 framework/src 加入 sys.path（calc_framework 源码开发模式）。"""
    src = Path(__file__).resolve().parent.parent / "framework" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def ensure_games_endfield() -> None:
    """将 games/endfield 加入 sys.path（gui 等顶层包）。"""
    pkg = Path(__file__).resolve().parent.parent / "games" / "endfield"
    if str(pkg) not in sys.path:
        sys.path.insert(0, str(pkg))
