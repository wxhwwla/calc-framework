"""DAG 公式模板库 — 可复用的子图模式。

模板是预定义的 DAG 子图模式，可通过 ``register_template()`` 注册，
在 DAG JSON 中通过 ``"template": "模板名"`` 引用，加载时自动展开为实际节点。

用法::

    # 注册模板
    register_template("defense_reduction",
        parameters=["defense", "scale"],
        nodes={
            "mult": {"type": "binary", "op": "*", "lhs": "$defense", "rhs": "$scale"},
            "result": {"type": "expr", "expr": "100 / (100 + def_scaled)", "inputs": {"def_scaled": "mult"}},
        },
        output_node="result",
        description="防御减伤: 100/(100 + defense*scale)")

    # DAG JSON 中引用
    # {"template": "defense_reduction", "bindings": {"defense": "enemy_def", "scale": "const_0_5"}}
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_TEMPLATES: dict[str, dict[str, Any]] = {}

TEMPLATE_META_FIELDS = frozenset({"parameters", "nodes", "output_node", "description"})


class TemplateError(ValueError):
    """模板相关错误。"""


def register_template(
    name: str,
    *,
    parameters: list[str],
    nodes: dict[str, dict[str, Any]],
    output_node: str,
    description: str = "",
) -> None:
    """注册一个可复用的 DAG 模板。

    Args:
        name: 模板名称（DAG JSON 中通过 ``"template": name`` 引用）
        parameters: 模板参数名列表。节点定义中以 ``$param`` 形式引用。
        nodes: 模板内部的节点定义。节点间的引用直接用节点 ID。
               模板外部的引用用 ``$param`` 形式，绑定阶段替换。
        output_node: 模板的输出节点 ID。展开后该节点会接管调用节点的 ID。
        description: 模板描述。

    Raises:
        TemplateError: 模板名已存在或参数不合法
    """
    if not name or not isinstance(name, str):
        raise TemplateError(f"模板名无效: {name!r}")
    if name in _TEMPLATES:
        raise TemplateError(f"模板 {name!r} 已注册")
    if not nodes:
        raise TemplateError(f"模板 {name!r} 没有节点")
    if output_node not in nodes:
        raise TemplateError(f"模板 {name!r} 的 output_node {output_node!r} 不在 nodes 中")

    _TEMPLATES[name] = {
        "name": name,
        "parameters": list(parameters),
        "nodes": deepcopy(nodes),
        "output_node": output_node,
        "description": description,
    }


def unregister_template(name: str) -> None:
    """注销一个模板。"""
    _TEMPLATES.pop(name, None)


def list_templates() -> list[str]:
    """列出所有已注册的模板名。"""
    return sorted(_TEMPLATES.keys())


def get_template(name: str) -> dict[str, Any]:
    """获取模板定义。"""
    if name not in _TEMPLATES:
        raise TemplateError(f"模板 {name!r} 未注册")
    return deepcopy(_TEMPLATES[name])


def clear_templates() -> None:
    """清空所有模板。"""
    _TEMPLATES.clear()


def expand_template_refs(raw: dict[str, Any]) -> dict[str, Any]:
    """展开 DAG JSON 中的所有模板引用节点。

    遍历 ``raw["nodes"]``，将所有含 ``"template"`` 字段的节点展开为实际节点。
    展开后原始模板节点被删除，其 ID 被模板的 output_node 取代。

    Returns:
        修改后的 raw dict（nodes 已被展开）
    """
    if "nodes" not in raw:
        return raw

    nodes = raw["nodes"]
    new_nodes: dict[str, dict[str, Any]] = {}

    for nid, ndef in nodes.items():
        if "template" not in ndef:
            new_nodes[nid] = deepcopy(ndef)
            continue

        tpl_name = ndef["template"]
        if tpl_name not in _TEMPLATES:
            raise TemplateError(
                f"节点 {nid!r} 引用的模板 {tpl_name!r} 未注册"
            )

        tpl = _TEMPLATES[tpl_name]
        bindings: dict[str, str] = ndef.get("bindings", {})
        prefix = f"{nid}_"
        param_set = set(tpl["parameters"])

        for pname in bindings:
            if pname not in param_set:
                raise TemplateError(
                    f"模板 {tpl_name!r} 没有参数 {pname!r}"
                )

        for tnid, tndef in tpl["nodes"].items():
            cloned: dict[str, Any] = deepcopy(tndef)

            cloned = _apply_bindings_to_def(cloned, bindings, prefix, tpl)

            is_output = (tnid == tpl["output_node"])
            new_id = nid if is_output else (prefix + tnid)
            new_nodes[new_id] = cloned

        label = ndef.get("label", "")
        if label:
            if nid in new_nodes:
                new_nodes[nid]["label"] = label
            for tnid in tpl["nodes"]:
                prefixed = prefix + tnid
                if prefixed in new_nodes:
                    if not new_nodes[prefixed].get("label"):
                        new_nodes[prefixed]["label"] = f"{label}.{tnid}"

    raw["nodes"] = new_nodes
    return raw


def _apply_bindings_to_def(
    ndef: dict[str, Any],
    bindings: dict[str, str],
    prefix: str,
    tpl: dict[str, Any],
) -> dict[str, Any]:
    """将绑定应用到单个节点定义上。

    - ``$param`` → bindings[param]（外部引用，不 prefix）
    - 模板内部节点 ID → prefix + ID
    """
    tpl_node_ids = set(tpl["nodes"].keys())

    _fields_with_node_refs = {"lhs", "rhs", "input", "cond", "true_val", "false_val"}

    result: dict[str, Any] = {}
    for key, val in ndef.items():
        if key in _fields_with_node_refs and isinstance(val, str):
            if val.startswith("$"):
                result[key] = bindings.get(val[1:], val)
            elif val in tpl_node_ids:
                result[key] = prefix + val
            else:
                result[key] = val
        elif key == "inputs" and isinstance(val, dict):
            result[key] = {}
            for iname, iref in val.items():
                if isinstance(iref, str) and iref.startswith("$"):
                    result[key][iname] = bindings.get(iref[1:], iref)
                elif isinstance(iref, str) and iref in tpl_node_ids:
                    result[key][iname] = prefix + iref
                else:
                    result[key][iname] = iref
        elif key == "path" and isinstance(val, str) and val.startswith("$"):
            result[key] = bindings.get(val[1:], val)
        else:
            result[key] = deepcopy(val)

    return result


# ===== 内置通用模板 =====

def _register_builtin_templates() -> None:
    """注册框架内置的通用公式模板。"""
    if _TEMPLATES:
        return

    register_template(
        "defense_reduction",
        parameters=["defense", "scale"],
        nodes={
            "mult": {"type": "binary", "op": "*", "lhs": "$defense", "rhs": "$scale"},
            "result": {
                "type": "expr",
                "expr": "100 / (100 + def_scaled)",
                "inputs": {"def_scaled": "mult"},
            },
        },
        output_node="result",
        description="经典防御减伤: 最终减伤比 = 100 / (100 + defense * scale)",
    )

    register_template(
        "crit_multiplier",
        parameters=["crit_rate", "crit_dmg", "is_crit"],
        nodes={
            "crit_rate_val": {"type": "var", "path": "$crit_rate"},
            "crit_dmg_val": {"type": "var", "path": "$crit_dmg"},
            "is_crit_val": {"type": "var", "path": "$is_crit"},
            "const_1": {"type": "const", "value": 1.0},
            "base_mult": {"type": "binary", "op": "+", "lhs": "const_1", "rhs": "crit_dmg_val"},
            "result": {
                "type": "condition",
                "cond": "is_crit_val",
                "true_val": "base_mult",
                "false_val": "const_1",
            },
        },
        output_node="result",
        description="暴击倍率: 暴击时 = 1 + crit_dmg, 否则 = 1",
    )

    register_template(
        "clamp_to_range",
        parameters=["value", "min_val", "max_val"],
        nodes={
            "result": {
                "type": "expr",
                "expr": "clamp(val, min_v, max_v)",
                "inputs": {"val": "$value", "min_v": "$min_val", "max_v": "$max_val"},
            },
        },
        output_node="result",
        description="值钳制: clamp(value, min, max)",
    )

    register_template(
        "percent_of",
        parameters=["value", "total"],
        nodes={
            "result": {
                "type": "expr",
                "expr": "percent_of(val, tot)",
                "inputs": {"val": "$value", "tot": "$total"},
            },
        },
        output_node="result",
        description="百分比: value / total（防除零）",
    )

    register_template(
        "attribute_scaling",
        parameters=["base", "growth", "level", "offset", "divisor"],
        nodes={
            "level_minus_1": {"type": "binary", "op": "-", "lhs": "$level", "rhs": "const_1"},
            "growth_term": {"type": "binary", "op": "*", "lhs": "$growth", "rhs": "level_minus_1"},
            "growth_with_offset": {"type": "binary", "op": "+", "lhs": "growth_term", "rhs": "$offset"},
            "div_result": {"type": "expr", "expr": "floor(growth_off / div)",
                           "inputs": {"growth_off": "growth_with_offset", "div": "$divisor"}},
            "result": {"type": "binary", "op": "+", "lhs": "$base", "rhs": "div_result"},
            "const_1": {"type": "const", "value": 1.0},
        },
        output_node="result",
        description="等级成长公式: base + floor((growth * (level - 1) + offset) / divisor)",
    )


_register_builtin_templates()
