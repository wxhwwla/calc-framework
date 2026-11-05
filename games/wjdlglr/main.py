# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""无尽的拉格朗日武器输出计算器入口点。

用法：
    python games/wjdlglr/main.py

桌面入口直接加载 ``framework/adapters/wjdlglr`` 适配器目录，由通用
``CalcPackViewer`` 渲染，与 ``.calcpack`` 查看器共用同一套界面。
"""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    """启动无尽的拉格朗日桌面计算器。"""
    repo_root = Path(__file__).resolve().parent.parent.parent
    fw_src = repo_root / "framework" / "src"

    for path in (repo_root, fw_src):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    from calc_framework.config.manager import get_adapters_dir
    from calc_framework.logging import setup_logging

    from utils.path_utils import get_application_dir

    log_dir = get_application_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(level="INFO", log_file=str(log_dir / "wjdlglr.log"))

    from calc_framework.ui.app_icon import apply_application_identity
    from calc_framework.ui.viewer import CalcPackViewer
    from PySide6.QtWidgets import QApplication

    existing = QApplication.instance()
    if isinstance(existing, QApplication):
        app = existing
        owns_app = False
    else:
        app = QApplication(sys.argv)
        owns_app = True

    apply_application_identity(app, "CalcFramework.Wjdlglr")

    viewer = CalcPackViewer()
    if not viewer.load_adapter_dir(get_adapters_dir() / "wjdlglr"):
        viewer.close()
        if owns_app:
            sys.exit(1)
        return

    viewer.showMaximized()

    if owns_app:
        sys.exit(app.exec())


if __name__ == "__main__":
    main()
