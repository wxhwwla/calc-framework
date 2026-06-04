# SPDX-License-Identifier: AGPL-3.0
"""GUI 日志查看控件 — QPlainTextEdit + logging handler Qt 桥接。

用法::

    from calc_framework.ui.log_widget import LogWidget

    widget = LogWidget(max_lines=5000)
    widget.attach_to_logger()          # 挂到 calc_framework 根 logger
    # 或挂到指定 logger: widget.attach_to_logger("my_module")
    widget.show()

所有通过 ``get_logger(__name__)`` 输出的日志自动出现在控件中。
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Q_ARG, QMetaObject, Qt, Slot
from PySide6.QtGui import QAction, QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..logging import get_logger

_ROOT_LOGGER = "calc_framework"

_logger = get_logger(__name__)

_LEVEL_STYLES: dict[int, str] = {
    logging.DEBUG: "color: #888888;",
    logging.INFO: "color: #d4d4d4;",
    logging.WARNING: "color: #ffcc00; font-weight: bold;",
    logging.ERROR: "color: #ff4444; font-weight: bold;",
    logging.CRITICAL: "color: #ff0000; font-weight: bold; background-color: #440000;",
}

_DEFAULT_MAX_LINES = 10_000


class QLogHandler(logging.Handler):
    """logging → Qt 信号桥接。

    在任意线程调用 ``emit()``，通过 ``QMetaObject.invokeMethod``
    在主线程安全追加日志。不依赖 Signal（避免 PySide6 多继承问题）。
    """

    def __init__(self, widget: LogWidget, level: int = logging.NOTSET) -> None:
        super().__init__(level)
        self._widget = widget
        self.setFormatter(
            logging.Formatter(
                "[%(asctime)s.%(msecs)03d] [%(levelname)-7s] [%(name)s] %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            html = _format_record_html(msg, record.levelno)
            QMetaObject.invokeMethod(
                self._widget,
                "_append_log_safe",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, html),
                Q_ARG(int, record.levelno),
            )
        except Exception:
            self.handleError(record)


def _format_record_html(msg: str, levelno: int) -> str:
    style = _LEVEL_STYLES.get(levelno, "color: #d4d4d4;")
    escaped = msg.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    return f"<pre style='{style} margin:0;'>{escaped}</pre>"


class LogWidget(QWidget):
    """GUI 日志查看面板。

    属性:
        max_lines: 最大行数，超出自动丢弃最旧行。
        handler: 绑定的 QLogHandler 实例（可通过 ``handler.setLevel()`` 动态调级）。
    """

    def __init__(self, parent: QWidget | None = None, max_lines: int = _DEFAULT_MAX_LINES) -> None:
        super().__init__(parent)
        self.max_lines = max_lines
        self.handler: QLogHandler | None = None

        self._level_filter = logging.NOTSET  # 显示最低级别
        self._build_ui()

    # ── UI 构建 ────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self._level_combo = QComboBox()
        self._level_combo.addItem("全部", logging.NOTSET)
        self._level_combo.addItem("DEBUG", logging.DEBUG)
        self._level_combo.addItem("INFO", logging.INFO)
        self._level_combo.addItem("WARNING", logging.WARNING)
        self._level_combo.addItem("ERROR", logging.ERROR)
        self._level_combo.currentIndexChanged.connect(self._on_level_filter_changed)
        toolbar.addWidget(QLabel("级别:"))
        toolbar.addWidget(self._level_combo)

        self._auto_scroll_cb = QCheckBox("自动滚动")
        self._auto_scroll_cb.setChecked(True)
        toolbar.addWidget(self._auto_scroll_cb)

        toolbar.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # 日志正文
        self._text = _LogTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Consolas", 9))
        self._text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self._text, stretch=1)

    # ── 公共 API ──────────────────────────────────────────

    def attach_to_logger(self, logger_name: str | None = None, level: int = logging.INFO) -> None:
        """挂到指定 logger（默认 calc_framework 根 logger）。

        所有现有 ``get_logger()`` 调用的输出自动出现在此控件中。
        可在创建 ``LogWidget`` 后多次调用以绑定不同 logger。
        """
        name = logger_name or _ROOT_LOGGER
        logger = logging.getLogger(name)
        self.handler = QLogHandler(self, level)
        logger.addHandler(self.handler)
        # 防止冒泡到根 logger 重复输出（如果根 logger 已有 handler）
        logger.propagate = True
        _logger.info("LogWidget 已挂到 logger '%s' (level=%s)", name, logging.getLevelName(level))

    def detach(self) -> None:
        """从 logger 移除 handler。"""
        if self.handler is None:
            return
        for name in (None, _ROOT_LOGGER):
            logger = logging.getLogger(name)
            if self.handler in logger.handlers:
                logger.removeHandler(self.handler)
        self.handler = None

    def clear(self) -> None:
        self._text.clear()

    def set_level_filter(self, level: int) -> None:
        """动态设置显示的最低级别（不送 logger，仅过滤展示）。"""
        self._level_filter = level

    # ── 内部 ──────────────────────────────────────────────

    @Slot(str, int)
    def _append_log_safe(self, html: str, levelno: int) -> None:
        """由 QMetaObject.invokeMethod 在主线程调用的日志追加方法。"""
        if levelno < self._level_filter:
            return
        text = self._text
        text.appendHtml(html)
        # 行数限制
        block_count = text.blockCount()
        if block_count > self.max_lines:
            cursor = text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                block_count - self.max_lines,
            )
            cursor.removeSelectedText()
            cursor.deleteChar()  # 去掉末尾空行
        # 自动滚动
        if self._auto_scroll_cb.isChecked():
            sb = text.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _on_level_filter_changed(self, _idx: int) -> None:
        level = self._level_combo.currentData()
        self._level_filter = level


class _LogTextEdit(QPlainTextEdit):
    """日志文本区域 — 右键菜单增加「复制选中」。"""

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        action = QAction("清空日志", self)
        action.triggered.connect(self.clear)
        menu.addAction(action)
        menu.exec(event.globalPos())
