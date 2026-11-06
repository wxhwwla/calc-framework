# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""变量 UI 元数据归一化 — 校验 ``min`` / ``max`` / ``ui_control``。

``ui_control`` 的结构由 ``calc_framework.ui.controls.infer_control`` 消费：

- ``suffix``：数值控件后缀（如 ``"%"``）；
- ``step``：单步增量，必须大于 0；
- ``widget``：``spinbox`` / ``slider`` / ``switch`` / ``dropdown``；
- ``options``：下拉候选项，提供时默认把控件切换为 ``dropdown``。
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

__all__ = ["VariableUiError", "normalize_variable_ui"]

_UI_KEYS = frozenset({"suffix", "step", "widget", "options"})
_WIDGETS = frozenset({"spinbox", "slider", "switch", "dropdown"})
_NUMERIC_TYPES = frozenset({"float", "int"})


class VariableUiError(ValueError):
    """变量 UI 元数据不合法。"""


def normalize_variable_ui(
    *,
    name: str,
    var_type: str,
    source: str,
    min_value: Any = None,
    max_value: Any = None,
    ui_control: Any = None,
    warnings: list[str] | None = None,
) -> tuple[float | int | None, float | int | None, dict[str, Any]]:
    """校验并归一化变量的数值范围与 UI 控件配置。

    Args:
        name: 变量名，用于错误/告警文案。
        var_type: 归一化后的变量类型（float/int/bool/str）。
        source: 归一化后的变量来源。
        min_value: 原始 ``min`` 声明。
        max_value: 原始 ``max`` 声明。
        ui_control: 原始 ``ui_control`` 声明。
        warnings: 可选的告警收集列表。

    Returns:
        ``(min, max, ui_control)``；未声明的值分别为 ``None`` / 空字典。

    Raises:
        VariableUiError: 数值非法、范围互斥、控件类型或候选项非法。
    """
    sink = warnings if warnings is not None else []
    low = _number(min_value, f"变量 {name!r} 的 min")
    high = _number(max_value, f"变量 {name!r} 的 max")
    if low is not None and high is not None and low > high:
        raise VariableUiError(f"变量 {name!r} 的 min 不能大于 max")
    if (low is not None or high is not None) and var_type not in _NUMERIC_TYPES:
        sink.append(f"变量 {name!r} 的类型为 {var_type!r}，min/max 只对 float/int 生效")

    ui = _normalize_ui(ui_control, f"变量 {name!r}", sink)
    if ui and source != "user_input":
        sink.append(f"变量 {name!r} 的 ui_control 仅对 user_input 变量生效（当前 source={source!r}）")
    if ui.get("options") and "widget" not in ui:
        ui["widget"] = "dropdown"
    return low, high, ui


def _normalize_ui(raw: Any, location: str, warnings: list[str]) -> dict[str, Any]:
    if raw is None:
        return {}
    if not isinstance(raw, Mapping):
        raise VariableUiError(f"{location} 的 ui_control 必须是对象")

    unknown = sorted(set(raw) - _UI_KEYS)
    if unknown:
        warnings.append(f"{location} 的 ui_control 忽略未知字段: {', '.join(unknown)}")

    ui: dict[str, Any] = {}
    if "suffix" in raw:
        suffix = raw["suffix"]
        if not isinstance(suffix, str):
            raise VariableUiError(f"{location} 的 ui_control.suffix 必须是字符串")
        ui["suffix"] = suffix

    if "step" in raw:
        step = _number(raw["step"], f"{location} 的 ui_control.step")
        if step is None or step <= 0:
            raise VariableUiError(f"{location} 的 ui_control.step 必须大于 0")
        ui["step"] = step

    if "widget" in raw:
        widget = raw["widget"]
        if widget not in _WIDGETS:
            allowed = ", ".join(sorted(_WIDGETS))
            raise VariableUiError(f"{location} 的 ui_control.widget 无效: {widget!r}（允许: {allowed}）")
        ui["widget"] = widget

    if "options" in raw:
        options = raw["options"]
        if not isinstance(options, list) or not options or any(not isinstance(item, str) for item in options):
            raise VariableUiError(f"{location} 的 ui_control.options 必须是非空字符串列表")
        ui["options"] = list(options)

    return ui


def _number(value: Any, location: str) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise VariableUiError(f"{location} 必须是数值")
    if isinstance(value, float) and not math.isfinite(value):
        raise VariableUiError(f"{location} 必须是有限数值")
    return value
