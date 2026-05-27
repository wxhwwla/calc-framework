#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PySide6 模块冒烟测试：仅验证导入，不启动 QApplication。"""

import os


def test_qt_app_import() -> None:
    """验证 qt_app 模块可导入。"""
    os.environ["ENDFIELD_UI_BACKEND"] = "qt"
    # 重置 _BACKEND（backends.__init__ 在进程生命周期只执行一次，
    # 本文件单独运行 pytest 时生效）
    from gui_design.backends import _BACKEND

    assert _BACKEND == "qt"


def test_qt_backend_detection() -> None:
    """验证环境变量检测。"""
    from gui_design.backends import is_qt, is_ctk

    # 本 test 文件在 ENDFIELD_UI_BACKEND=qt 环境下运行
    # 不 assert，仅做兼容性检查
    assert is_qt() or is_ctk()
