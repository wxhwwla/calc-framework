# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""布局与属性描述构建 — 按有效 source 分组生成 layout / attr_schema。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tools.generator.engine import OutputDef, VarDef

# 需要实体数据文件（或用户输入）提供取值的来源
ENTITY_SOURCES: frozenset[str] = frozenset({"character", "weapon", "equipment", "enemy"})

SECTION_ORDER: tuple[str, ...] = ("user_input", "character", "weapon", "equipment", "enemy")

SECTION_TITLES: dict[str, str] = {
    "user_input": "输入参数",
    "character": "角色参数",
    "weapon": "武器参数",
    "equipment": "装备参数",
    "enemy": "目标参数",
}

SECTION_IDS: dict[str, str] = {
    "user_input": "inputs",
    "character": "inputs_character",
    "weapon": "inputs_weapon",
    "equipment": "inputs_equipment",
    "enemy": "inputs_enemy",
}

_SECTION_TYPES: frozenset[str] = frozenset({"inputs", "outputs"})
_LAYOUT_SECTION_KEYS: frozenset[str] = frozenset({"type", "title", "tab", "columns", "variables", "outputs", "source"})
_MAX_COLUMNS = 3


class LayoutSectionsError(ValueError):
    """layout_sections 自定义布局声明错误。"""


def _normalize_names(value: object, location: str) -> list[str]:
    """校验非空字符串数组并去重。"""
    if not isinstance(value, list) or not value:
        raise LayoutSectionsError(f"{location} 必须是非空字符串数组")
    names: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise LayoutSectionsError(f"{location}[{index}] 必须是非空字符串")
        name = item.strip()
        if name in seen:
            raise LayoutSectionsError(f"{location} 存在重复项: {name!r}")
        seen.add(name)
        names.append(name)
    return names


def normalize_layout_sections(raw: object) -> tuple[list[dict[str, Any]], list[str]]:
    """校验 ``generate_adapter.layout_sections`` 的形状并补齐默认值。

    Args:
        raw: 工具调用传入的原始声明；``None`` 表示使用自动 layout。

    Returns:
        ``(归一化 sections, warnings)``；未知字段会被忽略并记入 warnings。

    Raises:
        LayoutSectionsError: 结构、类型、tab 一致性或 columns 范围非法。
    """
    if raw is None:
        return [], []
    if not isinstance(raw, list) or not raw:
        raise LayoutSectionsError("layout_sections 必须是非空数组")

    warnings: list[str] = []
    normalized: list[dict[str, Any]] = []
    tab_presence: list[bool] = []

    for index, item in enumerate(raw):
        location = f"layout_sections[{index}]"
        if not isinstance(item, dict):
            raise LayoutSectionsError(f"{location} 必须是对象")

        unknown = sorted(set(item) - _LAYOUT_SECTION_KEYS)
        if unknown:
            warnings.append(f"{location} 忽略未知字段: {', '.join(unknown)}")

        section_type = item.get("type", "inputs")
        if not isinstance(section_type, str) or section_type not in _SECTION_TYPES:
            raise LayoutSectionsError(f"{location}.type 必须为 inputs 或 outputs")

        title = item.get("title")
        if not isinstance(title, str) or not title.strip():
            raise LayoutSectionsError(f"{location}.title 必须是非空字符串")

        columns = item.get("columns", 2)
        if isinstance(columns, bool) or not isinstance(columns, int) or not 1 <= columns <= _MAX_COLUMNS:
            raise LayoutSectionsError(f"{location}.columns 必须是 1–{_MAX_COLUMNS} 的整数")

        section: dict[str, Any] = {
            "type": section_type,
            "title": title.strip(),
            "columns": columns,
        }

        has_tab = "tab" in item
        tab_presence.append(has_tab)
        if has_tab:
            tab = item.get("tab")
            if not isinstance(tab, str) or not tab.strip():
                raise LayoutSectionsError(f"{location}.tab 必须是非空字符串")
            section["tab"] = tab.strip()

        if section_type == "inputs":
            variables = item.get("variables")
            source = item.get("source")
            if variables is not None and source is not None:
                raise LayoutSectionsError(f"{location}: variables 与 source 只能二选一")
            if variables is None and source is None:
                raise LayoutSectionsError(f"{location}: inputs 段需要 variables 或 source")
            if variables is not None:
                section["variables"] = _normalize_names(variables, f"{location}.variables")
            if source is not None:
                if source not in SECTION_ORDER:
                    raise LayoutSectionsError(f"{location}.source 必须是 {'/'.join(SECTION_ORDER)} 之一")
                section["source"] = source
        else:
            outputs = item.get("outputs")
            if outputs is None:
                raise LayoutSectionsError(f"{location}: outputs 段需要非空 outputs 数组")
            section["outputs"] = _normalize_names(outputs, f"{location}.outputs")

        normalized.append(section)

    if any(tab_presence) and not all(tab_presence):
        raise LayoutSectionsError("layout_sections 的 tab 必须全部指定或全部省略")

    return normalized, warnings


