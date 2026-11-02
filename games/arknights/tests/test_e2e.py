# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""端到端集成测试 — 使用真实解析 JSON 数据验证 DAG 计算正确性。

手动验证值（默认精英二满级，skill_parser 已启用并自动解析技能倍率）：

  W（★6 狙击，技能1「红桃K」Lv.7）：
    ATK = 912(精英二满级) + 100(信赖) + 35(潜能) = 1047
    红桃K 倍率 = 3.1x（Lv.7 时相当于攻击力310%）
    物理 = max(1047*3.1 - 200, 1047*3.1*0.05) = max(3045.7, 162.285) = 3045.7

  阿米娅（★5 术师，技能1「战术咏唱·γ型」Lv.7）：
    ATK = 612(精英二满级) + 70(信赖) + 30(潜能) = 712
    战术咏唱·γ型 = 攻速技能，倍率=1.0
    法术 = 712 * (1-50/100) = 356.0

  指定精英/等级时直接读取该段曲线：
     W 精英0 Lv1 ATK=397，精英1满级 ATK=711
     阿米娅 精英0 Lv1 ATK=276，精英1满级 ATK=514
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
        assert result.outputs["最终攻击力"] == 1047.0
        assert result.outputs["物理伤害"] == pytest.approx(3045.7, abs=0.1)

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_w_elite0_level1(self, parsed_dir: Path) -> None:
        op = _load("W", parsed_dir)
        result = compute_snapshot_with_dag(op, elite=0, operator_level=1)
        assert result.outputs["最终攻击力"] == 532.0
        assert result.outputs["物理伤害"] == pytest.approx(1449.2, abs=0.1)

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_w_elite1_max_level(self, parsed_dir: Path) -> None:
        op = _load("W", parsed_dir)
        result = compute_snapshot_with_dag(op, elite=1)
        assert result.outputs["最终攻击力"] == 846.0
        assert result.outputs["物理伤害"] == pytest.approx(2422.6, abs=0.1)

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_amiya_magical(self, parsed_dir: Path) -> None:
        op = _load("阿米娅", parsed_dir)
        result = compute_snapshot_with_dag(op)
        assert result.outputs["最终攻击力"] == 712.0
        assert result.outputs["法术伤害"] == 356.0

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_amiya_elite0_level1(self, parsed_dir: Path) -> None:
        op = _load("阿米娅", parsed_dir)
        result = compute_snapshot_with_dag(op, elite=0, operator_level=1)
        assert result.outputs["最终攻击力"] == 376.0
        assert result.outputs["法术伤害"] == 188.0

    @pytest.mark.integration
    @pytest.mark.real_data
    def test_amiya_elite1_max_level(self, parsed_dir: Path) -> None:
        op = _load("阿米娅", parsed_dir)
        result = compute_snapshot_with_dag(op, elite=1)
        assert result.outputs["最终攻击力"] == 614.0
        assert result.outputs["法术伤害"] == 307.0

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
        assert result.outputs["真伤伤害"] == 712.0
