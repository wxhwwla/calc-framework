#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

四格配装搜索：用户可固定 0–4 件装备，未固定部位遍历 catalog 候选。



与旧版「遍历件数 1–4」（从护甲起连续开放遍历格）不同；``varying_slot_mask_from_count`` 仅保留给旧测试/迁移。

"""



from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import product

SLOT_KEYS = ("chest", "gloves", "accessory_a", "accessory_b")





@dataclass(frozen=True)

class VaryingSlotMask:

    """哪些部位参与笛卡尔积（True=遍历，False=固定）。"""



    chest: bool

    gloves: bool

    accessory_a: bool

    accessory_b: bool





@dataclass(frozen=True)

class FixedLoadoutSelection:

    """

    用户固定的配装；字段为 None 表示该格遍历 catalog。



    四格均可为 None（全套遍历）；亦可固定 1–4 件，其余格遍历。

    """



    chest: dict | None = None

    gloves: dict | None = None

    accessory_a: dict | None = None

    accessory_b: dict | None = None



    def to_mask(self) -> VaryingSlotMask:

        return VaryingSlotMask(

            chest=self.chest is None,

            gloves=self.gloves is None,

            accessory_a=self.accessory_a is None,

            accessory_b=self.accessory_b is None,

        )
        """to mask。"""



    def fixed_count(self) -> int:

        return sum(1 for item in (self.chest, self.gloves, self.accessory_a, self.accessory_b) if item is not None)
        """fixed count。"""



    def signature_token(self) -> str:

        """写入 run_signature 的固定格摘要。"""



        def _part(key: str, item: dict | None) -> str:

            if item is None:

                return f"{key}:vary"

            return f"{key}:{item.get('名称', '')}"
            """part。"""



        return "|".join(

            [

                _part("c", self.chest),

                _part("g", self.gloves),

                _part("a1", self.accessory_a),

                _part("a2", self.accessory_b),

            ]

        )





def varying_slot_mask_from_count(slot_count: int) -> VaryingSlotMask:

    """

    旧语义：1–4 表示从护甲起连续开放遍历格（其余格固定为首件）。



    新 GUI 请使用 ``FixedLoadoutSelection``；本函数仅供兼容测试。

    """

    count = max(1, min(4, int(slot_count)))

    return VaryingSlotMask(

        chest=count >= 1,

        gloves=count >= 2,

        accessory_a=count >= 3,

        accessory_b=count >= 4,

    )





def selection_from_legacy_slot_count(

    equipment_catalog: dict[str, list[dict]],

    slot_count: int,

) -> FixedLoadoutSelection:

    """将旧版「遍历件数 1–4」转为等价的固定/遍历选择。"""

    mask = varying_slot_mask_from_count(slot_count)

    baseline = baseline_loadout_from_catalog(equipment_catalog)

    return FixedLoadoutSelection(

        chest=None if mask.chest else baseline[0],

        gloves=None if mask.gloves else baseline[1],

        accessory_a=None if mask.accessory_a else baseline[2],

        accessory_b=None if mask.accessory_b else baseline[3],

    )





def baseline_loadout_from_catalog(

    equipment_catalog: dict[str, list[dict]],

) -> tuple[dict, dict, dict, dict]:

    """各部位取列表首件（目录应已按剪枝优先级排序）。"""

    chests = equipment_catalog.get("chest") or []

    gloves = equipment_catalog.get("gloves") or []

    accessories = equipment_catalog.get("accessories") or []

    if not chests or not gloves or not accessories:

        raise ValueError("装备目录三部位均需至少一件。")

    base_acc = accessories[0]

    return (chests[0], gloves[0], base_acc, base_acc)





def _choices_for_slot(

    catalog_items: list[dict],

    fixed_item: dict | None,

) -> list[dict]:

    if fixed_item is not None:

        return [fixed_item]

    return list(catalog_items)
    """choices for slot。"""





def count_loadout_combinations_for_selection(

    equipment_catalog: dict[str, list[dict]],

    *,

    selection: FixedLoadoutSelection,

    allow_duplicate_accessory: bool,

) -> int:

    """统计与 ``iter_loadout_combinations_for_selection`` 一致的配装组合数。"""

    return sum(

        1

        for _ in iter_loadout_combinations_for_selection(

            equipment_catalog,

            selection=selection,

            allow_duplicate_accessory=allow_duplicate_accessory,

        )

    )





def iter_loadout_combinations_for_selection(

    equipment_catalog: dict[str, list[dict]],

    *,

    selection: FixedLoadoutSelection,

    allow_duplicate_accessory: bool,

) -> Iterator[tuple[dict, dict, dict, dict]]:

    """按固定/遍历选择生成四格配装。"""

    chests = list(equipment_catalog.get("chest") or [])

    gloves = list(equipment_catalog.get("gloves") or [])

    accessories = list(equipment_catalog.get("accessories") or [])

    if not chests or not gloves or not accessories:

        return



    chest_choices = _choices_for_slot(chests, selection.chest)

    glove_choices = _choices_for_slot(gloves, selection.gloves)

    acc_a_choices = _choices_for_slot(accessories, selection.accessory_a)

    acc_b_choices = _choices_for_slot(accessories, selection.accessory_b)



    if not chest_choices or not glove_choices or not acc_a_choices or not acc_b_choices:

        return



    for chest, glove, acc_a, acc_b in product(chest_choices, glove_choices, acc_a_choices, acc_b_choices):

        if not allow_duplicate_accessory and acc_a.get("名称") == acc_b.get("名称"):

            continue

        yield (chest, glove, acc_a, acc_b)





def count_loadout_combinations(

    equipment_catalog: dict[str, list[dict]],

    *,

    allow_duplicate_accessory: bool = True,

    selection: FixedLoadoutSelection | None = None,

    varying_slot_count: int | None = None,

) -> int:

    """统计配装组合数；优先 ``selection``，否则回退旧 ``varying_slot_count``。"""

    if selection is None:

        if varying_slot_count is None:

            varying_slot_count = 4

        selection = selection_from_legacy_slot_count(equipment_catalog, varying_slot_count)

    return count_loadout_combinations_for_selection(

        equipment_catalog,

        selection=selection,

        allow_duplicate_accessory=allow_duplicate_accessory,

    )





def iter_loadout_combinations_for_mask(

    equipment_catalog: dict[str, list[dict]],

    *,

    allow_duplicate_accessory: bool,

    mask: VaryingSlotMask,

    baseline: tuple[dict, dict, dict, dict],

) -> Iterator[tuple[dict, dict, dict, dict]]:

    """兼容旧 mask+baseline API。"""

    selection = FixedLoadoutSelection(

        chest=None if mask.chest else baseline[0],

        gloves=None if mask.gloves else baseline[1],

        accessory_a=None if mask.accessory_a else baseline[2],

        accessory_b=None if mask.accessory_b else baseline[3],

    )

    yield from iter_loadout_combinations_for_selection(

        equipment_catalog,

        selection=selection,

        allow_duplicate_accessory=allow_duplicate_accessory,

    )





def count_loadout_combinations_for_mask(

    equipment_catalog: dict[str, list[dict]],

    *,

    allow_duplicate_accessory: bool,

    mask: VaryingSlotMask,

    baseline: tuple[dict, dict, dict, dict],

) -> int:

    return sum(

        1

        for _ in iter_loadout_combinations_for_mask(

            equipment_catalog,

            allow_duplicate_accessory=allow_duplicate_accessory,

            mask=mask,

            baseline=baseline,

        )

    )
    """count loadout combinations for mask。"""