def build_custom_layout(
    game_name: str,
    sections: list[dict[str, Any]],
    variables: list[VarDef],
    effective_sources: dict[str, str],
    outputs: list[OutputDef],
) -> dict[str, Any]:
    """按归一化的 ``layout_sections`` 构建 layout，支持分页与自定义列数。

    变量/输出引用必须存在；已绑定实体变量由查看器实体下拉提供，不能放进
    inputs 段。变量或输出跨 section 重复会直接报错。

    Args:
        game_name: 游戏/计算器名称。
        sections: :func:`normalize_layout_sections` 的输出。
        variables: 变量声明列表（保留原始 source 用于 ``source`` 简写分组）。
        effective_sources: 变量名 → 生成后实际 source。
        outputs: 输出声明列表。

    Returns:
        layout.json 对应的字典。

    Raises:
        LayoutSectionsError: 变量/输出引用不存在或跨 section 重复。
    """
    displayable = {v.name: f"user_input.{v.name}" for v in variables if effective_sources[v.name] == "user_input"}
    grouped: dict[str, list[str]] = {}
    for v in variables:
        if effective_sources[v.name] != "user_input":
            continue
        grouped.setdefault(_layout_group(v.source), []).append(v.name)

    output_names = {o.name for o in outputs}
    available_inputs = "、".join(sorted(displayable)[:10]) or "（无）"
    available_outputs = "、".join(sorted(output_names)) or "（无）"
    used_variables: set[str] = set()
    used_outputs: set[str] = set()
    built_sections: list[dict[str, Any]] = []

    for index, section in enumerate(sections):
        location = f"layout_sections[{index}]"
        built: dict[str, Any] = {
            "id": f"sec_{index + 1}",
            "type": section["type"],
            "title": section["title"],
            "columns": section.get("columns", 2),
        }
        if "tab" in section:
            built["tab"] = section["tab"]

        if section["type"] == "inputs":
            names = section.get("variables")
            if names is None:
                names = grouped.get(str(section.get("source", "")), [])
                if not names:
                    raise LayoutSectionsError(f"{location}: source {section.get('source')!r} 没有可显示的输入变量")
            resolved: list[str] = []
            for raw_name in names:
                name = raw_name.removeprefix("user_input.")
                if name not in displayable:
                    raise LayoutSectionsError(
                        f"{location}: 变量 {raw_name!r} 不可作为输入"
                        f"（绑定实体变量由查看器实体下拉提供，computed 不显示）。可用输入: {available_inputs}"
                    )
                if name in used_variables:
                    raise LayoutSectionsError(f"{location}: 变量 {name!r} 在多个 inputs 段中重复")
                used_variables.add(name)
                resolved.append(displayable[name])
            built["variables"] = resolved
        else:
            for name in section["outputs"]:
                if name not in output_names:
                    raise LayoutSectionsError(f"{location}: 未知输出 {name!r}。可用输出: {available_outputs}")
                if name in used_outputs:
                    raise LayoutSectionsError(f"{location}: 输出 {name!r} 在多个 outputs 段中重复")
                used_outputs.add(name)
            built["outputs"] = list(section["outputs"])

        built_sections.append(built)

    return {
        "schema_version": "ui-v1",
        "name": f"{game_name}计算表",
        "description": f"{game_name}的 ComputeSheet 排版（自定义分页）",
        "sections": built_sections,
    }


def _layout_group(original_source: str) -> str:
    """把原始 source 映射到输入分组；非实体来源统一归入 user_input。"""
    return original_source if original_source in ENTITY_SOURCES else "user_input"


def build_layout(
    game_name: str,
    variables: list[VarDef],
    effective_sources: dict[str, str],
    outputs: list[OutputDef],
) -> dict[str, Any]:
    """构建 UI layout，输入区按原始 source 分组，路径统一为 ``user_input.*``。

    Args:
        game_name: 游戏/计算器名称。
        variables: 变量声明列表（保留原始 source 用于分组）。
        effective_sources: 变量名 → 生成后实际 source。
        outputs: 输出声明列表。

    Returns:
        layout.json 对应的字典。
    """
    grouped: dict[str, list[str]] = {source: [] for source in SECTION_ORDER}
    for v in variables:
        if effective_sources[v.name] != "user_input":
            continue
        grouped[_layout_group(v.source)].append(f"user_input.{v.name}")

    sections: list[dict[str, Any]] = []
    for source in SECTION_ORDER:
        if grouped[source]:
            sections.append(
                {
                    "id": SECTION_IDS[source],
                    "type": "inputs",
                    "title": SECTION_TITLES[source],
                    "variables": grouped[source],
                }
            )

    primary_outs = [o.name for o in outputs if o.is_primary]
    if primary_outs:
        sections.append(
            {
                "id": "outputs",
                "type": "outputs",
                "title": "计算结果",
                "outputs": primary_outs,
            }
        )
    other_outs = [o.name for o in outputs if o.name not in primary_outs]
    if other_outs:
        sections.append(
            {
                "id": "detail",
                "type": "outputs",
                "title": "中间过程",
                "outputs": other_outs,
            }
        )

    return {
        "schema_version": "ui-v1",
        "name": f"{game_name}计算表",
        "description": f"{game_name}的 ComputeSheet 排版（自动生成）",
        "sections": sections,
    }


_ATTR_TYPES: frozenset[str] = frozenset({"float", "int", "bool", "str", "percent"})


def build_attr_schema(variables: list[VarDef], effective_sources: dict[str, str]) -> dict[str, Any]:
    """构建 attr_schema，``source`` 写入变量生成后的实际来源。

    变量类型原样保留（float/int/bool/str/percent），并始终写入 ``default``；
    省略 0 默认值会让 ``AttributeSchema.validate`` 把该属性当成必填项。
    """
    attrs = []
    for v in variables:
        attrs.append(
            {
                "name": v.name,
                "type": v.type if v.type in _ATTR_TYPES else "float",
                "source": effective_sources[v.name],
                "default": v.default,
                "description": v.description,
            }
        )
    return {"attributes": attrs}
