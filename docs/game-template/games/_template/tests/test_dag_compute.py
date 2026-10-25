# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""测试 DAG 计算基本流程 — 验证 compute_snapshot_with_dag 能否正常调用。

TODO:
  - 准备好适配器的 DAG 公式文件后启用这些测试
  - 根据实际游戏 DAG 的输出变量名调整键名断言
"""

from __future__ import annotations

from games._template.calc.dag_adapter import compute_snapshot_with_dag


class TestComputeSnapshot:
    def test_returns_dict(self, sample_character: dict) -> None:
        result = compute_snapshot_with_dag(sample_character)
        assert isinstance(result, dict)

    def test_outputs_have_expected_keys(self, sample_character: dict) -> None:
        """TODO: 替换为实际的 DAG 输出变量名。"""
        _result = compute_snapshot_with_dag(sample_character)
        # assert "最终攻击力" in result
        # assert "物理伤害" in result
        pass  # 移除 pass 并启用上述断言

    def test_outputs_are_floats(self, sample_character: dict) -> None:
        result = compute_snapshot_with_dag(sample_character)
        for val in result.values():
            assert isinstance(val, float), f"Expected float, got {type(val)}: {val}"

    def test_with_skill_multiplier(self, sample_character: dict) -> None:
        result = compute_snapshot_with_dag(sample_character, skill_multiplier=2.0)
        assert isinstance(result, dict)

    def test_with_custom_enemy_params(self, sample_character: dict) -> None:
        result = compute_snapshot_with_dag(
            sample_character,
            enemy_def=500.0,
            enemy_res=30.0,
        )
        assert isinstance(result, dict)
