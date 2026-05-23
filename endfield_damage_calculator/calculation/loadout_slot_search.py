#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 1–4 件装备控制四格中哪些部位参与遍历。"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterator

# 固定格：各部位目录排序后的第一件（与 build_optimizer_search_plan 中 catalog 顺序一致）


@dataclass(frozen=True)
class VaryingSlotMask:
    """四格配装中哪些部位参与笛卡尔积。"""

    chest: bool
    gloves: bool
    accessory_a: bool
    accessory_b: bool


def varying_slot_mask_from_count(slot_count: int) -> VaryingSlotMask:
    """
    将 1–4 映射为遍历格：护甲 → 护手 → 配件A → 配件B。

    1 件：仅护甲变动，其余三格固定；
    4 件：四格全部变动（全套配装搜索）。
    """
    count = max(1, min(4, int(slot_count)))
    return VaryingSlotMask(
        chest=count >= 1,
        gloves=count >= 2,
        accessory_a=count >= 3,
        accessory_b=count >= 4,
    )


def baseline_loadout_from_catalog(
    equipment_catalog: dict[str, list[dict]],
) -> tuple[dict, dict, dict, dict]:
    """各部位取列表首件作为固定格（目录应已按剪枝优先级排序）。"""
    chests = equipment_catalog.get("chest") or []
    gloves = equipment_catalog.get("gloves") or []
    accessories = equipment_catalog.get("accessories") or []
    if not chests or not gloves or not accessories:
        raise ValueError("装备目录三部位均需至少一件。")
    base_acc = accessories[0]
    return (chests[0], gloves[0], base_acc, base_acc)


def count_loadout_combinations_for_mask(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool,
    mask: VaryingSlotMask,
    baseline: tuple[dict, dict, dict, dict],
) -> int:
    """统计与 iter 一致的配装组合数。"""
    return sum(1 for _ in iter_loadout_combinations_for_mask(
        equipment_catalog,
        allow_duplicate_accessory=allow_duplicate_accessory,
        mask=mask,
        baseline=baseline,
    ))


def iter_loadout_combinations_for_mask(
    equipment_catalog: dict[str, list[dict]],
    *,
    allow_duplicate_accessory: bool,
    mask: VaryingSlotMask,
    baseline: tuple[dict, dict, dict, dict],
) -> Iterator[tuple[dict, dict, dict, dict]]:
    """按 mask 生成四格配装；未勾选部位使用 baseline。"""
    chests = list(equipment_catalog.get("chest") or [])
    gloves = list(equipment_catalog.get("gloves") or [])
    accessories = list(equipment_catalog.get("accessories") or [])
    if not chests or not gloves or not accessories:
        return

    chest_choices = chests if mask.chest else [baseline[0]]
    glove_choices = gloves if mask.gloves else [baseline[1]]

    if mask.accessory_a and mask.accessory_b:
        acc_a_choices = accessories
        acc_b_choices = accessories
        for chest, glove, acc_a, acc_b in product(
            chest_choices, glove_choices, acc_a_choices, acc_b_choices
        ):
            if not allow_duplicate_accessory and acc_a.get("名称") == acc_b.get("名称"):
                continue
            yield (chest, glove, acc_a, acc_b)
        return

    if mask.accessory_a and not mask.accessory_b:
        for chest, glove, acc_a in product(chest_choices, glove_choices, accessories):
            yield (chest, glove, acc_a, baseline[3])
        return

    for chest, glove in product(chest_choices, glove_choices):
        yield (chest, glove, baseline[2], baseline[3])
