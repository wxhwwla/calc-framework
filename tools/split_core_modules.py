#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拆分 optimizer / special_fields / inverse（AST 符号切分）。"""

from __future__ import annotations

from pathlib import Path

from split_module_by_symbols import _patch, split_by_symbols

PKG = Path(__file__).resolve().parents[1] / "endfield_damage_calculator"


def main() -> None:
    split_by_symbols(
        PKG / "calculation/loadout/optimizer.py",
        dest_dir=PKG / "calculation/loadout/optimizer_pkg",
        groups={
            "types.py": [
                "WeaponCandidate",
                "OptimizerConfig",
                "LoadoutScore",
                "RuntimeEvalSnapshot",
                "OptimizerResult",
                "OptimizerTask",
                "OptimizerSearchPlan",
            ],
            "catalog.py": [
                "_is_equipment_beneficial",
                "_apply_equipment_filter",
                "_resolve_config_fixed_loadout",
                "count_loadout_combinations",
                "_iter_loadout_combinations",
            ],
            "plan.py": ["build_optimizer_search_plan"],
            "tasks.py": [
                "iter_optimizer_tasks",
                "enumerate_optimizer_tasks",
                "optimizer_config_for_character",
            ],
            "evaluate.py": ["evaluate_task", "build_runtime_eval_snapshot"],
            "search.py": ["_select_top_n", "search_best_single_skill_loadouts"],
        },
    )
    _patch(
        PKG / "calculation/loadout/optimizer_pkg/plan.py",
        "from .catalog import _apply_equipment_filter, _is_equipment_beneficial, _resolve_config_fixed_loadout, count_loadout_combinations\nfrom .types import OptimizerConfig, OptimizerResult, OptimizerSearchPlan, WeaponCandidate\n\n",
    )
    _patch(
        PKG / "calculation/loadout/optimizer_pkg/tasks.py",
        "from .catalog import _iter_loadout_combinations\nfrom .plan import build_optimizer_search_plan\nfrom .types import OptimizerConfig, OptimizerSearchPlan, OptimizerTask, WeaponCandidate\n\n",
    )
    _patch(
        PKG / "calculation/loadout/optimizer_pkg/evaluate.py",
        "from .types import LoadoutScore, OptimizerConfig, OptimizerTask, RuntimeEvalSnapshot, WeaponCandidate\n\n",
    )
    _patch(
        PKG / "calculation/loadout/optimizer_pkg/search.py",
        "from .evaluate import evaluate_task\nfrom .plan import build_optimizer_search_plan\nfrom .tasks import enumerate_optimizer_tasks, optimizer_config_for_character\nfrom .types import LoadoutScore, OptimizerConfig, OptimizerResult, OptimizerTask, WeaponCandidate\n\n",
    )
    _patch(
        PKG / "calculation/loadout/optimizer_pkg/catalog.py",
        "from .types import OptimizerConfig, OptimizerSearchPlan, WeaponCandidate\n\n",
    )
    (PKG / "calculation/loadout/optimizer_pkg/__init__.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能最优配装搜索。"""

from .catalog import count_loadout_combinations
from .evaluate import build_runtime_eval_snapshot, evaluate_task
from .plan import build_optimizer_search_plan
from .search import search_best_single_skill_loadouts
from .tasks import (
    OptimizerTask,
    enumerate_optimizer_tasks,
    iter_optimizer_tasks,
    optimizer_config_for_character,
)
from .types import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerResult,
    OptimizerSearchPlan,
    RuntimeEvalSnapshot,
    WeaponCandidate,
)
''',
        encoding="utf-8",
    )
    (PKG / "calculation/loadout/optimizer.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单技能最优配装搜索（门面）。"""

from .optimizer_pkg import (
    LoadoutScore,
    OptimizerConfig,
    OptimizerResult,
    OptimizerSearchPlan,
    OptimizerTask,
    RuntimeEvalSnapshot,
    WeaponCandidate,
    build_optimizer_search_plan,
    build_runtime_eval_snapshot,
    count_loadout_combinations,
    enumerate_optimizer_tasks,
    evaluate_task,
    iter_optimizer_tasks,
    optimizer_config_for_character,
    search_best_single_skill_loadouts,
)
''',
        encoding="utf-8",
    )

    split_by_symbols(
        PKG / "character_weapon_equipment/weapon_data/special_fields.py",
        dest_dir=PKG / "character_weapon_equipment/weapon_data/special_pkg",
        groups={
            "codec.py": ["infer_max_stack_from_special", "parse_special_field", "build_special_field"],
            "slots_io.py": ["read_weapon_special_slots", "write_weapon_special_slots"],
            "name_utils.py": [
                "weapon_special_field_keys",
                "bonus_attribute_keys",
                "bonus_curve_for_key",
                "_extract_effect_name_from_special_name",
                "_split_special_name",
                "_special_name_matches",
            ],
            "skills_schema.py": [
                "read_weapon_skills_schema",
                "write_weapon_skills_schema",
                "migrate_weapon_record_to_skill_schema",
                "migrate_weapon_records_to_skill_schema",
            ],
            "runtime_bonus.py": [
                "special_pick_bonus",
                "apply_conditional_special_to_stats",
                "add_special_picks_to_main_sub_bonus",
                "add_special_picks_attack_percent",
                "get_special_value_at_level",
                "migrate_legacy_weapon_special_level",
            ],
        },
    )
    _patch(
        PKG / "character_weapon_equipment/weapon_data/special_pkg/runtime_bonus.py",
        "from .name_utils import _special_name_matches\nfrom .slots_io import read_weapon_special_slots\n\n",
    )
    _patch(
        PKG / "character_weapon_equipment/weapon_data/special_pkg/skills_schema.py",
        "from .codec import build_special_field, parse_special_field\n\n",
    )
    _patch(
        PKG / "character_weapon_equipment/weapon_data/special_pkg/name_utils.py",
        "from .codec import parse_special_field\n\n",
    )
    (PKG / "character_weapon_equipment/weapon_data/special_fields.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器特殊能力字段（门面）。"""

from .special_pkg.codec import *
from .special_pkg.name_utils import *
from .special_pkg.runtime_bonus import *
from .special_pkg.skills_schema import *
from .special_pkg.slots_io import *
''',
        encoding="utf-8",
    )

    split_by_symbols(
        PKG / "calculation/damage/inverse.py",
        dest_dir=PKG / "calculation/damage/inverse_pkg",
        groups={
            "fit_core.py": [
                "_inverse_verbose",
                "_inv_print",
                "_is_decimal_data",
                "_scale_data",
                "_restore_param",
                "_params_sort_key",
                "_gcd_normalize_params",
                "_offset_bounds_for_pair",
                "_find_best_params",
            ],
            "attribute.py": [
                "remove_duplicates",
                "fit_attribute_formula",
                "validate_attribute_formula",
            ],
            "skill.py": [
                "fit_skill_formula",
                "fit_skill_formula_no_special",
                "validate_skill_formula",
                "validate_skill_formula_no_special",
            ],
            "api.py": ["fit_formula", "validate_formula"],
        },
    )
    _patch(
        PKG / "calculation/damage/inverse_pkg/attribute.py",
        "from .fit_core import _find_best_params, _inverse_verbose, _inv_print, _is_decimal_data, _restore_param, _scale_data\n\n",
    )
    _patch(
        PKG / "calculation/damage/inverse_pkg/skill.py",
        "from .fit_core import _find_best_params, _inverse_verbose, _inv_print, _is_decimal_data, _restore_param, _scale_data\n\n",
    )
    _patch(
        PKG / "calculation/damage/inverse_pkg/api.py",
        "from .attribute import fit_attribute_formula, validate_attribute_formula\nfrom .skill import fit_skill_formula, fit_skill_formula_no_special, validate_skill_formula, validate_skill_formula_no_special\n\n",
    )
    (PKG / "calculation/damage/inverse_pkg/__init__.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性/技能公式反推。"""

from .api import fit_formula, validate_formula
from .attribute import fit_attribute_formula, remove_duplicates, validate_attribute_formula
from .fit_core import _is_decimal_data
from .skill import (
    fit_skill_formula,
    fit_skill_formula_no_special,
    validate_skill_formula,
    validate_skill_formula_no_special,
)
''',
        encoding="utf-8",
    )
    (PKG / "calculation/damage/inverse.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性/技能公式反推（门面）。"""

from .inverse_pkg import (
    _is_decimal_data,
    fit_attribute_formula,
    fit_formula,
    fit_skill_formula,
    fit_skill_formula_no_special,
    remove_duplicates,
    validate_attribute_formula,
    validate_formula,
    validate_skill_formula,
    validate_skill_formula_no_special,
)
''',
        encoding="utf-8",
    )
    print("core modules split done")


if __name__ == "__main__":
    main()
