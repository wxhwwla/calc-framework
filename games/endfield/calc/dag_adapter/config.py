#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""终末地完整伤害公式 DAG JSON 配置文件生成脚本。

迁移自 ``multiplicative_zones.dag.config``。

输出文件位于 ``framework/src/calc_framework/configs/endfield_full.dag.json``。

6 块架构（ADR-0011 §3.2）：
- ``ability_bonus``（属性块）：能力值加成 = main_flat×(1+main_pct/100)×0.005 + ...
- ``final_attack``（攻击力块）：最终攻击力 = (char+weapon)×(1+atk_bonus)+add+equip×(1+ability_bonus)
- ``crit_zone``（暴击块）：暴击区 = 1 + 暴击率×(暴击伤害-1)
- ``base_damage_block``（基础伤害块）：final_attack×skill_mult×crit_zone
- ``buff_debuff_block``（增益/减益块）：7 个乘区连乘
- ``environment_block``（环境乘区块）：防御减伤 + 5 个环境乘区连乘

主图：6 个 CallNode 块通过链式绑定串联，展开后等价于原 70 节点扁平 DAG。

P2-07 拆分：变量表迁至 ``config_variables.py``，节点表迁至 ``config_nodes.py``，
主图构建迁至 ``config_master_graph.py``；本模块保留路径初始化与生成/保存入口。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from calc_framework.logging import get_logger

_logger = get_logger(__name__)

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from calc_framework.dag.schema import DAGGraph
from calc_framework.dag.serializer import dag_to_dict

from .config_master_graph import _make_master_graph

__all__ = ["OUTPUT_PATH", "_make_master_graph", "generate", "main", "save_dag"]

OUTPUT_PATH = _SRC_DIR / "calc_framework" / "configs" / "endfield_full.dag.json"


def generate() -> DAGGraph:
    """生成完整终末地 DAG 公式图。"""
    return _make_master_graph()


def save_dag(graph: DAGGraph, path: Path | None = None) -> Path:
    """序列化 DAG 到 JSON 文件。"""
    target = path or OUTPUT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    d = dag_to_dict(graph)
    with target.open("w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return target


def main() -> None:
    """CLI 入口：生成并保存 DAG JSON。"""
    g = generate()
    out = save_dag(g)
    _logger.info("已生成: %s", out)
    _logger.info("  子图: %s", list(g.subgraphs.keys()))
    _logger.info("  节点: %d 个", len(g.nodes))
    _logger.info("  输出: %s", list(g.outputs.keys()))


if __name__ == "__main__":
    main()
