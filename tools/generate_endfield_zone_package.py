#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
终末地 15 乘区计算包生成器

为图编辑器生成完整的终末地伤害乘区计算包。
输出 ZIP 文件，可在编辑器中通过「+ 导入包」直接使用。

每个乘区作为一个独立 JSON 文件（复合节点），
顶部链图用复合节点串联 15 个乘区。

使用方式：
    python tools/generate_endfield_zone_package.py
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "output"
PACKAGE_NAME = "终末地乘区包"

# ── 每个乘区的定义 ──
# zone_id: (display_name, inputs, internal_graph_builder)

ZONE_DEFS: list[dict] = []

# ═══════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════

_counter = [0]


def _id() -> str:
    _counter[0] += 1
    return f"n{_counter[0]}"


def _reset_counter() -> None:
    _counter[0] = 0


def _graph(
    name: str,
    desc: str,
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    """构造一个 graph_editor 格式的 JSON 字典。"""
    output_ids = [n["id"] for n in nodes if n["type"] == "output"]
    return {
        "schema_version": "calc-graph-v1",
        "name": name,
        "description": desc,
        "nodes": nodes,
        "edges": edges,
        "layout": {
            "sections": [
                {"id": "s1", "title": "输出", "output_nodes": output_ids, "columns": 1},
            ],
        },
        "external_variables": {},
    }


def _ui(label: str, default: float = 0.0, min_v: float = -1e9, max_v: float = 1e9, step: float = 0.01) -> dict:
    return {
        "id": _id(),
        "type": "user_input",
        "label": label,
        "config": {"default": default, "min": min_v, "max": max_v, "step": step},
        "position": {"x": 0, "y": 0},
    }


def _const(value: float) -> dict:
    return {
        "id": _id(),
        "type": "const",
        "label": str(value),
        "config": {"value": value},
        "position": {"x": 0, "y": 0},
    }


def _binary(op: str, lhs_id: str, rhs_id: str, label: str = "") -> dict:
    return {
        "id": _id(),
        "type": "binary",
        "op": op,
        "label": label,
        "config": {},
        "position": {"x": 0, "y": 0},
    }


def _output(label: str) -> dict:
    return {
        "id": _id(),
        "type": "output",
        "label": label,
        "config": {},
        "position": {"x": 0, "y": 0},
    }


def _wire(frm: str, fport: int, to: str, tport: int) -> dict:
    return {"from_node": frm, "from_port": fport, "to_node": to, "to_port": tport}


# ═══════════════════════════════════════════
# 15 个乘区定义
# ═══════════════════════════════════════════


def zone_01_base_damage() -> tuple[str, str, dict]:
    """基础伤害区: final_attack × skill_multiplier"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_atk = _ui("最终攻击力", 1000, 0, 1e9)
    ui_skill = _ui("技能倍率", 1.0, 0, 1e9)
    mult = _binary("*", ui_atk["id"], ui_skill["id"], "基础伤害")
    out = _output("基础伤害")
    nodes += [ui_atk, ui_skill, mult, out]
    edges.append(_wire(ui_atk["id"], 0, mult["id"], 0))
    edges.append(_wire(ui_skill["id"], 0, mult["id"], 1))
    edges.append(_wire(mult["id"], 0, out["id"], 0))
    return "基础伤害区", "最终攻击力 × 技能倍率", _graph("基础伤害区", "基础伤害 = 最终攻击力 × 技能倍率", nodes, edges)


def zone_02_crit() -> tuple[str, str, dict]:
    """暴击区: 1 + 暴击率 × (暴击伤害 - 1)"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_rate = _ui("暴击率", 0.05, 0, 1, 0.01)
    ui_dmg = _ui("暴击伤害", 0.5, 0, 10, 0.01)
    c1 = _const(1.0)
    sub = _binary("-", ui_dmg["id"], c1["id"], "暴击伤害-1")
    mul = _binary("*", ui_rate["id"], sub["id"], "暴击率×(暴击伤害-1)")
    add = _binary("+", c1["id"], mul["id"], "暴击区")
    out = _output("暴击区")
    nodes += [ui_rate, ui_dmg, c1, sub, mul, add, out]
    edges.append(_wire(ui_dmg["id"], 0, sub["id"], 0))
    edges.append(_wire(c1["id"], 0, sub["id"], 1))
    edges.append(_wire(ui_rate["id"], 0, mul["id"], 0))
    edges.append(_wire(sub["id"], 0, mul["id"], 1))
    edges.append(_wire(c1["id"], 0, add["id"], 0))
    edges.append(_wire(mul["id"], 0, add["id"], 1))
    edges.append(_wire(add["id"], 0, out["id"], 0))
    return "暴击区", "1 + 暴击率×(暴击伤害-1)", _graph("暴击区", "暴击区 = 1 + 暴击率×(暴击伤害-1)", nodes, edges)


def zone_03_damage_bonus() -> tuple[str, str, dict]:
    """伤害加成区: 1 + sum(各类伤害加成)"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_dt = _ui("伤害类型加成", 0.0, -1, 10, 0.01)
    ui_st = _ui("技能类型加成", 0.0, -1, 10, 0.01)
    ui_ib = _ui("失衡伤害加成", 0.0, -1, 10, 0.01)
    ui_ot = _ui("其他伤害加成", 0.0, -1, 10, 0.01)
    c1 = _const(1.0)
    a1 = _binary("+", c1["id"], ui_dt["id"], "1+伤害类型")
    a2 = _binary("+", a1["id"], ui_st["id"], "+技能类型")
    a3 = _binary("+", a2["id"], ui_ib["id"], "+失衡")
    a4 = _binary("+", a3["id"], ui_ot["id"], "伤害加成区")
    out = _output("伤害加成区")
    nodes += [ui_dt, ui_st, ui_ib, ui_ot, c1, a1, a2, a3, a4, out]
    edges.append(_wire(c1["id"], 0, a1["id"], 0))
    edges.append(_wire(ui_dt["id"], 0, a1["id"], 1))
    edges.append(_wire(a1["id"], 0, a2["id"], 0))
    edges.append(_wire(ui_st["id"], 0, a2["id"], 1))
    edges.append(_wire(a2["id"], 0, a3["id"], 0))
    edges.append(_wire(ui_ib["id"], 0, a3["id"], 1))
    edges.append(_wire(a3["id"], 0, a4["id"], 0))
    edges.append(_wire(ui_ot["id"], 0, a4["id"], 1))
    edges.append(_wire(a4["id"], 0, out["id"], 0))
    return "伤害加成区", "1 + 伤害类型 + 技能类型 + 失衡 + 其他", _graph("伤害加成区", "伤害加成区 = 1 + 各类伤害加成之和", nodes, edges)


def zone_04_damage_reduction() -> tuple[str, str, dict]:
    """伤害减免区: 1 - 减免总值"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_reduce = _ui("伤害减免总值", 0.0, -1, 1, 0.01)
    c1 = _const(1.0)
    sub = _binary("-", c1["id"], ui_reduce["id"], "伤害减免区")
    out = _output("伤害减免区")
    nodes += [ui_reduce, c1, sub, out]
    edges.append(_wire(c1["id"], 0, sub["id"], 0))
    edges.append(_wire(ui_reduce["id"], 0, sub["id"], 1))
    edges.append(_wire(sub["id"], 0, out["id"], 0))
    return "伤害减免区", "1 - 减免总值", _graph("伤害减免区", "伤害减免区 = 1 - 伤害减免总值", nodes, edges)


def zone_05_amplification() -> tuple[str, str, dict]:
    """增幅区: 1 + 增幅总值"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_amp = _ui("增幅总值", 0.0, -1, 10, 0.01)
    c1 = _const(1.0)
    add = _binary("+", c1["id"], ui_amp["id"], "增幅区")
    out = _output("增幅区")
    nodes += [ui_amp, c1, add, out]
    edges.append(_wire(c1["id"], 0, add["id"], 0))
    edges.append(_wire(ui_amp["id"], 0, add["id"], 1))
    edges.append(_wire(add["id"], 0, out["id"], 0))
    return "增幅区", "1 + 增幅总值", _graph("增幅区", "增幅区 = 1 + 所有增幅之和", nodes, edges)


def zone_06_weakness() -> tuple[str, str, dict]:
    """虚弱区: 1 - 虚弱总值"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_wk = _ui("虚弱总值", 0.0, -1, 1, 0.01)
    c1 = _const(1.0)
    sub = _binary("-", c1["id"], ui_wk["id"], "虚弱区")
    out = _output("虚弱区")
    nodes += [ui_wk, c1, sub, out]
    edges.append(_wire(c1["id"], 0, sub["id"], 0))
    edges.append(_wire(ui_wk["id"], 0, sub["id"], 1))
    edges.append(_wire(sub["id"], 0, out["id"], 0))
    return "虚弱区", "1 - 虚弱总值", _graph("虚弱区", "虚弱区 = 1 - 虚弱总值", nodes, edges)


def zone_07_shelter() -> tuple[str, str, dict]:
    """庇护区: 1 - 庇护值"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_sh = _ui("庇护值", 0.0, -1, 1, 0.01)
    c1 = _const(1.0)
    sub = _binary("-", c1["id"], ui_sh["id"], "庇护区")
    out = _output("庇护区")
    nodes += [ui_sh, c1, sub, out]
    edges.append(_wire(c1["id"], 0, sub["id"], 0))
    edges.append(_wire(ui_sh["id"], 0, sub["id"], 1))
    edges.append(_wire(sub["id"], 0, out["id"], 0))
    return "庇护区", "1 - 庇护值", _graph("庇护区", "庇护区 = 1 - 庇护值", nodes, edges)


def zone_08_fragile() -> tuple[str, str, dict]:
    """脆弱区: 1 + 脆弱总值"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_fr = _ui("脆弱总值", 0.0, -1, 10, 0.01)
    c1 = _const(1.0)
    add = _binary("+", c1["id"], ui_fr["id"], "脆弱区")
    out = _output("脆弱区")
    nodes += [ui_fr, c1, add, out]
    edges.append(_wire(c1["id"], 0, add["id"], 0))
    edges.append(_wire(ui_fr["id"], 0, add["id"], 1))
    edges.append(_wire(add["id"], 0, out["id"], 0))
    return "脆弱区", "1 + 脆弱总值", _graph("脆弱区", "脆弱区 = 1 + 所有脆弱之和", nodes, edges)


def zone_09_vulnerability() -> tuple[str, str, dict]:
    """易伤区: 1 + 易伤总值"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_vu = _ui("易伤总值", 0.0, -1, 10, 0.01)
    c1 = _const(1.0)
    add = _binary("+", c1["id"], ui_vu["id"], "易伤区")
    out = _output("易伤区")
    nodes += [ui_vu, c1, add, out]
    edges.append(_wire(c1["id"], 0, add["id"], 0))
    edges.append(_wire(ui_vu["id"], 0, add["id"], 1))
    edges.append(_wire(add["id"], 0, out["id"], 0))
    return "易伤区", "1 + 易伤总值", _graph("易伤区", "易伤区 = 1 + 所有易伤之和", nodes, edges)


def zone_10_defense() -> tuple[str, str, dict]:
    """防御区: 100 / (100 + 敌方防御)"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_def = _ui("敌方防御", 200, 0, 1e9, 1)
    c100 = _const(100.0)
    add = _binary("+", ui_def["id"], c100["id"], "敌防+100")
    div = _binary("/", c100["id"], add["id"], "防御区")
    out = _output("防御区")
    nodes += [ui_def, c100, add, div, out]
    edges.append(_wire(ui_def["id"], 0, add["id"], 0))
    edges.append(_wire(c100["id"], 0, add["id"], 1))
    edges.append(_wire(c100["id"], 0, div["id"], 0))
    edges.append(_wire(add["id"], 0, div["id"], 1))
    edges.append(_wire(div["id"], 0, out["id"], 0))
    return "防御区", "100 / (100 + 敌方防御)", _graph("防御区", "防御区 = 100 / (100 + 敌方防御)", nodes, edges)


def zone_11_imbalance() -> tuple[str, str, dict]:
    """失衡易伤区: 失衡易伤系数（默认 1.0）"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_imb = _ui("失衡易伤系数", 1.0, 0, 10, 0.01)
    out = _output("失衡易伤区")
    nodes += [ui_imb, out]
    edges.append(_wire(ui_imb["id"], 0, out["id"], 0))
    return "失衡易伤区", "失衡易伤系数", _graph("失衡易伤区", "失衡易伤区 = 系数（默认 1.0）", nodes, edges)


def zone_12_resistance() -> tuple[str, str, dict]:
    """抗性区: 1 - (抗性 - 无视抗性) / 100"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_res = _ui("敌方抗性", 20, 0, 100, 1)
    ui_pen = _ui("无视抗性", 0, 0, 100, 1)
    c100 = _const(100.0)
    c1 = _const(1.0)
    sub = _binary("-", ui_res["id"], ui_pen["id"], "抗性-无视")
    div = _binary("/", sub["id"], c100["id"], "/100")
    result = _binary("-", c1["id"], div["id"], "抗性区")
    out = _output("抗性区")
    nodes += [ui_res, ui_pen, c100, c1, sub, div, result, out]
    edges.append(_wire(ui_res["id"], 0, sub["id"], 0))
    edges.append(_wire(ui_pen["id"], 0, sub["id"], 1))
    edges.append(_wire(sub["id"], 0, div["id"], 0))
    edges.append(_wire(c100["id"], 0, div["id"], 1))
    edges.append(_wire(c1["id"], 0, result["id"], 0))
    edges.append(_wire(div["id"], 0, result["id"], 1))
    edges.append(_wire(result["id"], 0, out["id"], 0))
    return "抗性区", "1 - (抗性-无视)/100", _graph("抗性区", "抗性区 = 1 - (敌方抗性-无视抗性)/100", nodes, edges)


def zone_13_non_control_reduction() -> tuple[str, str, dict]:
    """非主控减伤区: 1 - 非主控减伤"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_ncr = _ui("非主控减伤", 0.0, -1, 1, 0.01)
    c1 = _const(1.0)
    sub = _binary("-", c1["id"], ui_ncr["id"], "非主控减伤区")
    out = _output("非主控减伤区")
    nodes += [ui_ncr, c1, sub, out]
    edges.append(_wire(c1["id"], 0, sub["id"], 0))
    edges.append(_wire(ui_ncr["id"], 0, sub["id"], 1))
    edges.append(_wire(sub["id"], 0, out["id"], 0))
    return "非主控减伤区", "1 - 非主控减伤", _graph("非主控减伤区", "非主控减伤区 = 1 - 非主控减伤值", nodes, edges)


def zone_14_combo_bonus() -> tuple[str, str, dict]:
    """连击增伤区: 1 + 连击增伤"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_cb = _ui("连击增伤", 0.0, -1, 10, 0.01)
    c1 = _const(1.0)
    add = _binary("+", c1["id"], ui_cb["id"], "连击增伤区")
    out = _output("连击增伤区")
    nodes += [ui_cb, c1, add, out]
    edges.append(_wire(c1["id"], 0, add["id"], 0))
    edges.append(_wire(ui_cb["id"], 0, add["id"], 1))
    edges.append(_wire(add["id"], 0, out["id"], 0))
    return "连击增伤区", "1 + 连击增伤", _graph("连击增伤区", "连击增伤区 = 1 + 连击增伤值", nodes, edges)


def zone_15_special() -> tuple[str, str, dict]:
    """特殊乘区: 特殊乘区值（默认 1.0）"""
    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []
    ui_sp = _ui("特殊乘区", 1.0, -10, 10, 0.01)
    out = _output("特殊乘区")
    nodes += [ui_sp, out]
    edges.append(_wire(ui_sp["id"], 0, out["id"], 0))
    return "特殊乘区", "特殊乘区系数", _graph("特殊乘区", "特殊乘区 = 系数（默认 1.0）", nodes, edges)


# 15 乘区列表
ALL_ZONE_BUILDERS = [
    zone_01_base_damage,
    zone_02_crit,
    zone_03_damage_bonus,
    zone_04_damage_reduction,
    zone_05_amplification,
    zone_06_weakness,
    zone_07_shelter,
    zone_08_fragile,
    zone_09_vulnerability,
    zone_10_defense,
    zone_11_imbalance,
    zone_12_resistance,
    zone_13_non_control_reduction,
    zone_14_combo_bonus,
    zone_15_special,
]

# ═══════════════════════════════════════════
# 主函数
# ═══════════════════════════════════════════


def _ensure_ascii_for_json(obj: object) -> str:
    """序列化 JSON。"""
    return json.dumps(obj, ensure_ascii=False, indent=2)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    zip_path = OUTPUT_DIR / f"{PACKAGE_NAME}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # ── 逐个写入乘区 JSON ──
        print("生成 15 个乘区子图...")
        zone_files: list[str] = []
        for builder in ALL_ZONE_BUILDERS:
            zone_name, zone_desc, graph = builder()
            filename = f"{zone_name}.json"
            zf.writestr(filename, _ensure_ascii_for_json(graph))
            zone_files.append(filename)
            print(f"  ✓ {zone_name} — {zone_desc}")

        # ── 顶层链图 ──
        print("\n生成顶层链图（15 乘区串联）...")
        chain = _build_chain_graph()
        chain_filename = "15乘区链.json"
        zf.writestr(chain_filename, _ensure_ascii_for_json(chain))
        print(f"  ✓ {chain_filename}")

    print(f"\n✅ 包已生成: {zip_path}")
    print(f"   共 {len(ALL_ZONE_BUILDERS) + 1} 个文件")
    print("\n使用方式: 打开公式计算图编辑器 → 切换到「包」选项卡 → 点击「+ 导入包」→ 选择此 ZIP")


def _build_chain_graph() -> dict:
    """
    构建 15 乘区串联链图。
    
    结构：
        const(1.0) 
            × [复合:基础伤害区]   ← 端口: 最终攻击力, 技能倍率
            × [复合:暴击区]       ← 端口: 暴击率, 暴击伤害（默认值）
            × [复合:伤害加成区]    ← 端口: 各类加成（默认值）
            × ...
            × [复合:特殊乘区]      ← 端口: 特殊乘区系数（默认值）
            = [output:最终伤害]
    
    每个复合计算其乘区的倍率值，最后全部乘起来得最终伤害。
    """
    zone_sub_graphs: list[tuple[str, str]] = []
    for builder in ALL_ZONE_BUILDERS:
        zone_name, _, graph = builder()
        zone_sub_graphs.append((zone_name, json.dumps(graph, ensure_ascii=False)))

    _reset_counter()
    nodes: list[dict] = []
    edges: list[dict] = []

    # ── const(1.0) 作为乘算起点 ──
    c1 = _const(1.0)
    nodes.append(c1)
    accum_id = c1["id"]

    # ── 创建顶层 user_input 节点（用于 基础伤害区） ──
    # 这些会连接到第一个复合节点（基础伤害区）的输入端口
    ui_atk = _ui("最终攻击力", 1000, 0, 1e9)
    ui_skill = _ui("技能倍率", 1.0, 0, 1e9)

    for idx, (zone_name, sub_json) in enumerate(zone_sub_graphs):
        type_id = f"@{PACKAGE_NAME}/{zone_name}"

        comp = {
            "id": _id(),
            "type": "composite",
            "op": type_id,
            "label": zone_name,
            "config": {
                "source_graph": sub_json,
                "package_name": PACKAGE_NAME,
            },
            "position": {"x": 0, "y": 0},
        }
        comp_id = comp["id"]
        nodes.append(comp)

        # 第一个复合节点（基础伤害区）需要两个输入
        if idx == 0:
            nodes += [ui_atk, ui_skill]
            edges.append(_wire(ui_atk["id"], 0, comp_id, 0))
            edges.append(_wire(ui_skill["id"], 0, comp_id, 1))

        # accum × zone_multiplier
        mul = _binary("*", accum_id, comp_id, f"×{zone_name}")
        mul_id = mul["id"]
        nodes.append(mul)
        edges.append(_wire(accum_id, 0, mul["id"], 0))
        edges.append(_wire(comp_id, 0, mul["id"], 1))

        accum_id = mul_id

    out = _output("最终伤害")
    nodes.append(out)
    edges.append(_wire(accum_id, 0, out["id"], 0))

    output_ids = [out["id"]]
    return {
        "schema_version": "calc-graph-v1",
        "name": "终末地15乘区链",
        "description": "终末地 15 乘区完整伤害计算公式。每个乘区为独立的复合节点，双击可编辑内部逻辑。",
        "nodes": nodes,
        "edges": edges,
        "layout": {
            "sections": [
                {"id": "s1", "title": "输出", "output_nodes": output_ids, "columns": 1},
            ],
        },
        "external_variables": {},
    }


if __name__ == "__main__":
    main()
