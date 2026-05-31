#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 配置与适配器子包。

- ``config``：DAG JSON 生成脚本（generate / save_dag）
- ``adapter``：将 DAG 引擎接入现有 zone_snapshot 计算链

迁移自 ``multiplicative_zones.dag``。
"""

from calc_engine.endfield.calc.dag_adapter.adapter import (
    build_dag_context,
    compute_snapshot_with_dag,
    evaluate_attack_chain_via_dag,
)

__all__ = [
    "build_dag_context",
    "compute_snapshot_with_dag",
    "evaluate_attack_chain_via_dag",
]
