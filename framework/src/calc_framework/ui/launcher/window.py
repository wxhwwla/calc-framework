# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 GUI（ADR-0012 Phase 1）。"""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from calc_framework.ui.launcher.runtime import (
    AdapterEntry,
    argv_for_adapter,
    argv_for_calcpack,
    argv_for_tool,
    list_adapter_entries,
    repo_root,
    spawn_detached,
)
from calc_framework.ui.theme import ThemeManager

_HUB_URL = "https://wxhwwla.pythonanywhere.com/hub"
_GITHUB_URL = "https://github.com/wxhwwla/calc-framework"


def _read_exe_version() -> str:
    try:
        root = repo_root()
        sys.path.insert(0, str(root))
        from scripts.please_read_me import _EXE_VERSION

        return str(_EXE_VERSION)
    except Exception:
        return "?"


class _AdapterCard(QFrame):
    """单个适配包卡片。"""

    def __init__(self, entry: AdapterEntry, on_launch, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._entry = entry
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)

        title = QLabel(f"<b>{entry.name}</b>")
        layout.addWidget(title)

        meta_parts = [f"v{entry.version}"]
        if entry.game:
            meta_parts.append(entry.game)
        layout.addWidget(QLabel(" · ".join(meta_parts)))

        if entry.description:
            desc = QLabel(entry.description)
            desc.setWordWrap(True)
            desc.setProperty("secondary", True)
            layout.addWidget(desc)

        hint = "完整桌面计算器" if entry.has_full_app else "通用 ComputeSheet"
        layout.addWidget(QLabel(hint))

        btn = QPushButton("启动")
        btn.clicked.connect(lambda: on_launch(entry))
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignRight)


class GameLauncherWindow(QMainWindow):
    """游戏计算器统一启动器。"""

    def __init__(self) -> None:
        super().__init__()
        version = _read_exe_version()
        self.setWindowTitle(f"游戏计算器启动器 v{version}")
        self.setMinimumSize(520, 480)
        self._root = repo_root()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        root_layout.addWidget(QLabel("<h2>选择游戏适配器</h2>"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_body = QWidget()
        self._adapter_layout = QVBoxLayout(scroll_body)
        scroll.setWidget(scroll_body)
        root_layout.addWidget(scroll, stretch=1)

        root_layout.addWidget(self._build_tools_group())
        root_layout.addWidget(self._build_footer())

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._reload_adapters()

    def _build_tools_group(self) -> QGroupBox:
        box = QGroupBox("工具")
        grid = QGridLayout(box)
        tools = [
            ("数据设计器", "designer"),
            ("配置包设计器", "pack_designer"),
            ("CalcPack 查看器", "viewer"),
            ("公式图编辑器", "graph_editor"),
            ("布局编辑器", "layout_editor"),
        ]
        for i, (label, tool_id) in enumerate(tools):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _=False, tid=tool_id: self._launch_tool(tid))
            grid.addWidget(btn, i // 3, i % 3)
        return box

    def _build_footer(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        open_btn = QPushButton("打开 .calcpack…")
        open_btn.clicked.connect(self._open_calcpack_dialog)
        layout.addWidget(open_btn)

        hub_btn = QPushButton("Calc Hub")
        hub_btn.clicked.connect(lambda: webbrowser.open(_HUB_URL))
        layout.addWidget(hub_btn)

        about_btn = QPushButton("GitHub")
        about_btn.clicked.connect(lambda: webbrowser.open(_GITHUB_URL))
        layout.addWidget(about_btn)

        layout.addStretch()
        return row

    def _reload_adapters(self) -> None:
        while self._adapter_layout.count():
            item = self._adapter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        entries = list_adapter_entries()
        if not entries:
            self._adapter_layout.addWidget(
                QLabel("未发现适配包。请确认 framework/adapters/ 下存在 meta.json。")
            )
        else:
            for entry in entries:
                self._adapter_layout.addWidget(_AdapterCard(entry, self._launch_adapter))
            self._adapter_layout.addStretch()

        self._status.showMessage(f"已发现 {len(entries)} 个适配包")

    def _launch_adapter(self, entry: AdapterEntry) -> None:
        try:
            spawn_detached(argv_for_adapter(entry, self._root))
            self._status.showMessage(f"已启动：{entry.name}", 5000)
        except OSError as exc:
            QMessageBox.warning(self, "启动失败", str(exc))

    def _launch_tool(self, tool_id: str) -> None:
        try:
            spawn_detached(argv_for_tool(tool_id, self._root))
            self._status.showMessage(f"已启动工具：{tool_id}", 5000)
        except (KeyError, OSError) as exc:
            QMessageBox.warning(self, "启动失败", str(exc))

    def _open_calcpack_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "打开 .calcpack",
            str(self._root),
            "CalcPack (*.calcpack);;所有文件 (*.*)",
        )
        if not path:
            return
        self._open_calcpack(Path(path))

    def _open_calcpack(self, path: Path) -> None:
        if not path.is_file():
            QMessageBox.warning(self, "打开失败", f"文件不存在：{path}")
            return
        try:
            spawn_detached(argv_for_calcpack(path, self._root))
            self._status.showMessage(f"已打开：{path.name}", 5000)
        except OSError as exc:
            QMessageBox.warning(self, "打开失败", str(exc))


def run_gui_launcher() -> None:
    """启动 PySide6 启动器窗口。"""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("游戏计算器启动器")
    tm = ThemeManager()
    app.setStyleSheet(tm.stylesheet("dark"))
    window = GameLauncherWindow()
    window.show()
    sys.exit(app.exec())
