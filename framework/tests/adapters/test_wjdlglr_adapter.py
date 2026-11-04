#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
# ruff: noqa: E402

"""无尽的拉格朗日适配器集成测试 — 验证 MCP 生成的武器输出计算器可加载、可求值。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_ADAPTER_DIR = Path(__file__).resolve().parents[2] / "adapters" / "wjdlglr"

_FRAMEWORK_SRC = Path(__file__).resolve().parents[2] / "src"

if str(_FRAMEWORK_SRC) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_SRC))


from calc_framework.config.adapter import AdapterPackage


@pytest.fixture()
def adapter_pkg() -> AdapterPackage:
    return AdapterPackage(str(_ADAPTER_DIR))


def _context(**overrides: float) -> dict[str, dict[str, float]]:
    base = {
        "atk": 65.0,
        "attack_count": 4.0,
        "hit_rate": 0.9,
        "mounts": 3.0,
        "cooldown": 7.0,
        "duration": 16.0,
        "outbound": 0.0,
        "inbound": 0.0,
        "enemy_hp": 10000.0,
        "firepower": 851.0,
    }
    base.update(overrides)
    return {"user_input": base}


class TestAdapterLoads:
    """适配包应能被框架正常加载。"""

    def test_meta_declares_game(self, adapter_pkg: AdapterPackage) -> None:
        assert adapter_pkg.meta["name"] == "无尽的拉格朗日 武器输出计算器"
        assert adapter_pkg.meta["game"] == "无尽的拉格朗日"
        assert adapter_pkg.meta["schema_version"] == "dag-v1"

    def test_dag_exposes_expected_outputs(self, adapter_pkg: AdapterPackage) -> None:
        outputs = set(adapter_pkg.dag_service.dag.outputs)
        assert {"齐射总伤害", "攻击周期(秒)", "理论DPS", "击杀时间(秒)"} <= outputs

    def test_layout_file_exists(self) -> None:
        layout = json.loads((_ADAPTER_DIR / "ui" / "layout.json").read_text(encoding="utf-8"))
        assert layout["schema_version"] == "ui-v1"
        assert any(section["type"] == "outputs" for section in layout["sections"])


class TestEvaluation:
    """公式口径：周期 = 冷却 + 持续时间 + 去程 + 回程。"""

    def test_at021_weapon_outputs(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context())
        assert result.outputs["齐射总伤害"] == pytest.approx(702.0)
        assert result.outputs["攻击周期(秒)"] == pytest.approx(23.0)
        assert result.outputs["理论DPS"] == pytest.approx(702.0 / 23.0)
        assert result.outputs["击杀时间(秒)"] == pytest.approx(10000.0 * 23.0 / 702.0)
        assert result.outputs["官方火力击杀时间(秒)"] == pytest.approx(10000.0 / 851.0)

    def test_zero_cycle_does_not_crash(self, adapter_pkg: AdapterPackage) -> None:
        result = adapter_pkg.dag_service.evaluate(_context(cooldown=0.0, duration=0.0, outbound=0.0, inbound=0.0))
        assert result.outputs["理论DPS"] == pytest.approx(702000.0)
