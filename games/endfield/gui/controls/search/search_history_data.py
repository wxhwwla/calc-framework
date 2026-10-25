# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""搜索历史数据层 — SQLite 查询与格式化（无 PySide6 依赖）。

从 qt_search_browser.py 拆分而来，可被 Web/CLI/测试复用。
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from utils.app_paths import default_search_output_root

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunInfo:
    """单个搜索运行摘要。"""

    signature: str
    total_combinations: int
    processed_combinations: int
    status: str
    db_path: str


@dataclass(frozen=True)
class ScoreInfo:
    """scores 表单条配装记录。"""

    weapon_name: str
    final_damage: float
    chest: str
    gloves: str
    accessory_a: str
    accessory_b: str


def scan_search_output(root: Path | None = None) -> list[Path]:
    """扫描 search_output/ 下所有含 search_runs.db 的子目录。"""
    root = root or default_search_output_root()
    if not root.is_dir():
        return []
    return sorted(
        [d / "search_runs.db" for d in root.iterdir() if d.is_dir() and (d / "search_runs.db").is_file()],
        reverse=True,
    )


def human_size(path: Path) -> str:
    """将文件大小格式化为人类可读字符串。"""
    size = path.stat().st_size
    if size < 1024:
        return f"{size}B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    return f"{size / 1024 / 1024:.1f}MB"


def list_runs(db_path: Path) -> list[RunInfo]:
    """列出 SQLite 数据库中所有 runs。"""
    if not db_path.is_file():
        return []
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT signature, total_combinations, status FROM runs ORDER BY rowid DESC").fetchall()
        infos: list[RunInfo] = []
        for row in rows:
            processed = conn.execute(
                "SELECT COUNT(*) AS cnt FROM processed WHERE signature=?", (row["signature"],)
            ).fetchone()["cnt"]
            infos.append(
                RunInfo(
                    signature=row["signature"],
                    total_combinations=row["total_combinations"],
                    processed_combinations=processed,
                    status=row["status"],
                    db_path=str(db_path),
                )
            )
        return infos
    except sqlite3.Error:
        _logger.warning("SQLite 查询历史记录失败")
        return []
    finally:
        if conn:
            conn.close()


def list_scores(db_path: Path, signature: str) -> list[ScoreInfo]:
    """列出某次运行的 Top-N 得分。"""
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT weapon_name, final_damage, chest, gloves, accessory_a, accessory_b "
            "FROM scores WHERE signature=? ORDER BY final_damage DESC",
            (signature,),
        ).fetchall()
        return [
            ScoreInfo(
                weapon_name=row["weapon_name"],
                final_damage=row["final_damage"],
                chest=row["chest"],
                gloves=row["gloves"],
                accessory_a=row["accessory_a"],
                accessory_b=row["accessory_b"],
            )
            for row in rows
        ]
    except sqlite3.Error:
        _logger.warning("SQLite 查询缓存结果失败")
        return []
    finally:
        if conn:
            conn.close()


def format_loadout_line(score: ScoreInfo) -> str:
    """格式化单条配装摘要。"""
    parts = [
        f"武器: {score.weapon_name}",
        f"伤害: {score.final_damage:.1f}",
    ]
    for label, val in [
        ("护甲", score.chest),
        ("护手", score.gloves),
        ("配件A", score.accessory_a),
        ("配件B", score.accessory_b),
    ]:
        if val:
            parts.append(f"{label}: {val}")
    return "  |  ".join(parts)


def format_clipboard_text(
    run_infos: Sequence[RunInfo] | None = None,
    score_infos: Sequence[ScoreInfo] | None = None,
    db_path: str = "",
) -> str:
    """生成剪贴板文本。"""
    lines: list[str] = []
    if run_infos:
        lines.append("=== 搜索记录 ===")
        for ri in run_infos:
            lines.append(
                f"签名: {ri.signature}  状态: {ri.status}  组合: {ri.processed_combinations}/{ri.total_combinations}"
            )
        lines.append("")
    if score_infos:
        lines.append("=== 前列配装 ===")
        for idx, si in enumerate(score_infos, start=1):
            lines.append(f"第{idx}名: {format_loadout_line(si)}")
        lines.append("")
    if db_path:
        lines.append(f"数据库: {db_path}")
    return "\n".join(lines)
