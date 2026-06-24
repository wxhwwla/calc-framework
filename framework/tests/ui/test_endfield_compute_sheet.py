# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 ComputeSheet 端到端集成测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from calc_framework.dag.service import DAGService
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

_FRAMEWORK_DIR = Path(__file__).resolve().parents[2]

_DAG_PATH = _FRAMEWORK_DIR / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"

_LAYOUT_PATH = _FRAMEWORK_DIR / "adapters" / "endfield" / "ui" / "layout.json"


@pytest.fixture(scope="module")
def endfield_dag_service():
    return DAGService.from_file(_DAG_PATH)


@pytest.fixture(scope="module")
def endfield_layout():
    return load_layout_json(_LAYOUT_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def base_context():
    return {
        "character": {"基础攻击": 100, "主能力": "力量", "副能力": "敏捷"},
        "weapon": {"基础攻击": 50, "攻击力+": 0.0, "附加攻击力+": 0.0},
        "equipment": {"攻击力平值": 0.0},
        "computed": {
            "主能力平值加算": 0.0,
            "副能力平值加算": 0.0,
            "主能力百分比": 0.0,
            "副能力百分比": 0.0,
            "最终攻击力": 0.0,
            "技能倍率": 1.5,
            "暴击区": 1.0,
            "伤害加成": 1.0,
            "伤害减免": 1.0,
            "增幅": 1.0,
            "虚弱": 1.0,
            "庇护": 1.0,
            "脆弱": 1.0,
            "易伤": 1.0,
            "防御": 0.5,
            "失衡易伤": 1.0,
            "抗性": 1.0,
            "非主控减伤": 1.0,
            "连击增伤": 1.0,
            "特殊乘区": 1.0,
        },
    }


@pytest.fixture(scope="module")
def qapp():
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()

    if app is None:
        app = QApplication(sys.argv)

    yield app


class TestEndfieldComputeSheet:
    def test_layout_loads(self, endfield_layout):
        assert endfield_layout.name == "终末地计算表"

        assert len(endfield_layout.sections) == 13

    def test_compute_sheet_builds(self, endfield_dag_service, endfield_layout, base_context, qapp):
        sheet = ComputeSheet(
            dag_service=endfield_dag_service,
            layout=endfield_layout,
            variables=endfield_dag_service.dag.variables,
            base_context=base_context,
        )

        w = sheet.widget

        assert w is not None

    def test_evaluates_attack_chain(self, endfield_dag_service, endfield_layout, base_context, qapp):
        sheet = ComputeSheet(
            dag_service=endfield_dag_service,
            layout=endfield_layout,
            variables=endfield_dag_service.dag.variables,
            base_context=base_context,
        )

        sheet.widget

        result = sheet.evaluate()

        assert "最终攻击力" in result.outputs

        assert result.outputs["最终攻击力"] > 0

    def test_full_damage_chain(self, endfield_dag_service, endfield_layout, base_context, qapp):
        ctx = dict(base_context)

        result1 = endfield_dag_service.evaluate(ctx)

        final_atk = result1.outputs["最终攻击力"]

        ctx["computed"]["最终攻击力"] = final_atk

        ctx["computed"]["技能倍率"] = 1.5

        sheet = ComputeSheet(
            dag_service=endfield_dag_service,
            layout=endfield_layout,
            variables=endfield_dag_service.dag.variables,
            base_context=ctx,
        )

        sheet.widget

        result2 = sheet.evaluate()

        assert result2.outputs["最终伤害"] > 0
