#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成终末地乘区包 ZIP 文件，用于测试。"""

import json
import zipfile
from pathlib import Path

# 定义 15 个乘区子图（使用 graph_editor 期望的格式）
ZONE_GRAPHS = {
    "01_基础攻击力": {
        "schema_version": "calc-graph-v1",
        "name": "基础攻击力",
        "description": "角色基础攻击力",
        "external_variables": {},
        "nodes": [
            {"id": "base_atk", "type": "user_input", "label": "基础攻击力", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "基础攻击力", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "base_atk", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "02_攻击力百分比": {
        "schema_version": "calc-graph-v1",
        "name": "攻击力百分比",
        "description": "攻击力百分比加成",
        "external_variables": {},
        "nodes": [
            {"id": "atk_pct", "type": "user_input", "label": "攻击力%", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "攻击力百分比", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "atk_pct", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "03_最终攻击力": {
        "schema_version": "calc-graph-v1",
        "name": "最终攻击力",
        "description": "最终攻击力 = 基础攻击力 + 攻击力加成",
        "external_variables": {},
        "nodes": [
            {"id": "base", "type": "user_input", "label": "基础攻击力", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "flat", "type": "user_input", "label": "攻击力+", "config": {}, "position": {"x": 0, "y": 80}},
            {"id": "calc", "type": "binary", "op": "+", "label": "计算", "config": {}, "position": {"x": 200, "y": 40}},
            {"id": "out", "type": "output", "label": "最终攻击力", "config": {}, "position": {"x": 400, "y": 40}},
        ],
        "edges": [
            {"id": "e1", "from_node": "base", "from_port": 0, "to_node": "calc", "to_port": 0},
            {"id": "e2", "from_node": "flat", "from_port": 0, "to_node": "calc", "to_port": 1},
            {"id": "e3", "from_node": "calc", "from_port": 0, "to_node": "out", "to_port": 0},
        ],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "04_技能倍率": {
        "schema_version": "calc-graph-v1",
        "name": "技能倍率",
        "description": "技能倍率",
        "external_variables": {},
        "nodes": [
            {"id": "skill_mult", "type": "user_input", "label": "技能倍率", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "技能倍率", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "skill_mult", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "05_增伤区": {
        "schema_version": "calc-graph-v1",
        "name": "增伤区",
        "description": "增伤百分比",
        "external_variables": {},
        "nodes": [
            {"id": "dmg_bonus", "type": "user_input", "label": "增伤%", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "增伤区", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "dmg_bonus", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "06_暴击率": {
        "schema_version": "calc-graph-v1",
        "name": "暴击率",
        "description": "暴击率",
        "external_variables": {},
        "nodes": [
            {"id": "crit_rate", "type": "user_input", "label": "暴击率", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "暴击率", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "crit_rate", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "07_暴击伤害": {
        "schema_version": "calc-graph-v1",
        "name": "暴击伤害",
        "description": "暴击伤害",
        "external_variables": {},
        "nodes": [
            {"id": "crit_dmg", "type": "user_input", "label": "暴击伤害", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "暴击伤害", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "crit_dmg", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "08_防御区": {
        "schema_version": "calc-graph-v1",
        "name": "防御区",
        "description": "防御减伤",
        "external_variables": {},
        "nodes": [
            {"id": "enemy_def", "type": "user_input", "label": "敌人防御", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "char_level", "type": "user_input", "label": "角色等级", "config": {}, "position": {"x": 0, "y": 80}},
            {"id": "out", "type": "output", "label": "防御区", "config": {}, "position": {"x": 200, "y": 40}},
        ],
        "edges": [
            {"id": "e1", "from_node": "enemy_def", "from_port": 0, "to_node": "out", "to_port": 0},
            {"id": "e2", "from_node": "char_level", "from_port": 0, "to_node": "out", "to_port": 1},
        ],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "09_抗性区": {
        "schema_version": "calc-graph-v1",
        "name": "抗性区",
        "description": "元素抗性",
        "external_variables": {},
        "nodes": [
            {"id": "res", "type": "user_input", "label": "敌人抗性", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "抗性区", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "res", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "10_减防区": {
        "schema_version": "calc-graph-v1",
        "name": "减防区",
        "description": "减防百分比",
        "external_variables": {},
        "nodes": [
            {"id": "def_shred", "type": "user_input", "label": "减防%", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "减防区", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "def_shred", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "11_减抗区": {
        "schema_version": "calc-graph-v1",
        "name": "减抗区",
        "description": "减抗百分比",
        "external_variables": {},
        "nodes": [
            {"id": "res_shred", "type": "user_input", "label": "减抗%", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "减抗区", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "res_shred", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "12_蒸发融化": {
        "schema_version": "calc-graph-v1",
        "name": "蒸发融化",
        "description": "蒸发融化反应倍率",
        "external_variables": {},
        "nodes": [
            {"id": "reaction", "type": "user_input", "label": "反应倍率", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "蒸发融化", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "reaction", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "13_超导扩散": {
        "schema_version": "calc-graph-v1",
        "name": "超导扩散",
        "description": "剧变反应",
        "external_variables": {},
        "nodes": [
            {"id": "transformative", "type": "user_input", "label": "剧变反应", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "超导扩散", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "transformative", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "14_护盾强效": {
        "schema_version": "calc-graph-v1",
        "name": "护盾强效",
        "description": "护盾强效",
        "external_variables": {},
        "nodes": [
            {"id": "shield", "type": "user_input", "label": "护盾强效", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "护盾强效", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "shield", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
    "15_治疗加成": {
        "schema_version": "calc-graph-v1",
        "name": "治疗加成",
        "description": "治疗加成",
        "external_variables": {},
        "nodes": [
            {"id": "heal", "type": "user_input", "label": "治疗加成", "config": {}, "position": {"x": 0, "y": 0}},
            {"id": "out", "type": "output", "label": "治疗加成", "config": {}, "position": {"x": 200, "y": 0}},
        ],
        "edges": [{"id": "e1", "from_node": "heal", "from_port": 0, "to_node": "out", "to_port": 0}],
        "layout": {"sections": [{"id": "main", "title": "输出", "output_nodes": ["out"], "columns": 1}]},
    },
}


def build_chain_graph() -> dict:
    """构建 15 乘区链图（串联所有乘区）。"""
    nodes = []
    edges = []

    # 输入节点
    nodes.append(
        {
            "id": "const_one",
            "type": "const",
            "label": "常量1",
            "config": {"value": 1.0},
            "position": {"x": 0, "y": 0},
        }
    )
    nodes.append(
        {
            "id": "user_input_atk",
            "type": "user_input",
            "label": "最终攻击力",
            "config": {"default": 1000.0},
            "position": {"x": 0, "y": 100},
        }
    )

    # 15 个复合节点（乘区）
    zone_names = list(ZONE_GRAPHS.keys())
    for i, zone_name in enumerate(zone_names):
        node_id = f"zone_{i + 1:02d}"
        # source_graph 是子图的完整 JSON 字符串
        source_graph_json = json.dumps(ZONE_GRAPHS[zone_name], ensure_ascii=False)
        nodes.append(
            {
                "id": node_id,
                "type": "composite",
                "label": zone_name.split("_", 1)[1],
                "config": {"composite_type": f"@终末地乘区包/{zone_name}", "source_graph": source_graph_json},
                "position": {"x": 200 * (i + 1), "y": 50},
            }
        )

    # 15 个连乘节点
    for i in range(15):
        mult_id = f"mult_{i + 1:02d}"
        nodes.append(
            {
                "id": mult_id,
                "type": "binary",
                "op": "*",
                "label": f"乘{i + 1}",
                "config": {},
                "position": {"x": 200 * (i + 1), "y": 150},
            }
        )

    # 输出节点
    nodes.append({"id": "final_out", "type": "output", "label": "最终伤害", "config": {}, "position": {"x": 3400, "y": 100}})

    # 连线
    # const_one -> mult_01 (lhs)
    edges.append({"id": "e_const", "from_node": "const_one", "from_port": 0, "to_node": "mult_01", "to_port": 0})

    # 每个乘区的输出 -> 对应连乘节点的 rhs
    for i in range(15):
        zone_id = f"zone_{i + 1:02d}"
        mult_id = f"mult_{i + 1:02d}"
        edges.append({"id": f"e_zone_{i + 1}", "from_node": zone_id, "from_port": 0, "to_node": mult_id, "to_port": 1})

    # 连乘节点串联
    for i in range(1, 15):
        prev_mult = f"mult_{i:02d}"
        curr_mult = f"mult_{i + 1:02d}"
        edges.append({"id": f"e_chain_{i}", "from_node": prev_mult, "from_port": 0, "to_node": curr_mult, "to_port": 0})

    # 最后一个连乘节点 -> 输出
    edges.append({"id": "e_final", "from_node": "mult_15", "from_port": 0, "to_node": "final_out", "to_port": 0})

    return {
        "schema_version": "calc-graph-v1",
        "name": "15乘区链",
        "description": "终末地 15 乘区串联计算链",
        "external_variables": {},
        "nodes": nodes,
        "edges": edges,
        "layout": {"sections": [{"id": "main", "title": "最终伤害", "output_nodes": ["final_out"], "columns": 1}]},
    }


def build_zip(output_path: Path) -> None:
    """生成乘区包 ZIP 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 15 个乘区子图
        for name, graph in ZONE_GRAPHS.items():
            zf.writestr(f"{name}.json", json.dumps(graph, ensure_ascii=False, indent=2))

        # 15 乘区链图
        chain_graph = build_chain_graph()
        zf.writestr("15乘区链.json", json.dumps(chain_graph, ensure_ascii=False, indent=2))

    print(f"✅ 已生成: {output_path}")
    print(f"   包含 {len(ZONE_GRAPHS) + 1} 个文件（15 乘区 + 1 链图）")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    zip_path = project_root / "output" / "终末地乘区包.zip"
    build_zip(zip_path)
