# SPDX-License-Identifier: AGPL-3.0
"""端到端集成测试 — 使用真实解析 JSON 数据验证 DAG 计算正确性。

手动验证值：

  W（★6 狙击，物理）：
    ATK = 568 + 100(信赖) + 35(潜能) = 703
    物理 = max(703-200, 703*0.05) = max(503, 35.15) = 503.0

  阿米娅（★5 术师，法术）：
    ATK = 390 + 70(信赖) + 30(潜能) = 490
    法术 = 490 * (1-50/100) = 245.0
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from games.arknights.calc.dag_adapter import compute_snapshot_with_dag


def _load(name: str, parsed_dir: Path) -> dict:
    path = parsed_dir / f"{name}.json"
    if not path.is_file():
        pytest.skip(f"数据文件不存在: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


class TestWithRealData:
    @pytest.mark.integration
    @pytest.mark.real_data
    def test_w_physical(self, parsed_dir: Path) -> None:
        op = _load("W", parsed_dir)
        result = compute_snapshot_with_dag(op)
        assert result.outputs["最终攻击力"] == 703.0
        assert result.outputs["物理伤害"] == 503.0

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_amiya_magical(self, parsed_dir: Path) -> None:
        op = _load("阿米娅", parsed_dir)
        result = compute_snapshot_with_dag(op)
        assert result.outputs["最终攻击力"] == 490.0
        assert result.outputs["法术伤害"] == 245.0

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_operator_has_4_outputs(self, parsed_dir: Path) -> None:
        op = _load("W", parsed_dir)
        result = compute_snapshot_with_dag(op)
        assert len(result.outputs) == 4

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_healer_zero_attack_has_min_damage(self, parsed_dir: Path) -> None:
        op = _load("12F", parsed_dir)
        if op is None:
            pytest.skip("12F 数据不存在")
        result = compute_snapshot_with_dag(op, enemy_def=5000.0)
        assert result.outputs["物理伤害"] >= 0.0

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_true_damage_operator(self, parsed_dir: Path) -> None:
        op = _load("阿米娅", parsed_dir)
        result = compute_snapshot_with_dag(op, skill_multiplier=1.0)
        assert result.outputs["真伤伤害"] == 490.0
