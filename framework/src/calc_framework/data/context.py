#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""DataContext 类型定义 — 通用数据上下文类型。"""

from typing import Any, TypedDict


class DataContext(TypedDict, total=False):
    """DAG 求值上下文 TypedDict。

    顶层 key 约定：
    - ``character``：角色数据
    - ``weapon``：武器数据
    - ``equipment``：装备数据
    - ``enemy``：敌方数据
    - ``computed``：框架内部计算值

    上述 key 均为可选（total=False），适配器可按需填充，
    也可追加非标准 key（如 ``custom``）。
    """

    character: dict[str, Any]
    weapon: dict[str, Any]
    equipment: dict[str, Any]
    enemy: dict[str, Any]
    computed: dict[str, Any]


def make_context(**kwargs: Any) -> dict[str, Any]:
    """创建 DataContext 的简便工厂。

    自动初始化 5 个标准 key 为空字典，额外 keyword 可覆盖或追加。
    """
    ctx: dict[str, Any] = {
        "character": {},
        "weapon": {},
        "equipment": {},
        "enemy": {},
        "computed": {},
    }
    ctx.update(kwargs)
    return ctx
