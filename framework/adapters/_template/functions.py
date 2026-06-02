# SPDX-License-Identifier: AGPL-3.0
"""DAG 自定义函数 — 替换为你的游戏公式。

此文件在 meta.json 的 "functions" 字段中注册。
每个顶层函数通过函数名自动注册到 DAG 沙箱。
"""

from __future__ import annotations


def your_function(param1: float, param2: float) -> float:
    """你的游戏公式。

    Args:
        param1: 参数 1
        param2: 参数 2

    Returns:
        float: 计算结果
    """
    # TODO: 替换为实际公式
    return param1 * param2
