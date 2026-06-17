# SPDX-License-Identifier: AGPL-3.0
"""统一启动器 GUI（ADR-0012 Phase 1-3）。

Phase 1: 启动器窗口
Phase 2: 单 exe 打包（冻结模式子进程启动）
Phase 3: 自动更新检查
"""

from __future__ import annotations

import logging
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ...logging import get_logger, setup_logging
from ..log_widget import LogWidget
from ..theme import ThemeManager
from .auto_update import ReleaseInfo, check_for_update_async, download_and_replace
from .runtime import (
    AdapterEntry,
    argv_for_adapter,
    argv_for_calcpack,
    launch_adapter_in_process,
    list_adapter_entries,
    repo_root,
    spawn_detached,
)

_logger = get_logger(__name__)

_HUB_URL = "https://wxhwwla.pythonanywhere.com/hub"
_GITHUB_URL = "https://github.com/wxhwwla/calc-framework"
_GITHUB_RELEASES_URL = "https://github.com/wxhwwla/calc-framework/releases"


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


class _UpdateDialog(QDialog):
    """新版本通知对话框，支持下载更新。"""

    def __init__(self, info: ReleaseInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info = info
        self.setWindowTitle("发现新版本")
        self.setMinimumWidth(480)
        self.setModal(True)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<h3>新版本 {info.version} 可用</h3>"))
        layout.addWidget(QLabel(f"当前版本: {_read_exe_version()}") if _read_exe_version() != "?" else QLabel(""))

        # Release notes（截取前 500 字符）
        notes = info.body[:500] if info.body else "(无发布说明)"
        notes_label = QLabel(notes)
        notes_label.setWordWrap(True)
        notes_label.setMaximumHeight(200)
        notes_label.setProperty("secondary", True)
        layout.addWidget(notes_label)

        # 进度条（初始隐藏）
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        # 按钮
        btn_layout = QHBoxLayout()
        if info.zip_url:
            self._download_btn = QPushButton("下载更新")
            self._download_btn.clicked.connect(self._on_download)
            btn_layout.addWidget(self._download_btn)

        view_btn = QPushButton("查看发布说明")
        view_btn.clicked.connect(lambda: webbrowser.open(info.html_url))
        btn_layout.addWidget(view_btn)

        ignore_btn = QPushButton("忽略此版本")
        ignore_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ignore_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_download(self) -> None:
        """开始下载并替换当前 exe。"""
        info = self._info
        if not info.zip_url:
            return

        self._download_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._status_label.setVisible(True)

        exe_path = Path(sys.executable)

        def _progress_cb(downloaded: int, total: int) -> None:
            QMetaObject.invokeMethod(
                self._progress,
                "setMaximum",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(int, total),
            )
            QMetaObject.invokeMethod(
                self._progress,
                "setValue",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(int, downloaded),
            )

        def _status_cb(msg: str) -> None:
            QMetaObject.invokeMethod(
                self._status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, msg),
            )

        def _do_update():
            success = download_and_replace(
                info.zip_url,
                exe_path,
                _progress_cb,
                _status_cb,
                checksum_url=info.checksum_url,
            )  # type: ignore[arg-type]
            if success:
                QTimer.singleShot(0, self.accept)
                # 弹出重启提示
                QTimer.singleShot(0, lambda: self.parent()._on_update_complete())
            else:
                QTimer.singleShot(0, lambda: self._download_btn.setEnabled(True))

        threading.Thread(target=_do_update, daemon=True).start()


