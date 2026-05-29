#!/usr/bin/env python3
"""
分级操作日志：记录 GUI 用户路径，便于导出附在 Bug Issue。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any


class LogLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    USER = 30
    WARNING = 40
    ERROR = 50


_LEVEL_NAMES = {level: level.name for level in LogLevel}


@dataclass
class LogEntry:
    timestamp: str = ""
    level: str = "INFO"
    action: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_debug_fields: bool = True) -> dict[str, Any]:
        detail = dict(self.extra)
        if not include_debug_fields:
            detail = {k: v for k, v in detail.items() if not k.startswith("_")}
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "action": self.action,
            "detail": detail,
        }


class OperationLog:
    def __init__(self, min_level: LogLevel = LogLevel.INFO, max_entries: int = 5000):
        self._min_level = min_level
        self._max_entries = max_entries
        self._entries: list[LogEntry] = []

    @property
    def entries(self) -> list[LogEntry]:
        return list(self._entries)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def record(self, level: LogLevel | int, action: str, extra: dict[str, Any] | None = None) -> None:
        if isinstance(level, int):
            level = LogLevel(level)
        if level < self._min_level:
            return
        entry = LogEntry(
            timestamp=self._now_iso(),
            level=level.name,
            action=action,
            extra=extra or {},
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

    def export_json(self) -> str:
        return json.dumps(self.export_payload(), ensure_ascii=False, indent=2)

    def export_payload(self) -> dict[str, Any]:
        return {"entries": [e.to_dict() for e in self._entries]}

    def export_to_file(self, filepath: Path) -> None:
        filepath.write_text(self.export_json(), encoding="utf-8")

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)


_SESSION_LOG: OperationLog | None = None


def get_session_operation_log() -> OperationLog:
    global _SESSION_LOG
    if _SESSION_LOG is None:
        _SESSION_LOG = OperationLog()
    return _SESSION_LOG


def reset_session_operation_log() -> None:
    global _SESSION_LOG
    _SESSION_LOG = None
