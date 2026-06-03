# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 GUI（ADR-0012 Phase 1）。"""

from __future__ import annotations

import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
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

from ..theme import ThemeManager
from .runtime import (
    AdapterEntry,
    argv_for_adapter,
    argv_for_calcpack,
    list_adapter_entries,
    repo_root,
    spawn_detached,
)

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
        self.setMinimumSize(520, 520)
        self._root = repo_root()
        self._server_process: subprocess.Popen | None = None

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
        root_layout.addWidget(self._build_web_server_group())
        root_layout.addWidget(self._build_footer())

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._reload_adapters()

    def _build_tools_group(self) -> QGroupBox:
        box = QGroupBox("开发工具")
        layout = QVBoxLayout(box)

        # 开发者工具箱（统一入口，包含所有开发工具）
        tk_btn = QPushButton("🔧 开发者工具箱")
        tk_btn.setStyleSheet(
            "QPushButton { background: #094771; color: white; "
            "font-weight: bold; padding: 8px; border-radius: 4px; }"
            "QPushButton:hover { background: #0f5f99; }"
        )
        tk_btn.clicked.connect(self._launch_dev_toolkit)
        layout.addWidget(tk_btn)

        hint = QLabel("包含：数据编辑 / 布局编辑 / 图编辑 / DAG调试 / 计算包查看 / AI生成 / OCR标注")
        hint.setWordWrap(True)
        hint.setProperty("secondary", True)
        layout.addWidget(hint)
        return box

    def _launch_dev_toolkit(self) -> None:
        """启动开发者工具箱。"""
        try:
            root = repo_root()
            script = root / "scripts" / "main_dev_toolkit.py"
            if not script.exists():
                QMessageBox.warning(self, "启动失败", "找不到 main_dev_toolkit.py")
                return
            spawn_detached([sys.executable, str(script)])
            self._status.showMessage("已启动开发者工具箱", 5000)
        except OSError as exc:
            QMessageBox.warning(self, "启动失败", str(exc))

    def _build_web_server_group(self) -> QGroupBox:
        """本地 Web 服务器控制区。"""
        box = QGroupBox("本地 Web 服务器")
        layout = QHBoxLayout(box)

        self._server_status = QLabel("⚪ 未启动")
        layout.addWidget(self._server_status)

        self._server_btn = QPushButton("启动服务器")
        self._server_btn.clicked.connect(self._toggle_web_server)
        layout.addWidget(self._server_btn)

        self._open_browser_btn = QPushButton("打开浏览器")
        self._open_browser_btn.clicked.connect(
            lambda: webbrowser.open("http://localhost:8180")
        )
        self._open_browser_btn.setEnabled(False)
        layout.addWidget(self._open_browser_btn)

        layout.addStretch()
        return box

    def _toggle_web_server(self) -> None:
        """切换 Web 服务器启动/停止。"""
        if self._server_process is not None:
            self._stop_web_server()
        else:
            self._start_web_server()

    def _start_web_server(self) -> None:
        """启动本地 Web 服务器（uvicorn）。"""
        backend_dir = self._root / "web" / "backend"
        if not (backend_dir / "main.py").exists():
            QMessageBox.warning(self, "启动失败", f"找不到后端入口:\n{backend_dir / 'main.py'}")
            return

        self._server_btn.setEnabled(False)
        self._server_btn.setText("启动中...")
        self._server_status.setText("🟡 正在启动...")

        def _run() -> None:
            try:
                proc = subprocess.Popen(
                    [sys.executable, "-m", "uvicorn", "main:app",
                     "--host", "127.0.0.1", "--port", "8180"],
                    cwd=str(backend_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                import time
                time.sleep(2)

                if proc.poll() is not None:
                    # 进程已退出
                    self._server_status_label("🔴 启动失败")
                    self._server_btn.setText("启动服务器")
                    self._server_btn.setEnabled(True)
                else:
                    self._server_process = proc
                    self._server_status_label("🟢 运行中 (127.0.0.1:8180)")
                    self._server_btn.setText("停止服务器")
                    self._server_btn.setEnabled(True)
                    self._open_browser_btn.setEnabled(True)
                    webbrowser.open("http://localhost:8180")
            except Exception as exc:
                self._server_status_label(f"🔴 错误: {exc}")
                self._server_btn.setText("启动服务器")
                self._server_btn.setEnabled(True)

        threading.Thread(target=_run, daemon=True).start()

    def _server_status_label(self, text: str) -> None:
        """线程安全地更新状态标签。"""
        from PySide6.QtCore import QMetaObject, Qt as _Qt

        QMetaObject.invokeMethod(
            self._server_status,
            "setText",
            _Qt.ConnectionType.QueuedConnection,
            text,
        )

    def _stop_web_server(self) -> None:
        """停止 Web 服务器。"""
        if self._server_process is not None:
            self._server_process.terminate()
            self._server_process = None
        self._server_status.setText("⚪ 已停止")
        self._server_btn.setText("启动服务器")
        self._open_browser_btn.setEnabled(False)

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
