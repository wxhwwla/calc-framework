# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""GeneratorEngine — 自动 layout 分页规则测试。"""

from __future__ import annotations

import json
from pathlib import Path

from tools.generator.engine import GeneratorEngine


def test_auto_layout_assigns_calculation_and_breakdown_tabs(tmp_path: Path) -> None:
    """自动 layout 应把输入与主输出放「计算」，其余输出放「乘区明细」。"""
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "atk", "source": "user_input", "default": 100}],
        formula_steps=[
            {"id": "total", "op": "*", "lhs": "atk", "rhs": "2"},
            {"id": "zone", "op": "*", "lhs": "atk", "rhs": "3"},
        ],
        outputs=[
            {"name": "total", "node": "total", "label": "总伤害"},
            {"name": "zone", "node": "zone", "label": "乘区", "is_primary": False},
        ],
    )

    sections = json.loads(files["ui/layout.json"])["sections"]

    assert [section.get("tab") for section in sections] == ["计算", "计算", "乘区明细"]


def test_auto_layout_keeps_single_page_without_detail_outputs(tmp_path: Path) -> None:
    """没有非主输出时保持单页，不生成空「乘区明细」页。"""
    engine = GeneratorEngine(adapters_dir=tmp_path)
    files = engine.generate(
        None,
        "Demo",
        variables=[{"name": "atk", "source": "user_input", "default": 100}],
        formula_steps=[{"id": "total", "op": "*", "lhs": "atk", "rhs": "2"}],
        outputs=[{"name": "total", "node": "total", "label": "总伤害"}],
    )

    sections = json.loads(files["ui/layout.json"])["sections"]

    assert all("tab" not in section for section in sections)
