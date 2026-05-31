# SPDX-License-Identifier: AGPL-3.0
"""graph_editor 测试共享夹具。"""

import pytest


@pytest.fixture(scope="module")
def qapp():
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app
