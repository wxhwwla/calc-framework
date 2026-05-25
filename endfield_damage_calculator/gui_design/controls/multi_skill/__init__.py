#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能次数控件。"""

from .rows import (
    apply_physical_abnormal_counts_to_app,
    apply_segment_counts_to_app,
    apply_spell_abnormal_counts_to_app,
    ensure_multi_skill_segment_rows,
    read_manual_multi_skill_counts,
    read_manual_physical_abnormal_counts,
    read_manual_spell_abnormal_counts,
    rebuild_multi_skill_segment_rows,
    segment_rows_signature,
)
from .section import on_manual_skill_counts_switch_changed, place_multi_skill_section

__all__ = [
    "apply_physical_abnormal_counts_to_app",
    "apply_segment_counts_to_app",
    "apply_spell_abnormal_counts_to_app",
    "ensure_multi_skill_segment_rows",
    "on_manual_skill_counts_switch_changed",
    "place_multi_skill_section",
    "read_manual_multi_skill_counts",
    "read_manual_physical_abnormal_counts",
    "read_manual_spell_abnormal_counts",
    "rebuild_multi_skill_segment_rows",
    "segment_rows_signature",
]
