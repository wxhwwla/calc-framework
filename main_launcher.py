#!/usr/bin/env python3
"""Game Calc Platform — 统一启动器。

替换 calculator / designer / layout-editor / graph-editor 四个独立入口。

用法::

    python main_launcher.py                        # 显示启动器 GUI
    python main_launcher.py path/to/game.calcpack   # 直接打开 .calcpack
    python main_launcher.py --adapter endfield      # 直接启动指定游戏
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from utils.updater import UpdateInfo, check_update, download_update, extract_and_replace

_REPO = Path(__file__).resolve().parent


# ── 版本 ─────────────────────────────────────────────
def _read_version() -> str:
    try:
        sys.path.insert(0, str(_REPO / "games" / "endfield"))
        from please_read_me import get_version

        return get_version()
    except Exception:
        return "?"


# ── 适配器发现 ─────────────────────────────────────
def _discover_adapters() -> list[dict]:
    adapters_dir = _REPO / "framework" / "adapters"
    results: list[dict] = []
    if not adapters_dir.is_dir():
        return results
    for entry in sorted(adapters_dir.iterdir()):
        if not entry.is_dir():
            continue
        meta_path = entry / "meta.json"
        if not meta_path.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            results.append({
                "name": meta.get("name", entry.name),
                "game": meta.get("game", entry.name),
                "version": meta.get("version", "?"),
                "description": meta.get("description", ""),
                "dir": str(entry),
                "entry_dag": meta.get("entry_dag", ""),
            })
        except Exception:
            continue
    return results


# ── 入口映射 ─────────────────────────────────────
_TOOL_ENTRIES: dict[str, tuple[str, str]] = {
    "终末地计算器": ("main.py", "games/endfield/main.py"),
    "数据设计器": ("main_designer.py", "main_designer.py"),
}


def _launch_tool(name: str) -> None:
    entry, rel_path = _TOOL_ENTRIES[name]
    target = _REPO / rel_path
    if not target.exists():
        QMessageBox.critical(None, "启动失败", f"入口文件未找到:\n{target}")
        return
    subprocess.Popen(
        [sys.executable, str(target)],
        cwd=str(_REPO),
        shell=True,
    )


def _launch_adapter(adapter_name: str) -> None:
    sys.path.insert(0, str(_REPO / "framework" / "src"))
    try:
        from calc_framework.launcher import run_launcher

        run_launcher(adapter_name)
    except ImportError as e:
        QMessageBox.critical(None, "启动失败", f"框架导入失败:\n{e}")


# ── 更新检查线程 ─────────────────────────────────────
class _UpdateCheckThread(QThread):
    found = Signal(object)
    error = Signal(str)

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self._current = current_version

    def run(self) -> None:
        try:
            info = check_update(self._current)
            if info:
                self.found.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class _DownloadThread(QThread):
    progress = Signal(int, int)
    status = Signal(str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, update: UpdateInfo) -> None:
        super().__init__()
        self._update = update

    def run(self) -> None:
        try:
            path = download_update(
                self._update,
                progress=lambda d, t: self.progress.emit(d, t),
                status=lambda s: self.status.emit(s),
            )
            self.finished.emit(path)
        except Exception as e:
            self.error.emit(str(e))


# ── 更新通知/下载对话框 ─────────────────────────────────────
class _UpdateDialog(QDialog):
    def __init__(self, info: UpdateInfo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info = info
        self._downloaded_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowTitle("发现新版本")
        self.setMinimumSize(480, 360)
        self.resize(540, 420)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(f"新版本 v{self._info.latest_version} 可用！")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        if self._info.published_at:
            date_label = QLabel(f"发布日期: {self._info.published_at}")
            date_label.setStyleSheet("color: #888;")
            layout.addWidget(date_label)

        notes_label = QLabel("更新说明:")
        layout.addWidget(notes_label)

        notes = QTextBrowser()
        notes.setPlainText(self._info.release_notes or "暂无更新说明")
        notes.setMaximumHeight(180)
        notes.setStyleSheet("background: #1e1e2e; color: #ccc; border: 1px solid #333; border-radius: 4px;")
        layout.addWidget(notes)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #aaa;")
        layout.addWidget(self._status_label)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._skip_btn = QPushButton("忽略此版本")
        self._skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._skip_btn)

        self._download_btn = QPushButton("下载更新")
        self._download_btn.setStyleSheet("""
            QPushButton { background: #2B6CB6; color: white; border: none;
                          border-radius: 4px; padding: 6px 16px; font-size: 12px; }
            QPushButton:hover { background: #1a4f8a; }
        """)
        self._download_btn.clicked.connect(self._start_download)
        btn_row.addWidget(self._download_btn)

        self._apply_btn = QPushButton("安装并重启")
        self._apply_btn.setVisible(False)
        self._apply_btn.setStyleSheet("""
            QPushButton { background: #38a169; color: white; border: none;
                          border-radius: 4px; padding: 6px 16px; font-size: 12px; }
            QPushButton:hover { background: #2f855a; }
        """)
        self._apply_btn.clicked.connect(self._apply_update)
        btn_row.addWidget(self._apply_btn)

        layout.addLayout(btn_row)

    def _start_download(self) -> None:
        self._download_btn.setEnabled(False)
        self._skip_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)

        self._thread = _DownloadThread(self._info)
        self._thread.progress.connect(self._on_progress)
        self._thread.status.connect(self._status_label.setText)
        self._thread.finished.connect(self._on_downloaded)
        self._thread.error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, downloaded: int, total: int) -> None:
        pct = int(downloaded / max(total, 1) * 100)
        self._progress.setValue(pct)

    def _on_downloaded(self, path: object) -> None:
        self._downloaded_path = Path(str(path))
        self._status_label.setText("下载完成！")
        self._progress.setValue(100)
        self._download_btn.setVisible(False)
        self._apply_btn.setVisible(True)

    def _on_error(self, msg: str) -> None:
        self._status_label.setText(f"下载失败: {msg}")
        self._download_btn.setEnabled(True)
        self._skip_btn.setEnabled(True)
        self._progress.setVisible(False)

    def _apply_update(self) -> None:
        if self._downloaded_path is None:
            return
        self._status_label.setText("正在安装更新...")
        ok = extract_and_replace(self._downloaded_path)
        if ok:
            from utils.updater import restart_launcher
            self._status_label.setText("更新完成，正在重启...")
            restart_launcher()
        else:
            self._status_label.setText("安装失败，请手动更新")
            self._apply_btn.setEnabled(False)


# ── 主窗口 ─────────────────────────────────────
class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Game Calc Platform v{_read_version()}")
        self.setMinimumSize(680, 520)
        self.resize(780, 580)

        # ── 菜单栏 ──
        self._setup_menu()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── 标题 ──
        title = QLabel("Game Calc Platform")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(f"v{_read_version()}  ·  选择游戏或工具")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #888;")
        layout.addWidget(subtitle)

        # ── 游戏适配器区域 ──
        adapters = _discover_adapters()
        if adapters:
            section_label = QLabel("已安装游戏适配器")
            section_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
            layout.addWidget(section_label)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            container = QWidget()
            grid = QVBoxLayout(container)
            grid.setSpacing(8)

            for adp in adapters:
                card = self._build_adapter_card(adp)
                grid.addWidget(card)

            grid.addStretch()
            scroll.setWidget(container)
            layout.addWidget(scroll, stretch=1)

        # ── 工具行 ──
        tools_label = QLabel("工具")
        tools_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(tools_label)

        tool_row = QHBoxLayout()
        tool_row.setSpacing(8)
        for name in _TOOL_ENTRIES:
            btn = QPushButton(name)
            btn.setMinimumHeight(36)
            btn.clicked.connect(lambda _, n=name: _launch_tool(n))
            tool_row.addWidget(btn)
        layout.addLayout(tool_row)

        # ── 状态栏 ──
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage(f"发现 {len(adapters)} 个适配器")

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        tools_menu = menubar.addMenu("工具(&T)")
        check_update_action = QAction("检查更新(&U)", self)
        check_update_action.triggered.connect(self._check_for_updates)
        tools_menu.addAction(check_update_action)

        help_menu = menubar.addMenu("帮助(&H)")
        help_action = QAction("使用说明(&U)", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _check_for_updates(self) -> None:
        cur = _read_version()
        self._status.showMessage("正在检查更新...")
        self._check_thread = _UpdateCheckThread(cur)
        self._check_thread.found.connect(self._on_update_found)
        self._check_thread.error.connect(self._on_update_error)
        self._check_thread.start()

    def _on_update_found(self, info: object) -> None:
        self._status.showMessage("发现新版本")
        ui = UpdateInfo(
            latest_version=info.latest_version,
            download_url=info.download_url,
            asset_name=info.asset_name,
            asset_size=info.asset_size,
            release_notes=info.release_notes,
            published_at=info.published_at,
        )
        dialog = _UpdateDialog(ui, self)
        dialog.exec()

    def _on_update_error(self, msg: str) -> None:
        self._status.showMessage("检查更新失败")
        QMessageBox.warning(self, "检查失败", f"无法检查更新:\n{msg}")

    def _show_help(self) -> None:
        from utils.gui_help_dialog import HelpDialog
        from utils.gui_help_launcher import build_launcher_help
        dialog = HelpDialog(build_launcher_help, self, title="Game Calc Platform 使用说明")
        dialog.exec()

    def _build_adapter_card(self, adp: dict) -> QWidget:
        card = QWidget()
        card.setFixedHeight(60)
        card.setStyleSheet("""
            QWidget {
                background: #1e1e2e;
                border: 1px solid #333;
                border-radius: 6px;
            }
            QWidget:hover {
                border-color: #4a9eff;
                background: #252540;
            }
        """)
        row = QHBoxLayout(card)
        row.setContentsMargins(12, 8, 12, 8)

        info = QVBoxLayout()
        name_label = QLabel(adp["name"])
        name_font = QFont()
        name_font.setPointSize(11)
        name_font.setBold(True)
        name_label.setFont(name_font)
        info.addWidget(name_label)

        desc = adp.get("description", "")
        if desc:
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #aaa; font-size: 10px;")
            info.addWidget(desc_label)

        row.addLayout(info, stretch=1)

        ver_label = QLabel(f"v{adp['version']}")
        ver_label.setStyleSheet("color: #888; font-size: 10px; padding-right: 8px;")
        row.addWidget(ver_label)

        launch_btn = QPushButton("启动")
        launch_btn.setFixedSize(60, 28)
        launch_btn.setStyleSheet("""
            QPushButton {
                background: #2B6CB6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background: #1a4f8a; }
        """)
        adp_name = adp["name"]
        launch_btn.clicked.connect(lambda: _launch_adapter(adp_name))
        row.addWidget(launch_btn)

        return card


# ── 入口 ─────────────────────────────────────
def main() -> None:
    # 支持直接打开 .calcpack
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if path.endswith(".calcpack"):
            sys.path.insert(0, str(_REPO / "framework" / "src"))
            try:
                from calc_framework.ui.viewer import main as viewer_main
                sys.argv = [sys.argv[0], path]
                viewer_main()
                return
            except ImportError as e:
                print(f"无法打开 .calcpack: {e}", file=sys.stderr)
                sys.exit(1)

    # 支持直接启动指定适配器
    if "--adapter" in sys.argv:
        idx = sys.argv.index("--adapter")
        if idx + 1 < len(sys.argv):
            _launch_adapter(sys.argv[idx + 1])
            return

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    dark_palette = app.palette()
    dark_palette.setColor(app.palette().ColorRole.Window, "#1a1a2e")
    dark_palette.setColor(app.palette().ColorRole.WindowText, "#e0e0e0")
    dark_palette.setColor(app.palette().ColorRole.Base, "#16213e")
    dark_palette.setColor(app.palette().ColorRole.Button, "#2d2d4a")
    dark_palette.setColor(app.palette().ColorRole.ButtonText, "#e0e0e0")
    dark_palette.setColor(app.palette().ColorRole.Highlight, "#2B6CB6")
    app.setPalette(dark_palette)

    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
