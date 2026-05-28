#!/usr/bin/env python3
"""碰撞检测模块 — 检测 QGraphicsItem 之间的矩形重叠。

当前为骨架，后续版本将集成到 LayoutCanvasPanel 的实时检测循环中。
"""

from __future__ import annotations

from typing import List, Tuple

from PySide6.QtCore import QRectF
from PySide6.QtWidgets import QGraphicsItem


def find_collisions(
    items: List[QGraphicsItem],
) -> List[Tuple[QGraphicsItem, QGraphicsItem]]:
    """返回所有相互重叠的控件对。

    Args:
        items: 画布上的 QGraphicsItem 列表

    Returns:
        重叠对列表，每项为 (item_a, item_b)
    """
    collisions: List[Tuple[QGraphicsItem, QGraphicsItem]] = []
    for i, a in enumerate(items):
        rect_a = a.sceneBoundingRect()
        for b in items[i + 1 :]:
            rect_b = b.sceneBoundingRect()
            if rect_a.intersects(rect_b):
                collisions.append((a, b))
    return collisions


def has_collisions(items: List[QGraphicsItem]) -> bool:
    """是否有任何碰撞。"""
    return len(find_collisions(items)) > 0
