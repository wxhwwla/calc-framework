# SPDX-License-Identifier: AGPL-3.0
"""AK 成长参数批量压缩与段曲线解析测试。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from calc_framework.inverse.curve import GROWTH_PARAM_SEGMENTS_KEY

from games.arknights.calc.dag_adapter.loader import ArknightsContextLoader
from games.arknights.calc.inverse.stats import resolve_stats_from_segments
from tools.compact_arknights_operators import compact_operator, compact_parsed_dir


@pytest.fixture
def exusiai_milestones() -> dict:
    return {
        "名称": "能天使",
        "星级": 6,
        "基础属性": {"hp": 1016, "atk": 305, "def": 150, "res": 0},
        "属性里程碑": {
            "hp": {"e0_lv1": 711, "e0_max": 1016, "e1_max": 1338, "e2_max": 1673},
            "atk": {"e0_lv1": 217, "e0_max": 305, "e1_max": 437, "e2_max": 540},
            "def": {"e0_lv1": 80, "e0_max": 150, "e1_max": 200, "e2_max": 250},
            "res": {"e0_lv1": 0, "e0_max": 0, "e1_max": 0, "e2_max": 0},
        },
        "技能": [
            {
                "名称": "过载模式",
                "SP消耗": [50, 48, 46, 44, 42, 40, 38, 36, 34, 30],
            }
        ],
    }


def test_compact_operator_writes_growth_params(exusiai_milestones: dict) -> None:
    out, warns = compact_operator(exusiai_milestones, max_error=0.05)
    assert "成长参数" in out
    segments = out["成长参数"].get(GROWTH_PARAM_SEGMENTS_KEY, [])
    assert any(s["key"] == "e0.hp" for s in segments)
    assert "段曲线" not in out
    materialized = resolve_stats_from_segments(out, elite=2)
    assert materialized["atk"] == pytest.approx(540, abs=1)


def test_compact_parsed_dir_dry_run(exusiai_milestones: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        parsed = Path(tmp)
        path = parsed / "能天使.json"
        path.write_text(json.dumps(exusiai_milestones, ensure_ascii=False), encoding="utf-8")
        stats = compact_parsed_dir(parsed, apply=False)
        assert stats["success"]
        assert stats["total"] == 1
        assert stats["compacted"] == 1
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "成长参数" not in raw


def test_compact_parsed_dir_apply(exusiai_milestones: dict) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        parsed = Path(tmp)
        path = parsed / "能天使.json"
        path.write_text(json.dumps(exusiai_milestones, ensure_ascii=False), encoding="utf-8")
        stats = compact_parsed_dir(parsed, apply=True)
        assert stats["compacted"] == 1
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "成长参数" in raw
        assert (parsed / "operators.json").is_file()


def test_loader_uses_segment_stats(exusiai_milestones: dict) -> None:
    compacted, _ = compact_operator(exusiai_milestones)
    loader = ArknightsContextLoader()
    ctx_default = loader.build_context(operator=compacted)
    ctx_e0 = loader.build_context(operator=compacted, elite=0, operator_level=1)
    assert ctx_default["character"]["攻击力"] == pytest.approx(540, abs=1)
    assert ctx_e0["character"]["攻击力"] == pytest.approx(217, abs=1)
