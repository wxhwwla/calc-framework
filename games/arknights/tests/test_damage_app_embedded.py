# SPDX-License-Identifier: AGPL-3.0
"""ArknightsDamageApp 嵌入模式 smoke 测试。"""

from __future__ import annotations

import sys

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    yield app  # type: ignore[misc]


def test_damage_app_embedded_init(qapp: QApplication) -> None:
    from games.arknights.gui.ArknightsDamageApp import ArknightsDamageApp

    win = ArknightsDamageApp(embedded=True)
    assert win._embedded is True
    assert win._owns_qapp is False
    assert len(win._operator_index) >= 1


def test_damage_app_standalone_owns_qapp() -> None:
    from games.arknights.gui.ArknightsDamageApp import ArknightsDamageApp

    # 若已有 QApplication（上一测试），embedded 路径仍应可用
    win = ArknightsDamageApp(embedded=False)
    assert win._embedded is False
