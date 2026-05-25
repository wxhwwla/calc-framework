#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确认刷新与右侧乘区展示的统一输入（LoadoutState + catalog + 武器候选）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from calculation.loadout_optimizer import WeaponCandidate
from data.game_data_facade import GameDataFacade
from .loadout_state import LoadoutState


@dataclass(frozen=True)
class DisplayRequest:
    """一次确认刷新所需的全部非 CTk 输入。"""

    loadout: LoadoutState
    equipment_catalog: dict[str, list[dict[str, Any]]]
    preview_weapon_candidates: tuple[WeaponCandidate, ...]


def build_display_request(
    loadout: LoadoutState,
    game_data: GameDataFacade,
    *,
    preview_weapon_candidates: list[WeaponCandidate],
) -> DisplayRequest:
    return DisplayRequest(
        loadout=loadout,
        equipment_catalog=game_data.equipment_catalog(loadout.equipment_scope_label),
        preview_weapon_candidates=tuple(preview_weapon_candidates),
    )
