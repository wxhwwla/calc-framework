#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地 DAG 配置与适配器子包。

- ``config``：DAG JSON 生成脚本（generate / save_dag）
- ``adapter``：将 DAG 引擎接入现有 zone_snapshot 计算链

迁移自 ``multiplicative_zones.dag``。
"""

from .adapter import (
    build_dag_context,
    compute_snapshot_with_dag,
    evaluate_attack_chain_via_dag,
)

# ── 优先使用 Rust 加速版 evaluate_search_damage ──
try:
    from extensions.rust_search.python.rust_bridge import evaluate_search_damage
except ImportError:
    from .search_evaluate import evaluate_search_damage
from .search_evaluate import DamageEvalResult

__all__ = [
    "DamageEvalResult",
    "build_dag_context",
    "compute_snapshot_with_dag",
    "evaluate_attack_chain_via_dag",
    "evaluate_search_damage",
]
