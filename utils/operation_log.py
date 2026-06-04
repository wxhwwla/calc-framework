#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

分级操作日志：记录 GUI 用户路径，便于导出附在 Bug Issue。



级别：DEBUG < INFO < USER < WARNING < ERROR（导出默认不含 DEBUG）。

"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any


class LogLevel(IntEnum):
    """日志级别（数值越大越严重）。"""

    DEBUG = 10

    INFO = 20

    USER = 30

    WARNING = 40

    ERROR = 50


_LEVEL_NAMES = {level: level.name for level in LogLevel}


@dataclass
class LogEntry:
    """单条操作记录。"""

    level: LogLevel

    action: str

    detail: dict[str, Any]

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def to_dict(self, *, include_debug_fields: bool = True) -> dict[str, Any]:
        row = {
            "timestamp": self.timestamp,
            "level": _LEVEL_NAMES[self.level],
            "action": self.action,
            "detail": dict(self.detail),
        }

        if not include_debug_fields:
            row["detail"] = {k: v for k, v in row["detail"].items() if not str(k).startswith("_")}

        return row


class OperationLog:
    """内存操作日志，可导出为 JSON 文件。"""

    def __init__(self, *, min_level: LogLevel = LogLevel.INFO) -> None:
        self._min_level = min_level

        self._entries: list[LogEntry] = []

    def record(
        self,
        level: LogLevel,
        action: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """追加一条记录；低于 min_level 的 DEBUG 等会被丢弃。"""

        if level < self._min_level:
            return

        self._entries.append(LogEntry(level=level, action=action, detail=dict(detail or {})))

    def export_payload(self) -> dict[str, Any]:
        """生成可序列化字典。"""

        return {
            "schema": "endfield_operation_log_v1",
            "entry_count": len(self._entries),
            "entries": [e.to_dict() for e in self._entries],
        }

    def export_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.export_payload(), ensure_ascii=False, indent=indent)

    def export_to_file(self, path: Path) -> Path:
        """写入 UTF-8 JSON 文件。"""

        target = Path(path)

        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(self.export_json(), encoding="utf-8")

        return target

    def clear(self) -> None:
        self._entries.clear()


_session_log: OperationLog | None = None


def get_session_operation_log() -> OperationLog:
    """获取当前进程会话级日志（GUI 入口共用）。"""

    global _session_log

    if _session_log is None:
        _session_log = OperationLog()

    return _session_log


def reset_session_operation_log() -> None:
    """测试用：重置会话日志。"""

    global _session_log

    _session_log = None
