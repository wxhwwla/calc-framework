# SPDX-License-Identifier: AGPL-3.0
"""终末地 15 乘区 DAG 完整性审查脚本。

验证 ``endfield_full.dag.json`` 是否覆盖全部 15 个伤害乘区。"""

from __future__ import annotations

import json
from pathlib import Path

# Python 代码中的 15 乘区顺序（from games.endfield.calc.damage.engine.types）
ZONE_ORDER_PYTHON = [
    "基础伤害区",
    "暴击区",
    "伤害加成区",
    "伤害减免区",
    "增幅区",
    "虚弱区",
    "庇护区",
    "脆弱区",
    "易伤区",
    "防御区",
    "失衡易伤区",
    "抗性区",
    "非主控减伤区",
    "连击增伤区",
    "特殊乘区",
]

# DAG config.py 中定义的 zones 列表（_make_single_hit_damage_subgraph）
DAG_ZONE_PARAMS = [
    "final_attack",
    "skill_multiplier",
    "crit_zone",
    "damage_bonus_zone",
    "damage_reduction",
    "amplification",
    "weakness",
    "shelter",
    "fragile",
    "vulnerability",
    "defense_zone",
    "imbalance_zone",
    "resistance_zone",
    "non_control_reduction",
    "combo_bonus",
    "special_zone",
]

ZONE_MAP = [
    ("final_attack + skill_multiplier", "基础伤害区"),
    ("crit_zone", "暴击区"),
    ("damage_bonus_zone", "伤害加成区"),
    ("damage_reduction", "伤害减免区"),
    ("amplification", "增幅区"),
    ("weakness", "虚弱区"),
    ("shelter", "庇护区"),
    ("fragile", "脆弱区"),
    ("vulnerability", "易伤区"),
    ("defense_zone", "防御区"),
    ("imbalance_zone", "失衡易伤区"),
    ("resistance_zone", "抗性区"),
    ("non_control_reduction", "非主控减伤区"),
    ("combo_bonus", "连击增伤区"),
    ("special_zone", "特殊乘区"),
]

DAG_PATH = Path(__file__).resolve().parents[2] / "src" / "calc_framework" / "configs" / "endfield_full.dag.json"


def review() -> list[str]:
    findings: list[str] = []

    if not DAG_PATH.is_file():
        findings.append(f"❌ DAG 文件不存在: {DAG_PATH}")
        return findings
    findings.append(f"✅ DAG 文件存在: {DAG_PATH}")

    raw = json.loads(DAG_PATH.read_text(encoding="utf-8"))
    findings.append(f"   schema_version: {raw.get('schema_version', '?')}")
    findings.append(f"   name: {raw.get('name', '?')}")

    # 检查 variables 中的乘区相关变量
    variables = raw.get("variables", {})
    zone_vars = [k for k in variables if any(z in k for z in ["defense", "resistance", "crit_", "damage", "imbalance", "combo", "special", "amplif", "weakness", "shelter", "fragile", "vulnerability", "non_control"])]
    findings.append(f"   乘区相关变量数: {len(zone_vars)}")

    # 检查子图中是否有 single_hit_damage
    subgraphs = raw.get("subgraphs", {})
    missing: list[str] = []
    shd_params: list[str] = []
    if "single_hit_damage" in subgraphs:
        findings.append("✅ 子图 'single_hit_damage' 存在")
        shd = subgraphs["single_hit_damage"]
        shd_params = list(shd.get("parameters", {}).keys())
        missing = [p for p in DAG_ZONE_PARAMS if p not in shd_params]
        if missing:
            findings.append(f"❌ 缺少参数: {missing}")
        else:
            findings.append(f"✅ 全部 {len(DAG_ZONE_PARAMS)} 个乘区参数已声明")
        findings.append(f"   子图节点数: {len(shd.get('nodes', {}))}")
        findings.append(f"   子图输出: {list(shd.get('outputs', {}).keys())}")
    else:
        findings.append("❌ 缺少 'single_hit_damage' 子图")

    # 检查主图节点数
    nodes = raw.get("nodes", {})
    findings.append(f"   主图节点数: {len(nodes)}")

    # 输出映射表
    findings.append("\n📊 15 乘区映射表：")
    findings.append(f"   {'DAG 参数名':<28} {'←→'}  {'Python 乘区名':<16}")
    findings.append(f"   {'-'*28}   {'-'*16}")
    for dag_param, py_zone in ZONE_MAP:
        ok = dag_param in shd_params if shd_params else False
        mark = "✅" if ok else "❌"
        findings.append(f"   {dag_param:<28} {mark} {py_zone:<16}")

    # 主图 output
    outputs = raw.get("outputs", {})
    if "最终伤害" in outputs:
        findings.append("\n✅ 主图输出 '最终伤害' 存在")
    else:
        findings.append("\n❌ 缺少 '最终伤害' 输出")

    # 结论
    all_ok = len(missing) == 0
    findings.append("\n📋 结论：15 乘区 DAG 完整性审查通过 ✅" if all_ok else "\n📋 结论：发现缺口 ❌")

    return findings


if __name__ == "__main__":
    for line in review():
        print(line)
