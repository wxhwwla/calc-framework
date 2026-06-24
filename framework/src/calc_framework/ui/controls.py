# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""控件推断 — 根据 DAG variables 声明推断对应的 UI 控件类型。



纯逻辑模块，无 GUI 依赖。

"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ControlSpec:
    """ControlSpec。"""

    label: str

    widget: str

    default: Any = 0.0

    min_val: float | None = None

    max_val: float | None = None

    step: float = 0.01

    options: list[str] = field(default_factory=list)

    description: str = ""


def infer_control(path: str, variable: dict[str, Any]) -> ControlSpec:
    ui_override = variable.get("ui_control", {})

    source = variable.get("source", "")

    var_type = variable.get("type", "float")

    label = path

    description = variable.get("description", "")

    if source not in ("user_input",):
        return ControlSpec(label=label, widget="none", description=description)

    widget = ui_override.get("widget")

    step = ui_override.get("step")

    options = ui_override.get("options")

    default = variable.get("default", 0)

    if default is None:
        default = 0 if var_type in ("float", "int") else ""

    min_val = variable.get("min")

    max_val = variable.get("max")

    if widget is None:
        if var_type == "bool":
            widget = "switch"

        elif var_type == "str":
            widget = "dropdown"

        elif (min_val is not None and max_val is not None) or ui_override.get("widget") == "slider":
            widget = "slider"

        else:
            widget = "spinbox"

    if step is None:
        step = 1 if var_type == "int" else 0.01

    if options is None and var_type == "str":
        options = variable.get("options", [])

    return ControlSpec(
        label=label,
        widget=widget,
        default=default,
        min_val=min_val,
        max_val=max_val,
        step=step,
        options=options if options else [],
        description=description,
    )


# from format.py
def format_node_value(value: Any, format_spec: str | None = None) -> str:
    if value is None:
        return "N/A"
    if not format_spec:
        return str(value)
    try:
        return f"{value:{format_spec}}"
    except (ValueError, TypeError):
        return str(value)
