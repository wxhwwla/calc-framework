# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""loadout_reader — 统一配装读取模式（无 PySide6 依赖）。

从 endfield_actions.py 和 endfield_search.py 提取的重复调用模式：
read_loadout_from_panels() 的参数收集逻辑集中在本模块。
GUI 层只需传入 dock 控件读取结果，无需重复组装参数。
"""

from __future__ import annotations

from typing import Any

from games.endfield.gui.app.loadout_state import LoadoutState, read_loadout_from_panels


def read_common_loadout(
    char_panel: Any,
    weapon_panel: Any,
    *,
    calculation_mode: str,
    weapon_scope_label: str,
    equipment_scope_label: str,
    fixed_loadout: Any,
    use_manual_multi_skill_counts: bool,
    manual_counts: dict[str, int],
    physical_abnormal_counts: dict[str, int],
    spell_abnormal_counts: dict[str, int],
    damage_component_mode: str,
    use_expected_crit: bool,
    include_conditional_equipment_crit: bool,
    extra_crit_rate: float,
    extra_crit_damage: float,
    enemy_defense: float = 100.0,
    enemy_resistance: float = 0.0,
    ignore_resistance: float = 0.0,
    imbalance_vulnerability_coeff: float = 1.3,
    is_unbalanced: bool = False,
    is_true_damage: bool = False,
    enemy_tier: str = "普通",
    combo_stacks: int = 0,
    attached_effect_multiplier: float = 1.0,
    corrosion_duration_seconds: float = 15.0,
    imbalance_efficiency_bonus: float = 0.0,
) -> LoadoutState | None:
    """统一配装读取入口。

    将 endfield_actions.py（_build_request / _populate_sheet / _on_survival_estimate /
    _on_export_preset）和 endfield_search.py（_build_search_job_inputs）中重复的
    read_loadout_from_panels() 调用模式集中为一个函数。

    参数：
        char_panel: 角色选择面板。
        weapon_panel: 武器选择面板。
        calculation_mode: 计算模式内部标识。
        weapon_scope_label: 武器候选范围标签。
        equipment_scope_label: 装备范围标签。
        fixed_loadout: 固定配装选择。
        use_manual_multi_skill_counts: 是否使用手动次数。
        manual_counts: 手动次数字典。
        physical_abnormal_counts: 物理异常次数。
        spell_abnormal_counts: 法术异常次数。
        damage_component_mode: 伤害组成模式。
        use_expected_crit: 是否使用期望暴击。
        include_conditional_equipment_crit: 是否包含条件暴击。
        extra_crit_rate: 额外暴击率。
        extra_crit_damage: 额外暴击伤害。
        enemy_defense ~ imbalance_efficiency_bonus: 敌方参数（可选）。

    返回：
        LoadoutState 或 None（面板数据无效时）。
    """
    return read_loadout_from_panels(
        char_panel,
        weapon_panel,
        calculation_mode=calculation_mode,
        weapon_scope_label=weapon_scope_label,
        equipment_scope_label=equipment_scope_label,
        fixed_loadout=fixed_loadout,
        use_manual_multi_skill_counts=use_manual_multi_skill_counts,
        manual_counts=manual_counts,
        physical_abnormal_counts=physical_abnormal_counts,
        spell_abnormal_counts=spell_abnormal_counts,
        damage_component_mode=damage_component_mode,
        use_expected_crit=use_expected_crit,
        include_conditional_equipment_crit=include_conditional_equipment_crit,
        extra_crit_rate=extra_crit_rate,
        extra_crit_damage=extra_crit_damage,
        enemy_defense=enemy_defense,
        enemy_resistance=enemy_resistance,
        ignore_resistance=ignore_resistance,
        imbalance_vulnerability_coeff=imbalance_vulnerability_coeff,
        is_unbalanced=is_unbalanced,
        is_true_damage=is_true_damage,
        enemy_tier=enemy_tier,
        combo_stacks=combo_stacks,
        attached_effect_multiplier=attached_effect_multiplier,
        corrosion_duration_seconds=corrosion_duration_seconds,
        imbalance_efficiency_bonus=imbalance_efficiency_bonus,
    )


def read_dock_enemy_params(app: Any) -> dict[str, Any]:
    """从 app 实例读取敌方参数字典（统一来源）。

    参数：
        app: EndfieldApp 实例（或任何有 _enemy_* 属性的对象）。

    返回：
        敌方参数字典，键名与 EnemyParamsState.from_dict() 兼容。
    """
    return {
        "enemy_defense": getattr(app, "_enemy_defense", 100.0),
        "enemy_resistance": getattr(app, "_enemy_resistance", 0.0),
        "ignore_resistance": getattr(app, "_ignore_resistance", 0.0),
        "imbalance_vulnerability_coeff": getattr(app, "_imbalance_vulnerability_coeff", 1.3),
        "is_unbalanced": getattr(app, "_is_unbalanced", False),
        "is_true_damage": getattr(app, "_is_true_damage", False),
        "enemy_tier": getattr(app, "_enemy_tier", "普通"),
        "combo_stacks": getattr(app, "_combo_stacks", 0),
        "attached_effect_multiplier": getattr(app, "_attached_effect_multiplier", 1.0),
        "corrosion_duration_seconds": getattr(app, "_corrosion_duration_seconds", 15.0),
        "imbalance_efficiency_bonus": getattr(app, "_imbalance_efficiency_bonus", 0.0),
        "break_defense_stacks": getattr(app, "_break_defense_stacks", 0),
    }
