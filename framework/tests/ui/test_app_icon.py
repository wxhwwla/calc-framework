# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""应用图标与任务栏身份测试。

回归：查看器/启动器未设置窗口图标，Windows 任务栏显示 pythonw 的
蛇形图标，用户会误以为是残留的控制台；关闭该图标会连同 GUI 一起退出。
"""

from __future__ import annotations

import ctypes
import sys

import pytest
from PySide6.QtWidgets import QApplication

from calc_framework.ui.app_icon import apply_application_identity, build_app_icon


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_build_app_icon_provides_common_sizes(qapp) -> None:
    """任务栏/Alt-Tab/高 DPI 需要多种位图尺寸，至少要包含 32 与 256。"""
    icon = build_app_icon()
    sizes = {(size.width(), size.height()) for size in icon.availableSizes()}
    assert (32, 32) in sizes
    assert (256, 256) in sizes


def test_apply_application_identity_sets_window_icon(qapp) -> None:
    """身份应用后，QApplication 必须有非空窗口图标。"""
    apply_application_identity(qapp, "CalcFramework.Test")
    assert not qapp.windowIcon().isNull()


class _FakeShell32:
    """记录 AppUserModelID 调用的假 shell32。"""

    def __init__(self) -> None:
        self.app_id: str | None = None

    def SetCurrentProcessExplicitAppUserModelID(self, value: str) -> int:  # noqa: N802
        """记录传入的 AppUserModelID。"""
        self.app_id = value
        return 0


class _FakeWindll:
    """最小 ctypes.windll 替身。"""

    def __init__(self) -> None:
        self.shell32 = _FakeShell32()


def test_apply_application_identity_sets_windows_app_id(qapp, monkeypatch) -> None:
    """Windows 下必须设置 AppUserModelID，否则任务栏仍按解释器归类。"""
    fake = _FakeWindll()
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(ctypes, "windll", fake, raising=False)

    apply_application_identity(qapp, "CalcFramework.Test")

    assert fake.shell32.app_id == "CalcFramework.Test"


def test_apply_application_identity_skips_app_id_off_windows(qapp, monkeypatch) -> None:
    """非 Windows 平台不触碰 ctypes.windll。"""
    fake = _FakeWindll()
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(ctypes, "windll", fake, raising=False)

    apply_application_identity(qapp, "CalcFramework.Test")

    assert fake.shell32.app_id is None