class GameLauncherWindow(QMainWindow):
    """游戏计算器统一启动器。"""

    def __init__(self) -> None:
        super().__init__()
        self._version = _read_exe_version()
        self.setWindowTitle(f"游戏计算器启动器 v{self._version}")
        self.setMinimumSize(520, 520)
        self._root = repo_root()
        self._log_visible = False

        _logger.info("启动器初始化 — v%s (root=%s)", self._version, self._root)

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

        # 日志面板（初始隐藏）
        self._log_widget = LogWidget(max_lines=5000)
        self._log_widget.setVisible(False)
        self._log_widget.attach_to_logger(level=logging.INFO)
        root_layout.addWidget(self._log_widget)

        root_layout.addWidget(self._build_footer())

        self._status = QStatusBar()
        self.setStatusBar(self._status)

        self._reload_adapters()

        # Phase 3：后台检查更新
        self._check_for_updates_background()

        # 延迟自动启动默认游戏（等窗口完全渲染）
        QTimer.singleShot(1500, self._auto_launch_default)

    # ── Phase 3: 自动更新 ─────────────────────────────────

    def _check_for_updates_background(self) -> None:
        """后台线程检查更新，不阻塞启动。"""

        def _on_check_result(info: ReleaseInfo | None) -> None:
            if info is not None and info.is_newer:
                self._show_update_notification(info)

        check_for_update_async(_on_check_result)

    def _check_updates_manual(self) -> None:
        """用户手动点击「检查更新」。"""
        self._status.showMessage("正在检查更新…")

        def _on_check_result(info: ReleaseInfo | None) -> None:
            if info is None:
                QTimer.singleShot(
                    0,
                    lambda: self._status.showMessage(
                        "检查更新失败（网络错误或无 Release）",
                        5000,
                    ),
                )
                return
            if info.is_newer:
                QTimer.singleShot(0, lambda: self._show_update_notification(info))
            else:
                QTimer.singleShot(
                    0,
                    lambda: self._status.showMessage(
                        f"已是最新版本 ({self._version})",
                        5000,
                    ),
                )

        check_for_update_async(_on_check_result)

    def _show_update_notification(self, info: ReleaseInfo) -> None:
        """显示更新通知对话框。"""
        dialog = _UpdateDialog(info, self)
        dialog.show()

    def _on_update_complete(self) -> None:
        """更新完成后提示用户重启。"""
        reply = QMessageBox.information(
            self,
            "更新完成",
            "新版本已下载并替换。是否立即重启以应用更新？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from .runtime import win32_subprocess_kwargs

            subprocess.Popen([sys.executable], **win32_subprocess_kwargs())
            sys.exit(0)

    # ── 底部栏 ───────────────────────────────────────────

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

        update_btn = QPushButton("检查更新")
        update_btn.clicked.connect(self._check_updates_manual)
        layout.addWidget(update_btn)

        self._log_toggle_btn = QPushButton("📋 日志")
        self._log_toggle_btn.setCheckable(True)
        self._log_toggle_btn.clicked.connect(self._toggle_log_panel)
        layout.addWidget(self._log_toggle_btn)

        about_btn = QPushButton("GitHub")
        about_btn.clicked.connect(lambda: webbrowser.open(_GITHUB_URL))
        layout.addWidget(about_btn)

        layout.addStretch()
        return row

    def _toggle_log_panel(self) -> None:
        """切换日志面板显示/隐藏。"""
        self._log_visible = not self._log_visible
        self._log_widget.setVisible(self._log_visible)
        self._log_toggle_btn.setChecked(self._log_visible)

    def _reload_adapters(self) -> None:
        while self._adapter_layout.count():
            item = self._adapter_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 只显示有完整桌面计算器的游戏适配器
        entries = [e for e in list_adapter_entries() if e.has_full_app]
        if not entries:
            self._adapter_layout.addWidget(QLabel("未发现游戏适配包。请确认 framework/adapters/ 下存在游戏 meta.json。"))
        else:
            for entry in entries:
                self._adapter_layout.addWidget(_AdapterCard(entry, self._launch_adapter))
            self._adapter_layout.addStretch()

        self._status.showMessage(f"已发现 {len(entries)} 个游戏")
        _logger.info("游戏适配器: %s", [e.adapter_id for e in entries])

    def _launch_adapter(self, entry: AdapterEntry) -> None:
        try:
            if launch_adapter_in_process(entry, self):
                self._status.showMessage(f"已启动：{entry.name}", 5000)
                return
            spawn_detached(argv_for_adapter(entry, self._root))
            self._status.showMessage(f"已启动：{entry.name}", 5000)
        except OSError as exc:
            QMessageBox.warning(self, "启动失败", str(exc))

    def _auto_launch_default(self) -> None:
        """窗口打开后自动启动终末地（如果有）。"""
        entries = [e for e in list_adapter_entries() if e.has_full_app]
        if not entries:
            return
        # 优先启动终末地
        default = next((e for e in entries if e.adapter_id == "endfield"), entries[0])
        _logger.info("自动启动默认游戏: %s", default.adapter_id)
        self._launch_adapter(default)

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
    import os

    log_dir = Path(__file__).resolve().parents[4] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("CALC_FRAMEWORK_LOG_FILE", str(log_dir / "launcher.log"))

    setup_logging(level="INFO")

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("游戏计算器启动器")
    tm = ThemeManager()
    app.setStyleSheet(tm.stylesheet("dark"))
    window = GameLauncherWindow()
    window.show()
    sys.exit(app.exec())
