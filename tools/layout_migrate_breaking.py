#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性布局迁移（方案 B：无 compat stub，全量改 import）。

用法（仓库根）：
    python tools/layout_migrate_breaking.py
"""

from __future__ import annotations

import re
import shutil
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG = REPO / "endfield_damage_calculator"

# (旧相对 PKG 路径, 新相对 PKG 路径)
MOVES: list[tuple[str, str]] = [
    # --- gui_design: layout / search_ui / shared ---
    ("gui_design/gui_layout.py", "gui_design/layout/gui_layout.py"),
    ("gui_design/label_layout.py", "gui_design/layout/label_layout.py"),
    ("gui_design/label_wrap.py", "gui_design/layout/label_wrap.py"),
    ("gui_design/panel_hints.py", "gui_design/layout/panel_hints.py"),
    ("gui_design/search_settings.py", "gui_design/search_ui/search_settings.py"),
    ("gui_design/search_results_view.py", "gui_design/search_ui/search_results_view.py"),
    ("gui_design/search_estimate_message.py", "gui_design/search_ui/search_estimate_message.py"),
    ("gui_design/search_export_paths.py", "gui_design/search_ui/search_export_paths.py"),
    ("gui_design/calc_history.py", "gui_design/shared/calc_history.py"),
    ("gui_design/calc_mode_labels.py", "gui_design/shared/calc_mode_labels.py"),
    ("gui_design/ui_preferences.py", "gui_design/shared/ui_preferences.py"),
    ("gui_design/weapon_display_text.py", "gui_design/shared/weapon_display_text.py"),
    ("gui_design/damage_visualization.py", "gui_design/shared/damage_visualization.py"),
    ("gui_design/preset_batch_compare.py", "gui_design/shared/preset_batch_compare.py"),
    ("gui_design/display_view.py", "gui_design/shared/display_view.py"),
    ("gui_design/gui_settings.py", "gui_design/shared/gui_settings.py"),
    # --- gui_design controls subdirs ---
    ("gui_design/controls/enhancement_preset.py", "gui_design/controls/enhancement/preset.py"),
    ("gui_design/controls/enhancement_section.py", "gui_design/controls/enhancement/section.py"),
    ("gui_design/controls/enhancement_dialogs.py", "gui_design/controls/enhancement/dialogs.py"),
    ("gui_design/controls/search_section.py", "gui_design/controls/search/section.py"),
    ("gui_design/controls/search_actions.py", "gui_design/controls/search/actions.py"),
    ("gui_design/controls/multi_skill_rows.py", "gui_design/controls/multi_skill/rows.py"),
    ("gui_design/controls/multi_skill_section.py", "gui_design/controls/multi_skill/section.py"),
    ("gui_design/controls/fixed_loadout_controls.py", "gui_design/controls/fixed_loadout.py"),
    # --- calculation/search subdirs ---
    ("calculation/search/plan_controller.py", "calculation/search/plan/controller.py"),
    ("calculation/search/plan_estimate.py", "calculation/search/plan/estimate.py"),
    ("calculation/search/plan_job.py", "calculation/search/plan/job.py"),
    ("calculation/search/run_runner.py", "calculation/search/run/runner.py"),
    ("calculation/search/run_session.py", "calculation/search/run/session.py"),
    ("calculation/search/run_single_skill.py", "calculation/search/run/single_skill.py"),
    ("calculation/search/run_mvp.py", "calculation/search/run/mvp.py"),
    ("calculation/search/run_parallel.py", "calculation/search/run/parallel.py"),
    ("calculation/search/run_cancel.py", "calculation/search/run/cancel.py"),
    ("calculation/search/evaluate_task.py", "calculation/search/evaluate/task.py"),
    ("calculation/search/evaluate_context.py", "calculation/search/evaluate/context.py"),
    ("calculation/search/evaluate_multi_skill.py", "calculation/search/evaluate/multi_skill.py"),
    ("calculation/search/persist_store.py", "calculation/search/persist/store.py"),
    # --- calculation domain ---
    ("calculation/damage_engine.py", "calculation/damage/engine.py"),
    ("calculation/damage_types.py", "calculation/damage/types.py"),
    ("calculation/formula.py", "calculation/damage/formula.py"),
    ("calculation/inverse.py", "calculation/damage/inverse.py"),
    ("calculation/equipment_affix.py", "calculation/equipment/affix.py"),
    ("calculation/equipment_prune.py", "calculation/equipment/prune.py"),
    ("calculation/equipment_system.py", "calculation/equipment/system.py"),
    ("calculation/loadout_optimizer.py", "calculation/loadout/optimizer.py"),
    ("calculation/loadout_slot_search.py", "calculation/loadout/slot_search.py"),
    ("calculation/loadout_attack_eval.py", "calculation/loadout/attack_eval.py"),
    ("calculation/in_memory_optimizer.py", "calculation/loadout/in_memory_optimizer.py"),
    ("calculation/skill_segments.py", "calculation/skills/segments.py"),
    ("calculation/weapon_skill_selection.py", "calculation/skills/weapon_selection.py"),
    ("calculation/physical_abnormal.py", "calculation/abnormal/physical.py"),
    ("calculation/spell_abnormal.py", "calculation/abnormal/spell.py"),
    ("calculation/spell_abnormal_params.py", "calculation/abnormal/spell_params.py"),
    ("calculation/multi_skill_optimizer.py", "calculation/multi_skill/optimizer.py"),
    ("calculation/config.py", "calculation/core/config.py"),
    ("calculation/curve_baker.py", "calculation/core/curve_baker.py"),
    ("calculation/data_generator.py", "calculation/core/data_generator.py"),
    ("calculation/top_n_tracker.py", "calculation/core/top_n_tracker.py"),
    ("calculation/parallel_evaluate.py", "calculation/core/parallel_evaluate.py"),
    ("calculation/preview_cache.py", "calculation/core/preview_cache.py"),
    ("calculation/result_cache.py", "calculation/core/result_cache.py"),
    ("calculation/result_export.py", "calculation/core/result_export.py"),
]

STUBS_TO_DELETE = [
    "gui_design/confirm_orchestrator.py",
    "gui_design/confirm_refresh.py",
    "gui_design/damage_snapshot.py",
    "gui_design/display_lines.py",
    "gui_design/display_request.py",
    "gui_design/enhancement_controls.py",
    "gui_design/fixed_loadout_controls.py",
    "gui_design/gui.py",
    "gui_design/loadout_evaluation.py",
    "gui_design/loadout_pending.py",
    "gui_design/loadout_preset.py",
    "gui_design/loadout_state.py",
    "gui_design/multi_skill_controls.py",
    "gui_design/preview_lines.py",
    "gui_design/search_controls.py",
    "gui_design/search_results_lines.py",
    "gui_design/selection_components.py",
    "gui_design/selection_panel.py",
    "gui_design/weapon_skill_selection.py",
    "calculation/search_controller.py",
    "calculation/search_estimate.py",
    "calculation/single_skill_search_job.py",
    "calculation/search_runner.py",
    "calculation/search_session.py",
    "calculation/single_skill_search_runner.py",
    "calculation/mvp_pipeline.py",
    "calculation/parallel_search.py",
    "calculation/search_cancel.py",
    "calculation/search_task_evaluator.py",
    "calculation/search_eval_context.py",
    "calculation/multi_skill_search_eval.py",
    "calculation/search_persistence.py",
    "gui_design/controls/enhancement_controls.py",
    "gui_design/controls/search_controls.py",
    "gui_design/controls/multi_skill_controls.py",
]

# 手工补充（旧模块 → 新模块），按长度降序在运行时排序
EXTRA_REPLACEMENTS: list[tuple[str, str]] = [
    ("gui_design.app.loadout_state", "gui_design.app.loadout_state"),
    ("gui_design.shell.app", "gui_design.shell.app"),
    ("calculation.search.plan.controller", "calculation.search.plan.controller"),
    ("calculation.search.plan.estimate", "calculation.search.plan.estimate"),
    ("calculation.search.plan.job", "calculation.search.plan.job"),
    ("calculation.search.run.runner", "calculation.search.run.runner"),
    ("calculation.search.run.session", "calculation.search.run.session"),
    ("calculation.search.run.single_skill", "calculation.search.run.single_skill"),
    ("calculation.search.run.mvp", "calculation.search.run.mvp"),
    ("calculation.search.run.parallel", "calculation.search.run.parallel"),
    ("calculation.search.run.cancel", "calculation.search.run.cancel"),
    ("calculation.search.evaluate.task", "calculation.search.evaluate.task"),
    ("calculation.search.evaluate.context", "calculation.search.evaluate.context"),
    ("calculation.search.evaluate.multi_skill", "calculation.search.evaluate.multi_skill"),
    ("calculation.search.persist.store", "calculation.search.persist.store"),
    ("gui_design.controls.enhancement.preset", "gui_design.controls.enhancement.preset"),
    ("gui_design.controls.enhancement.section", "gui_design.controls.enhancement.section"),
    ("gui_design.controls.enhancement.dialogs", "gui_design.controls.enhancement.dialogs"),
    ("gui_design.controls.search.section", "gui_design.controls.search.section"),
    ("gui_design.controls.search.actions", "gui_design.controls.search.actions"),
    ("gui_design.controls.multi_skill.rows", "gui_design.controls.multi_skill.rows"),
    ("gui_design.controls.multi_skill.section", "gui_design.controls.multi_skill.section"),
    ("gui_design.controls.fixed_loadout", "gui_design.controls.fixed_loadout"),
]

TEST_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("calculation/search", ("test_search_", "test_mvp_", "test_single_skill_search", "test_multi_skill_full")),
    ("calculation/loadout", ("test_loadout_", "test_fixed_loadout", "test_streaming_optimizer", "test_in_memory")),
    ("calculation/damage", ("test_damage_", "test_zone_snapshot", "test_calculation", "test_formula", "test_decimal", "test_inverse", "test_scaling_mode", "test_calc_chain")),
    ("calculation/equipment", ("test_equipment_", "test_equipment")),
    ("calculation/skills", ("test_skill_segments", "test_skill_tables", "test_damage_types")),
    ("calculation/abnormal", ("test_spell_abnormal", "test_physical")),
    ("gui_design/app", ("test_confirm_", "test_loadout_state", "test_loadout_pending", "test_loadout_preset", "test_loadout_evaluation", "test_loadout_attack")),
    ("gui_design/controls", ("test_search_controls", "test_control_dock", "test_manual_skill", "test_multi_skill_segment", "test_fixed_loadout_integration", "test_enhancement_", "test_search_error", "test_search_settings", "test_search_format", "test_frozen_search")),
    ("gui_design/presentation", ("test_display_", "test_property_display", "test_preview_", "test_single_hit", "test_single_skill_search_preview", "test_multi_skill_search_preview", "test_property_display_cache")),
    ("gui_design/shell", ("test_gui_app", "test_gui_import", "test_gui_layout", "test_window_restore", "test_weapon_panel")),
    ("gui_design/shared", ("test_calc_history", "test_calc_mode", "test_ui_preferences", "test_damage_visualization", "test_preset_batch", "test_operation_log")),
    ("data", ("test_loader", "test_game_data", "test_equipment_catalog", "test_equipment_sync", "test_pack_data")),
    ("character_weapon_equipment", ("test_weapon_special", "test_weapon_dual", "test_weapon_property", "test_add_weapon", "test_add_character", "test_weapon_panel")),
    ("tools", ("test_bwiki", "test_migrate", "test_wiki_sync", "test_github", "test_upload", "test_import_targets")),
    ("repo", ("test_repo_", "test_optional", "test_legal", "test_build_", "test_config", "test_coverage")),
    ("multi_skill", ("test_multi_skill_optimizer", "test_multi_skill_search")),
]


def _mod(path: str) -> str:
    return path.replace("/", ".").replace(".py", "")


def build_replacements() -> list[tuple[str, str]]:
    reps: dict[str, str] = {}
    for old, new in MOVES:
        reps[_mod(old)] = _mod(new)
    # stub → canonical（删除前）
    stub_map = {
        "gui_design.app.loadout_state": "gui_design.app.loadout_state",
        "gui_design.app.loadout_pending": "gui_design.app.loadout_pending",
        "gui_design.app.loadout_preset": "gui_design.app.loadout_preset",
        "gui_design.app.loadout_evaluation": "gui_design.app.loadout_evaluation",
        "gui_design.app.confirm_orchestrator": "gui_design.app.confirm_orchestrator",
        "gui_design.app.confirm_refresh": "gui_design.app.confirm_refresh",
        "gui_design.app.display_request": "gui_design.app.display_request",
        "gui_design.presentation.display_lines": "gui_design.presentation.display_lines",
        "gui_design.presentation.preview_lines": "gui_design.presentation.preview_lines",
        "gui_design.presentation.damage_snapshot": "gui_design.presentation.damage_snapshot",
        "gui_design.presentation.search_results_lines": "gui_design.presentation.search_results_lines",
        "gui_design.panels.selection_panel": "gui_design.panels.selection_panel",
        "gui_design.panels.selection_components": "gui_design.panels.selection_components",
        "gui_design.panels.weapon_skill_selection": "gui_design.panels.weapon_skill_selection",
        "gui_design.shell.app": "gui_design.shell.app",
        "gui_design.controls.enhancement": "gui_design.controls.enhancement",
        "gui_design.controls.search": "gui_design.controls.search",
        "gui_design.controls.multi_skill": "gui_design.controls.multi_skill",
        "gui_design.controls.fixed_loadout": "gui_design.controls.fixed_loadout",
        "calculation.search.plan.controller": "calculation.search.plan.controller",
        "calculation.search.plan.estimate": "calculation.search.plan.estimate",
        "calculation.search.plan.job": "calculation.search.plan.job",
        "calculation.search.run.runner": "calculation.search.run.runner",
        "calculation.search.run.session": "calculation.search.run.session",
        "calculation.search.run.single_skill": "calculation.search.run.single_skill",
        "calculation.search.run.mvp": "calculation.search.run.mvp",
        "calculation.search.run.parallel": "calculation.search.run.parallel",
        "calculation.search.run.cancel": "calculation.search.run.cancel",
        "calculation.search.evaluate.task": "calculation.search.evaluate.task",
        "calculation.search.evaluate.context": "calculation.search.evaluate.context",
        "calculation.search.evaluate.multi_skill": "calculation.search.evaluate.multi_skill",
        "calculation.search.persist.store": "calculation.search.persist.store",
        "calculation.damage.engine": "calculation.damage.engine",
        "calculation.damage.types": "calculation.damage.types",
        "calculation.equipment.affix": "calculation.equipment.affix",
        "calculation.equipment.prune": "calculation.equipment.prune",
        "calculation.equipment.system": "calculation.equipment.system",
        "calculation.loadout.optimizer": "calculation.loadout.optimizer",
        "calculation.loadout.slot_search": "calculation.loadout.slot_search",
        "calculation.loadout.attack_eval": "calculation.loadout.attack_eval",
        "calculation.loadout.in_memory_optimizer": "calculation.loadout.in_memory_optimizer",
        "calculation.skills.segments": "calculation.skills.segments",
        "calculation.skills.weapon_selection": "calculation.skills.weapon_selection",
        "calculation.abnormal.physical": "calculation.abnormal.physical",
        "calculation.abnormal.spell": "calculation.abnormal.spell",
        "calculation.abnormal.spell_params": "calculation.abnormal.spell_params",
        "calculation.multi_skill.optimizer": "calculation.multi_skill.optimizer",
        "calculation.core.preview_cache": "calculation.core.preview_cache",
        "calculation.core.result_cache": "calculation.core.result_cache",
        "calculation.core.result_export": "calculation.core.result_export",
        "calculation.core.top_n_tracker": "calculation.core.top_n_tracker",
        "calculation.core.parallel_evaluate": "calculation.core.parallel_evaluate",
        "calculation.core.config": "calculation.core.config",
        "calculation.core.curve_baker": "calculation.core.curve_baker",
        "calculation.core.data_generator": "calculation.core.data_generator",
        "calculation.damage.formula": "calculation.damage.formula",
        "calculation.damage.inverse": "calculation.damage.inverse",
    }
    reps.update(stub_map)
    for o, n in EXTRA_REPLACEMENTS:
        if o != n:
            reps[o] = n
    return sorted(reps.items(), key=lambda x: len(x[0]), reverse=True)


def apply_replacements(text: str, reps: list[tuple[str, str]]) -> str:
    for old, new in reps:
        text = text.replace(old, new)
    return text


def ensure_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    init = path / "__init__.py"
    if not init.exists():
        init.write_text(
            f'#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"""{path.name} 子包。"""\n',
            encoding="utf-8",
        )


def move_files() -> None:
    for old, new in MOVES:
        src = PKG / old
        dst = PKG / new
        if not src.exists():
            print("skip missing", old)
            continue
        ensure_init(dst.parent)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print("move", old, "->", new)


def write_control_aggregators() -> None:
  # enhancement
    (PKG / "gui_design/controls/enhancement/__init__.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工具与分享控件。"""

