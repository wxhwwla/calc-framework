#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量遍历结果展示（可测试文案 + GUI 弹窗）。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

import customtkinter as ctk

from calculation.loadout_optimizer import LoadoutScore
from utils.gui_fonts import default_ui_font

# 弹窗默认尺寸（主窗口右侧区域较窄，结果用独立窗口展示）
DEFAULT_DIALOG_WIDTH = 920
DEFAULT_DIALOG_HEIGHT = 720


def _format_top_result_line(rank: int, score: LoadoutScore) -> str:
    loadout = score.loadout_names
    return (
        f"Top{rank}: 武器 {score.weapon_name}  伤害 {score.final_damage:.1f}\n"
        f"       护甲 {loadout.get('chest', '')}  |  "
        f"护手 {loadout.get('gloves', '')}  |  "
        f"配件A {loadout.get('accessory_a', '')}  |  "
        f"配件B {loadout.get('accessory_b', '')}"
    )


def build_search_results_report_lines(
    *,
    mode_label: str,
    skill_label: str,
    scope_labels: tuple[str, str] = ("", ""),
    processed_combinations: int,
    total_combinations: int,
    top_results: Sequence[LoadoutScore],
    export_paths: Optional[dict[str, str]] = None,
    cancelled: bool = False,
) -> list[str]:
    """生成全量遍历结果报告（供弹窗与测试使用）。"""
    weapon_scope, equip_scope = scope_labels
    lines = [
        f"=== {mode_label} ===",
        f"技能: {skill_label}",
    ]
    if weapon_scope:
        lines.append(f"武器候选: {weapon_scope}")
    if equip_scope:
        lines.append(f"装备范围: {equip_scope}")
    lines.append(
        f"组合进度: {processed_combinations}/{total_combinations}"
        + ("（已取消，以下为目前已完成中的 Top）" if cancelled else "")
    )
    lines.append("")
    if not top_results:
        lines.append("无可用 Top 结果，请检查装备数据或缩小候选范围。")
    else:
        lines.append("—— Top 配装 ——")
        for idx, score in enumerate(top_results, start=1):
            lines.append(_format_top_result_line(idx, score))
    if export_paths:
        lines.append("")
        lines.append("—— 导出文件 ——")
        for label, path in export_paths.items():
            if path:
                lines.append(f"{label}: {path}")
    return lines


def loadout_scores_from_payload(rows: Sequence[dict[str, Any]]) -> tuple[LoadoutScore, ...]:
    """将 MVP 流水线返回的 top_results 字典转回 LoadoutScore。"""
    scores: list[LoadoutScore] = []
    for row in rows:
        scores.append(
            LoadoutScore(
                weapon_name=str(row.get("weapon_name", "")),
                final_damage=float(row.get("final_damage", 0.0)),
                loadout_names=dict(row.get("loadout_names") or {}),
            )
        )
    return tuple(scores)


def show_search_results_dialog(
    parent: ctk.CTk,
    *,
    title: str,
    lines: list[str],
    width: int = DEFAULT_DIALOG_WIDTH,
    height: int = DEFAULT_DIALOG_HEIGHT,
) -> None:
    """在独立大窗口中展示遍历结果（可滚动）。"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry(f"{width}x{height}")
    dialog.minsize(640, 480)
    dialog.transient(parent)

    header = ctk.CTkLabel(
        dialog,
        text=title,
        font=default_ui_font(size=18, weight="bold"),
    )
    header.pack(anchor="w", padx=12, pady=(12, 4))

    textbox = ctk.CTkTextbox(
        dialog,
        font=default_ui_font(size=13),
        wrap="word",
    )
    textbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
    textbox.insert("1.0", "\n".join(lines))
    textbox.configure(state="disabled")

    close_btn = ctk.CTkButton(dialog, text="关闭", command=dialog.destroy, width=120)
    close_btn.pack(pady=(0, 12))

    dialog.after(100, dialog.lift)
    dialog.after(120, dialog.focus_force)


def export_paths_to_strings(exports: dict[str, Any]) -> dict[str, str]:
    """将导出路径对象转为弹窗可读的字符串映射。"""
    mapping: dict[str, str] = {}
    for key, value in exports.items():
        if value is None:
            continue
        mapping[key] = str(Path(value))
    return mapping
