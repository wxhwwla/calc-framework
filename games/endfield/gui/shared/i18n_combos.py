# SPDX-License-Identifier: AGPL-3.0
"""终末地 GUI 下拉框：显示文案 i18n + itemData 保留中文内部标识。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr
from PySide6.QtWidgets import QComboBox

# 与业务逻辑 / 预设 JSON 一致的中文 canonical 值（itemData）
FIXED_SLOT_NONE_LABEL = "（不固定）"

WEAPON_SCOPE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("当前武器", "desktop.endfield.weaponScopeCurrent"),
    ("同类型同星级", "desktop.endfield.weaponScopeSameTypeStar"),
    ("同类型全部", "desktop.endfield.weaponScopeSameTypeAll"),
)

EQUIPMENT_SCOPE_OPTIONS: tuple[tuple[str, str], ...] = (
    ("全部装备", "desktop.endfield.equipmentScopeAll"),
    ("仅套装装备", "desktop.endfield.equipmentScopeSetOnly"),
    ("仅散件装备", "desktop.endfield.equipmentScopeLooseOnly"),
)

DAMAGE_COMPONENT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("skill_only", "desktop.endfield.damageSkillOnly"),
    ("abnormal_only", "desktop.endfield.damageAbnormalOnly"),
    ("skill_and_abnormal", "desktop.endfield.damageBoth"),
)


def populate_i18n_combo(combo: QComboBox, options: tuple[tuple[str, str], ...]) -> None:
    """填充下拉：显示 ``tr(key)``，itemData 为内部中文/标识。"""
    combo.blockSignals(True)
    combo.clear()
    for internal, i18n_key in options:
        combo.addItem(tr(i18n_key), internal)
    combo.blockSignals(False)


def combo_internal_value(combo: QComboBox) -> str:
    """读取 combo 的 itemData；无 data 时回退 currentText。"""
    data = combo.currentData()
    if data is not None:
        return str(data)
    return combo.currentText()


def set_combo_by_internal(combo: QComboBox, internal: str) -> None:
    """按 itemData（内部标识）选中项。"""
    idx = combo.findData(internal)
    if idx >= 0:
        combo.setCurrentIndex(idx)
    else:
        idx = combo.findText(internal)
        if idx >= 0:
            combo.setCurrentIndex(idx)


def read_damage_component_mode(combo: QComboBox) -> str:
    """读取伤害口径 mode_id。"""
    data = combo.currentData()
    if data is not None:
        return str(data)
    legacy = {
        "仅技能": "skill_only",
        "仅异常": "abnormal_only",
        "技能+异常": "skill_and_abnormal",
    }
    return legacy.get(combo.currentText(), "skill_and_abnormal")
