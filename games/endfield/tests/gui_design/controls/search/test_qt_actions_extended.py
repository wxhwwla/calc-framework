# SPDX-License-Identifier: AGPL-3.0
"""_build_tree_items 物理/法术异常分支 + SearchWorker/SearchResultsDialog 测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.gui_design.controls.search.qt_actions import (
    QtSearchResultsDialog,
    SearchWorker,
    _build_tree_items,
)
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication


def _app() -> QApplication | QCoreApplication:
    inst = QApplication.instance()
    if inst is None:
        inst = QApplication([])
    return inst


class TestBuildTreeItemsPhysicalAbnormal:
    def test_with_physical_abnormal(self) -> None:
        score = LoadoutScore(
            weapon_name="物伤剑",
            final_damage=8000.0,
            loadout_names={"chest": "甲", "gloves": "手"},
            segment_breakdown={
                "战技:1": 5000.0,
                "碎甲:3": 2000.0,
                "倒地:1": 1000.0,
            },
        )
        items = _build_tree_items(
            [], [score],
            damage_metric="伤害",
            segment_counts={"战技:1": 2},
            abnormal_counts={"碎甲:3": 1, "倒地:1": 1},
            spell_abnormal_counts=None,
        )
        assert len(items) == 1
        root = items[0]
        assert root.childCount() >= 2
        child_texts = [root.child(i).text(0) for i in range(root.childCount())]
        has_weighted = any("加权合计" in t for t in child_texts)
        assert has_weighted
        has_abnormal = any("碎甲" in t for t in child_texts)
        assert has_abnormal

    def test_with_spell_abnormal(self) -> None:
        score = LoadoutScore(
            weapon_name="法伤剑",
            final_damage=7000.0,
            loadout_names={"chest": "甲", "gloves": "手"},
            segment_breakdown={
                "战技:1": 4000.0,
                "灼热异常:2": 3000.0,
            },
        )
        items = _build_tree_items(
            [], [score],
            damage_metric="伤害",
            segment_counts={"战技:1": 1},
            abnormal_counts=None,
            spell_abnormal_counts={"灼热异常:2": 1},
        )
        assert len(items) == 1
        root = items[0]
        child_texts = [root.child(i).text(0) for i in range(root.childCount())]
        has_spell = any("灼热异常" in t for t in child_texts)
        assert has_spell

    def test_with_both_abnormal_types(self) -> None:
        score = LoadoutScore(
            weapon_name="混伤剑",
            final_damage=10000.0,
            loadout_names={"chest": "甲", "gloves": "手"},
            segment_breakdown={
                "战技:1": 5000.0,
                "碎甲:3": 2500.0,
                "灼热异常:2": 2500.0,
            },
        )
        items = _build_tree_items(
            [], [score],
            damage_metric="伤害",
            segment_counts={"战技:1": 1},
            abnormal_counts={"碎甲:3": 1},
            spell_abnormal_counts={"灼热异常:2": 1},
        )
        assert len(items) == 1
        root = items[0]
        child_texts = [root.child(i).text(0) for i in range(root.childCount())]
        assert any("碎甲" in t for t in child_texts)
        assert any("灼热异常" in t for t in child_texts)
        assert any("加权合计" in t for t in child_texts)

    def test_abnormal_only_no_skill_segments(self) -> None:
        score = LoadoutScore(
            weapon_name="纯异常",
            final_damage=3000.0,
            loadout_names={},
            segment_breakdown={
                "击飞:1": 3000.0,
            },
        )
        items = _build_tree_items(
            [], [score],
            damage_metric="伤害",
            segment_counts={},
            abnormal_counts={"击飞:1": 1},
            spell_abnormal_counts=None,
        )
        assert len(items) == 1
        root = items[0]
        child_texts = [root.child(i).text(0) for i in range(root.childCount())]
        has_abnormal = any("击飞" in t for t in child_texts)
        assert has_abnormal


class TestBuildTreeItemsSingleSkillTypeTotal:
    def test_single_skill_type_total_no_parentheses(self) -> None:
        score = LoadoutScore(
            weapon_name="单系剑",
            final_damage=5000.0,
            loadout_names={},
            segment_breakdown={"战技:1": 5000.0},
        )
        items = _build_tree_items(
            [], [score],
            damage_metric="伤害",
            segment_counts={"战技:1": 1},
            abnormal_counts=None,
            spell_abnormal_counts=None,
        )
        assert len(items) == 1
        root = items[0]
        child_texts = [root.child(i).text(0) for i in range(root.childCount())]
        weighted_lines = [t for t in child_texts if "加权合计" in t]
        assert len(weighted_lines) == 1
        assert "（" not in weighted_lines[0]


class TestQtSearchResultsDialog:
    def test_create_with_no_results(self) -> None:
        _app()
        dialog = QtSearchResultsDialog(
            big_font=MagicMock(),
            small_font=MagicMock(),
            title="测试",
            lines=["无结果"],
        )
        assert dialog.windowTitle() == "测试"
        dialog.accept()


class TestSearchWorkerInit:
    def test_worker_attributes(self) -> None:
        from games.endfield.calc.search.plan.job import SingleSkillSearchJob
        from games.endfield.calc.search.run.cancel import SearchCancelToken


        job = MagicMock(spec=SingleSkillSearchJob)
        cancel = SearchCancelToken()
        worker = SearchWorker(
            job, mode_label="测试", export_root=Path("/tmp"),
            top_n_choice="10", workers_choice="自动",
            status_prefix="测试", cancel_token=cancel,
        )
        assert worker._mode_label == "测试"
        assert worker._top_n == 10
