# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer — 通用用户展示层。

加载 .calcpack 文件或适配器目录（``framework/adapters/<id>/``），渲染完整的
交互式计算界面。

支持实体选择（角色/武器/装备，含级联选择与明细面板）、自定义输入、实时
DAG 求值。

用法::

    python -m calc_framework.ui.viewer path/to/game.calcpack
    python -m calc_framework.ui.viewer framework/adapters/wjdlglr

"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..dag.schema import DAGVariable
from ..dag.service import DAGService
from .app_icon import apply_application_identity
from .compute_sheet import ComputeSheet
from .i18n import tr
from .layout import Layout
from .theme import ThemeManager
from .viewer_events import CalcPackViewerEventMixin
from .viewer_render import CalcPackViewerRenderMixin
from .viewer_shell import CalcPackViewerShellMixin


class CalcPackViewer(CalcPackViewerShellMixin, CalcPackViewerRenderMixin, CalcPackViewerEventMixin, QMainWindow):
    """通用 .calcpack 查看器 — 加载计算包并渲染交互界面。"""

    def __init__(self, calcpack_path: str | None = None):
        super().__init__()

        self.setWindowTitle(tr("desktop.viewer.windowTitle"))

        self.resize(1400, 900)

        self._loaded_data: dict[str, Any] = {}

        self._meta: dict[str, Any] = {}

        self._dag_service: DAGService | None = None

        self._layout: Layout | None = None

        self._variables: dict[str, DAGVariable] = {}

        self._theme_manager = ThemeManager()

        self._data_files: dict[str, list[dict[str, Any]]] = {}

        self._compute_sheet: ComputeSheet | None = None

        self._entity_selectors: dict[str, QComboBox] = {}

        self._cascade_combos: dict[str, list[QComboBox]] = {}

        self._level_spin: QSpinBox | None = None

        self._current_level: int = 90

        self._entity_data: dict[str, dict[str, Any]] = {}

        self._entity_group: QGroupBox = QGroupBox(tr("desktop.viewer.selectEntity"))

        self._entity_form = QFormLayout(self._entity_group)

        self._detail_group: QGroupBox | None = None

        self._detail_value_labels: dict[str, QLabel] = {}

        self._detail_container = QWidget()

        self._detail_layout: QVBoxLayout = QVBoxLayout(self._detail_container)

        self._detail_layout.setContentsMargins(0, 0, 0, 0)

        self._detail_scroll = QScrollArea()

        self._detail_scroll.setObjectName("detailScroll")

        self._detail_scroll.setWidgetResizable(True)

        self._detail_scroll.setWidget(self._detail_container)

        self._asset_temp_dir: tempfile.TemporaryDirectory | None = None

        self._calcpack_path: str = calcpack_path or ""

        self._init_shell()

        if calcpack_path:
            path_copy = calcpack_path

            QTimer.singleShot(100, lambda p=path_copy: self.load_calcpack(p))

    @property
    def is_loaded(self) -> bool:
        """是否已成功加载计算包或适配器目录。"""
        return self._dag_service is not None


def open_calcpack(path: str | Path) -> None:
    """便捷函数：加载并显示 .calcpack 文件。"""

    app = cast(QApplication, QApplication.instance() or QApplication([]))
    apply_application_identity(app)
    viewer = CalcPackViewer()

    viewer.load_calcpack(path)

    viewer.show()


def open_adapter_dir(path: str | Path) -> None:
    """便捷函数：直接加载并显示适配器目录。"""

    app = cast(QApplication, QApplication.instance() or QApplication([]))
    apply_application_identity(app)
    viewer = CalcPackViewer()

    viewer.load_adapter_dir(path)

    viewer.show()


def main() -> None:
    """CLI 入口。

    用法::

        python -m calc_framework.ui.viewer [path/游戏名.calcpack]
        python -m calc_framework.ui.viewer [适配器目录]

    """

    import sys

    app = QApplication(sys.argv)
    apply_application_identity(app)

    app.setApplicationName(tr("app.calcpackViewer"))

    path = sys.argv[1] if len(sys.argv) > 1 else None

    viewer = CalcPackViewer()

    if path:
        source = Path(path)
        if source.is_dir():
            viewer.load_adapter_dir(source)
        else:
            viewer.load_calcpack(source)

    viewer.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
