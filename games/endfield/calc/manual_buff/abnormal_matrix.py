# SPDX-License-Identifier: AGPL-3.0
"""物理/法术异常手动次数矩阵规格（GUI ↔ 计算键 ``异常:L{n}``）。"""

from __future__ import annotations

from dataclasses import dataclass

from games.endfield.calc.manual_buff.physical import (
    PHYSICAL_ABNORMAL_TYPES,
    abnormal_levels_for,
)
from games.endfield.calc.manual_buff.spell_params import SPELL_ABNORMAL_PARAM_ROWS

ABNORMAL_MATRIX_HINT = (
    "列 L0–L4 对应计算异常等级 1–5（消耗层数）；"
    "倒地/击飞仅 L0–L1。填入各档触发次数。"
)


@dataclass(frozen=True)
class AbnormalMatrixRowSpec:
    """单行：界面标签、计算键前缀、可用 UI 等级。"""

    label: str
    abnormal_key: str
    ui_levels: tuple[int, ...]


def ui_level_column_label(ui_level: int) -> str:
    """表头：L{n}（计算用 {n+1} 层）。"""
    lv = max(0, int(ui_level))
    return f"L{lv}\n({lv + 1}层)"


def physical_abnormal_matrix_specs() -> tuple[AbnormalMatrixRowSpec, ...]:
    return tuple(
        AbnormalMatrixRowSpec(
            label=name,
            abnormal_key=name,
            ui_levels=abnormal_levels_for(name),
        )
        for name in PHYSICAL_ABNORMAL_TYPES
    )


def spell_abnormal_matrix_specs() -> tuple[AbnormalMatrixRowSpec, ...]:
    return tuple(
        AbnormalMatrixRowSpec(
            label=str(row["key"]),
            abnormal_key=str(row["key"]),
            ui_levels=(0, 1, 2, 3, 4),
        )
        for row in SPELL_ABNORMAL_PARAM_ROWS
    )


def matrix_column_labels(*, max_ui_level: int = 4) -> tuple[str, ...]:
    return tuple(ui_level_column_label(i) for i in range(max_ui_level + 1))


def read_abnormal_matrix_counts(
    edits_by_row: dict[str, list],
    specs: tuple[AbnormalMatrixRowSpec, ...],
) -> dict[str, int]:
    """从矩阵读取 ``{异常键:ui_level: 次数}``。"""
    result: dict[str, int] = {}
    for spec in specs:
        row_edits = edits_by_row.get(spec.abnormal_key)
        if not row_edits:
            continue
        for j, ui_level in enumerate(spec.ui_levels):
            if j >= len(row_edits):
                break
            edit = row_edits[j]
            try:
                val = max(0, int(edit.text() or "0"))
            except (TypeError, ValueError):
                val = 0
            if val > 0:
                result[f"{spec.abnormal_key}:{ui_level}"] = val
    return result


def apply_abnormal_matrix_counts(
    edits_by_row: dict[str, list],
    specs: tuple[AbnormalMatrixRowSpec, ...],
    counts: dict[str, int] | None,
) -> None:
    """将预设/快照中的次数写回矩阵。"""
    data = counts or {}
    for spec in specs:
        row_edits = edits_by_row.get(spec.abnormal_key)
        if not row_edits:
            continue
        for j, ui_level in enumerate(spec.ui_levels):
            if j >= len(row_edits):
                break
            val = max(0, int(data.get(f"{spec.abnormal_key}:{ui_level}", 0)))
            row_edits[j].setText(str(val) if val else "0")
