#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按顶层符号名拆分 Python 模块（保留 import 前导段）。"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Iterable


def _module_preamble(source: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    first_start: int | None = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            if node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            first_start = start if first_start is None else min(first_start, start)
        elif isinstance(node, ast.Assign):
            start = node.lineno - 1
            first_start = start if first_start is None else min(first_start, start)
    if first_start is None:
        return source
    return "".join(lines[:first_start])


def _top_level_ranges(source: str) -> dict[str, tuple[int, int]]:
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    spans: list[tuple[str, int]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    spans.append((target.id, node.lineno - 1))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            if node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            spans.append((node.name, start))
    spans.sort(key=lambda x: x[1])
    ends = [s[1] for s in spans[1:]] + [len(lines)]
    return {name: (start, ends[i]) for i, (name, start) in enumerate(spans)}


def split_by_symbols(
    src: Path,
    *,
    dest_dir: Path,
    groups: dict[str, Iterable[str]],
    facade: Path | None = None,
    facade_exports: list[str] | None = None,
) -> None:
    source = src.read_text(encoding="utf-8")
    preamble = _module_preamble(source)
    lines = source.splitlines(keepends=True)
    ranges = _top_level_ranges(source)
    dest_dir.mkdir(parents=True, exist_ok=True)

    for filename, symbols in groups.items():
        chunks: list[str] = []
        for sym in symbols:
            if sym not in ranges:
                raise KeyError(f"{src}: missing symbol {sym!r}")
            start, end = ranges[sym]
            chunks.append("".join(lines[start:end]))
        (dest_dir / filename).write_text(preamble + "".join(chunks), encoding="utf-8")
        print(f"  wrote {dest_dir / filename}")

    if facade is not None and facade_exports:
        rel = dest_dir.name
        parent = dest_dir.parent
        imports = "\n".join(
            f"from .{rel}.{mod[:-3]} import {', '.join(syms)}"
            for mod, syms in _group_exports(groups, facade_exports).items()
        )
        body = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{src.stem}（门面）。"""

{imports}
'''
        facade.write_text(body, encoding="utf-8")
        print(f"  wrote {facade}")


def _group_exports(groups: dict[str, Iterable[str]], exports: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    export_set = set(exports)
    for mod, syms in groups.items():
        picked = [s for s in syms if s in export_set]
        if picked:
            out[mod] = picked
    return out


def split_into_package(
    src: Path,
    *,
    dest_pkg: Path,
    groups: dict[str, Iterable[str]],
    init_body: str,
    patches: dict[str, str] | None = None,
) -> None:
    """将单文件模块拆成包目录，并删除原文件。"""
    split_by_symbols(src, dest_dir=dest_pkg, groups=groups)
    if patches:
        for rel, insert in patches.items():
            _patch(dest_pkg / rel, insert)
    (dest_pkg / "__init__.py").write_text(init_body, encoding="utf-8")
    src.unlink()
    print(f"  package {dest_pkg.name} done (removed {src.name})")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="按顶层符号拆分 Python 模块")
    parser.add_argument(
        "--only",
        choices=("all", "presentation", "core", "soft"),
        default="core",
        help="all=全部；core=optimizer/special/inverse；soft=剩余 >400 行模块",
    )
    args = parser.parse_args()
    pkg = Path(__file__).resolve().parents[1] / "endfield_damage_calculator"

    if args.only in ("all", "presentation"):
        _split_presentation(pkg)

    if args.only in ("all", "core"):
        _split_core(pkg)

    if args.only in ("all", "soft"):
        _split_soft(pkg)


def _split_presentation(pkg: Path) -> None:
    preview_src = pkg / "gui_design/presentation/preview_lines.py"
    if "build_single_skill_search_preview_lines" not in preview_src.read_text(encoding="utf-8"):
        print("preview + display already split, skip")
        return

    # preview_lines
    split_by_symbols(
        pkg / "gui_design/presentation/preview_lines.py",
        dest_dir=pkg / "gui_design/presentation/preview",
        groups={
            "single_skill.py": [
                "build_single_skill_search_preview_lines",
                "_build_single_skill_search_preview_lines_impl",
            ],
            "multi_skill.py": [
                "build_multi_skill_search_preview_lines",
                "_build_multi_skill_search_preview_lines_impl",
            ],
        },
        facade=pkg / "gui_design/presentation/preview_lines.py",
        facade_exports=[
            "build_single_skill_search_preview_lines",
            "build_multi_skill_search_preview_lines",
        ],
    )

    # display_lines
    split_by_symbols(
        pkg / "gui_design/presentation/display_lines.py",
        dest_dir=pkg / "gui_design/presentation/display",
        groups={
            "format.py": [
                "weapon_bonus_display_uses_percent",
                "_weapon_bonus_uses_integer_display",
                "evaluate_display_state",
                "format_weapon_bonus_display_value",
                "_get_attribute_value",
                "format_skill_multiplier_display_value",
                "_skill_segment_display_value",
                "SelectedSkillForDamage",
            ],
            "character.py": [
                "build_character_skill_damage_type_lines",
                "build_character_skill_lines",
                "build_character_attribute_lines",
                "build_weapon_attribute_lines",
            ],
            "skill_resolve.py": ["resolve_selected_skill_for_damage"],
            "single_hit.py": [
                "format_fifteen_zone_damage_lines",
                "build_single_hit_damage_lines",
                "_build_single_hit_damage_lines_impl",
            ],
        },
        facade=pkg / "gui_design/presentation/display_lines.py",
        facade_exports=[
            "NO_DAMAGE_MULTIPLIER_TEXT",
            "SelectedSkillForDamage",
            "build_character_attribute_lines",
            "build_character_skill_damage_type_lines",
            "build_character_skill_lines",
            "build_single_hit_damage_lines",
            "build_weapon_attribute_lines",
            "evaluate_display_state",
            "format_fifteen_zone_damage_lines",
            "format_skill_multiplier_display_value",
            "format_weapon_bonus_display_value",
            "resolve_selected_skill_for_damage",
            "weapon_bonus_display_uses_percent",
        ],
    )

    # 写 display __init__ 与 display_lines 门面（常量 NO_DAMAGE_MULTIPLIER_TEXT 在前导段）
    display_init = pkg / "gui_design/presentation/display/__init__.py"
    display_init.write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性/乘区/单段伤害展示文案。"""

from .character import (
    build_character_attribute_lines,
    build_character_skill_damage_type_lines,
    build_character_skill_lines,
    build_weapon_attribute_lines,
)
from .format import (
    NO_DAMAGE_MULTIPLIER_TEXT,
    SelectedSkillForDamage,
    evaluate_display_state,
    format_skill_multiplier_display_value,
    format_weapon_bonus_display_value,
    weapon_bonus_display_uses_percent,
)
from .single_hit import build_single_hit_damage_lines, format_fifteen_zone_damage_lines
from .skill_resolve import resolve_selected_skill_for_damage
''',
        encoding="utf-8",
    )
    (pkg / "gui_design/presentation/display_lines.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性/乘区/单段伤害展示文案（门面）。"""

from .display import *  # noqa: F403
from .display.format import NO_DAMAGE_MULTIPLIER_TEXT, SelectedSkillForDamage
from .display.character import (
    build_character_attribute_lines,
    build_character_skill_damage_type_lines,
    build_character_skill_lines,
    build_weapon_attribute_lines,
)
from .display.single_hit import build_single_hit_damage_lines, format_fifteen_zone_damage_lines
from .display.skill_resolve import resolve_selected_skill_for_damage
from .display.format import (
    evaluate_display_state,
    format_skill_multiplier_display_value,
    format_weapon_bonus_display_value,
    weapon_bonus_display_uses_percent,
)
''',
        encoding="utf-8",
    )

    preview_init = pkg / "gui_design/presentation/preview/__init__.py"
    preview_init.write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""预览文案子包。"""

from .multi_skill import build_multi_skill_search_preview_lines
from .single_skill import build_single_skill_search_preview_lines
''',
        encoding="utf-8",
    )
    (pkg / "gui_design/presentation/preview_lines.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单/多技能遍历快速预览文案（门面）。"""

from .preview import build_multi_skill_search_preview_lines, build_single_skill_search_preview_lines
''',
        encoding="utf-8",
    )

    print("preview + display done")


def _split_core(pkg: Path) -> None:
    opt_src = pkg / "calculation/loadout/optimizer.py"
    if not opt_src.is_file():
        print("optimizer already package, skip")
    else:
        opt_pkg = pkg / "calculation/loadout/optimizer"
        split_into_package(
            opt_src,
            dest_pkg=opt_pkg,
            groups={
                "types.py": [
                    "WeaponCandidate",
                    "OptimizerConfig",
                    "LoadoutScore",
                    "RuntimeEvalSnapshot",
                    "OptimizerResult",
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
                    "OptimizerTask",
                    "iter_optimizer_tasks",
                    "enumerate_optimizer_tasks",
                    "optimizer_config_for_character",
                ],
                "evaluate.py": ["evaluate_task", "build_runtime_eval_snapshot"],
                "search.py": ["_select_top_n", "search_best_single_skill_loadouts"],
            },
            patches={
                "plan.py": "from .catalog import _apply_equipment_filter, _is_equipment_beneficial, _resolve_config_fixed_loadout, count_loadout_combinations\nfrom .types import OptimizerConfig, OptimizerResult, OptimizerSearchPlan, WeaponCandidate\n\n",
                "tasks.py": "from .catalog import _iter_loadout_combinations\nfrom .plan import build_optimizer_search_plan\nfrom .types import OptimizerConfig, OptimizerSearchPlan, WeaponCandidate\n\n",
                "evaluate.py": "from .tasks import OptimizerTask\nfrom .types import LoadoutScore, OptimizerConfig, RuntimeEvalSnapshot, WeaponCandidate\n\n",
                "search.py": "from .evaluate import evaluate_task\nfrom .plan import build_optimizer_search_plan\nfrom .tasks import OptimizerTask, enumerate_optimizer_tasks, optimizer_config_for_character\nfrom .types import LoadoutScore, OptimizerConfig, OptimizerResult, WeaponCandidate\n\n",
                "catalog.py": "from .types import OptimizerConfig, OptimizerSearchPlan, WeaponCandidate\n\n",
            },
            init_body='''#!/usr/bin/env python3
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
        )

    sf_src = pkg / "character_weapon_equipment/weapon_data/special_fields.py"
    if not sf_src.is_file():
        print("special_fields already package, skip")
    else:
        sf_pkg = pkg / "character_weapon_equipment/weapon_data/special_fields"
        split_into_package(
            sf_src,
            dest_pkg=sf_pkg,
            groups={
                "codec.py": [
                    "SPECIAL_FIELD_KEYS",
                    "LEGACY_SPECIAL_KEY",
                    "_MAX_STACK_PATTERNS",
                    "infer_max_stack_from_special",
                    "parse_special_field",
                    "build_special_field",
                ],
                "slots_io.py": ["read_weapon_special_slots", "write_weapon_special_slots"],
                "name_utils.py": [
                    "_EFFECT_NAME_RE",
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
            patches={
                "slots_io.py": "from .codec import LEGACY_SPECIAL_KEY, SPECIAL_FIELD_KEYS, build_special_field, parse_special_field\nfrom .name_utils import _extract_effect_name_from_special_name\n\n",
                "name_utils.py": "from .codec import LEGACY_SPECIAL_KEY, SPECIAL_FIELD_KEYS\n\n",
                "runtime_bonus.py": "from .name_utils import _special_name_matches\nfrom .slots_io import read_weapon_special_slots\n\n",
                "skills_schema.py": "from .codec import build_special_field, parse_special_field\nfrom .name_utils import _extract_effect_name_from_special_name, _split_special_name, bonus_attribute_keys, bonus_curve_for_key, weapon_special_field_keys\nfrom .slots_io import read_weapon_special_slots\n\n",
            },
            init_body='''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""武器有条件特殊能力字段。"""

from .codec import *
from .name_utils import *
from .runtime_bonus import *
from .skills_schema import *
from .slots_io import *
''',
        )

    inv_src = pkg / "calculation/damage/inverse.py"
    if not inv_src.is_file():
        print("inverse already package, skip")
    else:
        inv_pkg = pkg / "calculation/damage/inverse"
        split_into_package(
            inv_src,
            dest_pkg=inv_pkg,
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
            patches={
                "attribute.py": "from .fit_core import _find_best_params, _inverse_verbose, _inv_print, _is_decimal_data, _restore_param, _scale_data\n\n",
                "skill.py": "from .fit_core import _find_best_params, _inverse_verbose, _inv_print, _is_decimal_data, _restore_param, _scale_data\n\n",
                "api.py": "from .attribute import fit_attribute_formula, validate_attribute_formula\nfrom .skill import fit_skill_formula, fit_skill_formula_no_special, validate_skill_formula, validate_skill_formula_no_special\n\n",
            },
            init_body='''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性/技能公式反推。"""

from .api import fit_formula, validate_formula
from .attribute import fit_attribute_formula, remove_duplicates, validate_attribute_formula
from .fit_core import _find_best_params, _is_decimal_data, _scale_data
from .skill import (
    fit_skill_formula,
    fit_skill_formula_no_special,
    validate_skill_formula,
    validate_skill_formula_no_special,
)
''',
        )


def _split_soft(pkg: Path) -> None:
    # damage engine → 包
    eng_src = pkg / "calculation/damage/engine.py"
    if eng_src.is_file():
        eng_pkg = pkg / "calculation/damage/engine"
        split_into_package(
            eng_src,
            dest_pkg=eng_pkg,
            groups={
                "types.py": [
                    "CritMode",
                    "ZONE_ORDER",
                    "KNOWN_EFFECT_TYPES",
                    "DamageContext",
                    "DamageEffect",
                    "DamageResult",
                ],
                "helpers.py": [
                    "_clamp",
                    "_resolve_crit_zone",
                    "_match_scope",
                    "_collect_effects",
                ],
                "calculate.py": ["calculate_single_hit_damage"],
            },
            patches={
                "helpers.py": "from .types import KNOWN_EFFECT_TYPES, CritMode, DamageContext, DamageEffect\n\n",
                "calculate.py": "from .helpers import _collect_effects, _resolve_crit_zone\nfrom .types import CritMode, DamageContext, DamageEffect, DamageResult, ZONE_ORDER\n\n",
            },
            init_body='''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""单段伤害引擎（15 乘区链）。"""

from .calculate import calculate_single_hit_damage
from .helpers import _clamp, _collect_effects, _match_scope, _resolve_crit_zone
from .types import (
    KNOWN_EFFECT_TYPES,
    ZONE_ORDER,
    CritMode,
    DamageContext,
    DamageEffect,
    DamageResult,
)
''',
        )

    # multi_skill optimizer → 包
    ms_src = pkg / "calculation/multi_skill/optimizer.py"
    if ms_src.is_file():
        ms_pkg = pkg / "calculation/multi_skill/optimizer"
        split_into_package(
            ms_src,
            dest_pkg=ms_pkg,
            groups={
                "types.py": [
                    "SkillScenario",
                    "resolve_scenario_damage_type",
                    "MultiSkillConfig",
                    "MultiSkillScore",
                    "MultiSkillResult",
                ],
                "search.py": [
                    "_resolve_skill_counts",
                    "optimize_multi_skill_loadouts",
                    "evaluate_multi_skill_task",
                ],
            },
            patches={
                "search.py": "from .types import MultiSkillConfig, MultiSkillResult, MultiSkillScore, SkillScenario, resolve_scenario_damage_type\n\n",
            },
            init_body='''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""多技能加权总伤优化。"""

from .search import evaluate_multi_skill_task, optimize_multi_skill_loadouts
from .types import (
    MultiSkillConfig,
    MultiSkillResult,
    MultiSkillScore,
    SkillScenario,
    resolve_scenario_damage_type,
)
''',
        )

    # display_view → 包
    dv_src = pkg / "gui_design/shared/display_view.py"
    if dv_src.is_file():
        dv_pkg = pkg / "gui_design/shared/display_view"
        split_into_package(
            dv_src,
            dest_pkg=dv_pkg,
            groups={
                "render.py": ["_render_lines", "_render_placeholder"],
                "refresh.py": ["refresh_right_column_from_request"],
                "confirm.py": ["confirm_from_display_request", "confirm_selection"],
                "zone_panel.py": ["_display_zone_data"],
            },
            patches={
                "refresh.py": "from .zone_panel import _display_zone_data\n\n",
                "confirm.py": "from .render import _render_lines, _render_placeholder\nfrom .zone_panel import _display_zone_data\n\n",
            },
            init_body='''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""属性三列 CTk 渲染与确认刷新编排。"""

from .confirm import confirm_from_display_request, confirm_selection
from .refresh import refresh_right_column_from_request
from .render import _render_lines, _render_placeholder
from .zone_panel import _display_zone_data
''',
        )

    # ability_bonus：类留 zone 文件，计算函数拆到 ability_bonus_calc.py
    ab_src = pkg / "calculation/multiplicative_zones/ability_bonus_zone.py"
    ab_calc = pkg / "calculation/multiplicative_zones/ability_bonus_calc.py"
    if ab_src.is_file() and not ab_calc.is_file():
        import shutil

        tmp = pkg / "calculation/multiplicative_zones/_ab_tmp"
        split_by_symbols(
            ab_src,
            dest_dir=tmp,
            groups={
                "zone.py": ["AbilityBonusZone"],
                "calc.py": [
                    "_get_weapon_bonus",
                    "_warn_if_legacy_skill_kwargs_used",
                    "calculate_ability_bonus",
                    "calculate_ability_bonus_with_details",
                ],
            },
        )
        ab_calc.write_text((tmp / "calc.py").read_text(encoding="utf-8"), encoding="utf-8")
        ab_src.write_text(
            (tmp / "zone.py").read_text(encoding="utf-8")
            + "\nfrom .ability_bonus_calc import calculate_ability_bonus, calculate_ability_bonus_with_details\n",
            encoding="utf-8",
        )
        shutil.rmtree(tmp)
        print("  ability_bonus calc split done")

    print("soft splits done")


def _patch(path: Path, insert: str) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    end = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = max(end, node.end_lineno or node.lineno)
    lines.insert(end, "\n" + insert)
    path.write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
