#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""PySide6 模块冒烟测试：仅验证导入，不启动 QApplication。"""





def test_qt_app_import() -> None:

    """验证 qt_app 模块可导入。"""

    from games.endfield.gui.shell import _BACKEND



    assert _BACKEND == "qt"





def test_qt_backend_detection() -> None:

    """验证后端始终为 qt。"""

    from games.endfield.gui.shell import is_qt



    assert is_qt()