from .dialogs import (
    get_app_calculation_history,
    record_calculation_history,
    refresh_damage_snapshot,
    show_calculation_history_dialog,
    show_damage_dashboard_dialog,
    show_preset_compare_dialog,
)
from .preset import apply_preset_to_app, build_preset_from_app
from .section import place_enhancement_section

__all__ = [
    "apply_preset_to_app",
    "build_preset_from_app",
    "get_app_calculation_history",
    "place_enhancement_section",
    "record_calculation_history",
    "refresh_damage_snapshot",
    "show_calculation_history_dialog",
    "show_damage_dashboard_dialog",
    "show_preset_compare_dialog",
]
''',
        encoding="utf-8",
    )
    (PKG / "gui_design/controls/search/__init__.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量搜索控件。"""

from .actions import (
    compute_search_estimate_text,
    on_cancel_search,
    on_fixed_loadout_changed,
    on_run_full_search,
    on_run_mvp_search,
    prepare_single_skill_search_job,
    refresh_parallel_workers_hint,
    refresh_search_estimate,
    set_mvp_status,
    set_search_buttons_enabled,
    show_search_result_popup,
    start_search_worker,
)
from .section import build_search_job_inputs, place_search_section

__all__ = [
    "build_search_job_inputs",
    "compute_search_estimate_text",
    "on_cancel_search",
    "on_fixed_loadout_changed",
    "on_run_full_search",
    "on_run_mvp_search",
    "place_search_section",
    "prepare_single_skill_search_job",
    "refresh_parallel_workers_hint",
    "refresh_search_estimate",
    "set_mvp_status",
    "set_search_buttons_enabled",
    "show_search_result_popup",
    "start_search_worker",
]
''',
        encoding="utf-8",
    )
    (PKG / "gui_design/controls/multi_skill/__init__.py").write_text(
        '''#!/usr/bin/env python3
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
''',
        encoding="utf-8",
    )
    (PKG / "gui_design/controls/__init__.py").write_text(
        '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高级页控件子包。"""

from . import enhancement, fixed_loadout, multi_skill, search

__all__ = ["enhancement", "fixed_loadout", "multi_skill", "search"]
''',
        encoding="utf-8",
    )


def fix_relative_imports_in_file(path: Path, reps: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    new = apply_replacements(text, reps)
    # 包内相对 import 修正示例
    new = new.replace("from .fixed_loadout_controls import", "from .fixed_loadout import")
    new = new.replace("from .enhancement_preset import", "from .preset import")
    new = new.replace("from .enhancement_section import", "from .section import")
    new = new.replace("from .enhancement_dialogs import", "from .dialogs import")
    new = new.replace("from .search_section import", "from .section import")
    new = new.replace("from .search_actions import", "from .actions import")
    new = new.replace("from .multi_skill_rows import", "from .rows import")
    new = new.replace("from .multi_skill_section import", "from .section import")
  # search 子包旧相对名
    new = new.replace("from .plan_controller import", "from .controller import")
    new = new.replace("from .plan_estimate import", "from .estimate import")
    new = new.replace("from .plan_job import", "from .job import")
    new = new.replace("from .run_runner import", "from .runner import")
    new = new.replace("from .run_session import", "from .session import")
    new = new.replace("from .run_single_skill import", "from .single_skill import")
    new = new.replace("from .run_mvp import", "from .mvp import")
    new = new.replace("from .run_parallel import", "from .parallel import")
    new = new.replace("from .run_cancel import", "from .cancel import")
    new = new.replace("from .evaluate_task import", "from .task import")
    new = new.replace("from .evaluate_context import", "from .context import")
    new = new.replace("from .evaluate_multi_skill import", "from .multi_skill import")
    new = new.replace("from .persist_store import", "from .store import")
    new = new.replace("from tests.gui_fixtures import", "from tests.fixtures.gui_fixtures import")
    if new != text:
        path.write_text(new, encoding="utf-8")


def rewrite_all_py(reps: list[tuple[str, str]]) -> None:
    roots = [PKG, REPO / "tools", REPO / "docs"]
    for root in roots:
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            if any(p in py.parts for p in ("__pycache__", ".venv", "dist")):
                continue
            text = py.read_text(encoding="utf-8")
            new = apply_replacements(text, reps)
            if new != text:
                py.write_text(new, encoding="utf-8")


def delete_stubs() -> None:
    for rel in STUBS_TO_DELETE:
        p = PKG / rel
        if p.exists():
            p.unlink()
            print("deleted stub", rel)


def categorize_test(name: str) -> str:
    for cat, prefixes in TEST_RULES:
        if any(name.startswith(p) or p in name for p in prefixes):
            return cat
    return "misc"


def move_tests() -> None:
    tests = PKG / "tests"
    buckets: dict[str, list[Path]] = defaultdict(list)
    for f in sorted(tests.glob("test_*.py")):
        cat = categorize_test(f.name)
        buckets[cat].append(f)

    # 超限桶拆分
    final: dict[str, list[Path]] = {}
    for cat, files in buckets.items():
        if len(files) <= 10:
            final[cat] = files
            continue
        for i, chunk_start in enumerate(range(0, len(files), 10)):
            chunk = files[chunk_start : chunk_start + 10]
            final[f"{cat}_{i+1}"] = chunk

    fixtures = tests / "fixtures"
    fixtures.mkdir(exist_ok=True)
    for name in ("gui_fixtures.py",):
        src = tests / name
        if src.exists():
            dst = fixtures / name
            if not dst.exists():
                shutil.move(str(src), str(dst))

    for cat, files in final.items():
        dest_dir = tests.joinpath(*cat.split("/"))
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            target = dest_dir / f.name
            if f.resolve() != target.resolve():
                shutil.move(str(f), str(target))
        print(f"tests/{cat}: {len(files)} files")

    # conftest 集成/慢测路径（迁移后子目录）
    conftest = tests / "conftest.py"
    if conftest.exists():
        conftest.write_text(
            '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pytest 全局夹具：缓存清理、慢测/集成测分层、收集阶段跳过重型模块。"""

from __future__ import annotations

from pathlib import Path

import pytest

from calculation.core.result_cache import reset_global_result_cache

_INTEGRATION_FILES = frozenset(
    {
        "gui_design/presentation/test_property_display_integration.py",
        "gui_design/controls/test_enhancement_integration.py",
        "gui_design/shell/test_gui_app_integration.py",
        "gui_design/controls/test_fixed_loadout_integration.py",
    }
)

_SLOW_FILES = frozenset(
    {
        "calculation/damage/test_calculation.py",
        "calculation/damage/test_inverse_refactored.py",
        "calculation/damage/test_scaling_mode.py",
        "calculation/damage/test_decimal_scaling.py",
        "tools/test_wiki_sync.py",
    }
)


def _markexpr(config: pytest.Config) -> str:
    return (config.getoption("-m") or "").replace(" ", "").replace("_", "").lower()


def pytest_configure(config: pytest.Config) -> None:
    """带 ``-m 'not integration'`` 等时，收集阶段直接 --ignore 重型文件（避免 import CTk）。"""
    expr = _markexpr(config)
    if not expr:
        return
    tests_dir = Path(__file__).resolve().parent
    ignore: list[str] = list(config.option.ignore or [])
    if "notintegration" in expr:
        ignore.extend(str(tests_dir / name) for name in _INTEGRATION_FILES)
    if "notrealdata" in expr:
        pass
    if "notslow" in expr:
        ignore.extend(str(tests_dir / name) for name in _SLOW_FILES)
    if ignore:
        config.option.ignore = ignore


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """为慢测模块自动打 slow 标记（全量收集时生效）。"""
    for item in items:
        rel = item.path.relative_to(Path(__file__).resolve().parent).as_posix()
        if rel in _SLOW_FILES:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(autouse=True)
def _reset_global_calculation_cache() -> None:
    """每条用例前后清空全局结果缓存，避免跨测堆积大对象。"""
    reset_global_result_cache()
    yield
    reset_global_result_cache()
''',
            encoding="utf-8",
        )


def fix_test_imports_gui_fixtures(reps: list[tuple[str, str]]) -> None:
    for gf in (PKG / "tests/gui_fixtures.py", PKG / "tests/fixtures/gui_fixtures.py"):
        if gf.exists():
            fix_relative_imports_in_file(gf, reps)


def main() -> None:
    reps = build_replacements()
    print("replacements:", len(reps))
    move_files()
    write_control_aggregators()
    delete_stubs()
    rewrite_all_py(reps)
    move_tests()
    fix_test_imports_gui_fixtures(reps)
    # 包内相对 import 二次扫描
    for py in PKG.rglob("*.py"):
        if "__pycache__" not in str(py):
            fix_relative_imports_in_file(py, reps)
    print("done")


if __name__ == "__main__":
    main()
