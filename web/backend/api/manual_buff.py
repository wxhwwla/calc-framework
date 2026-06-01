# SPDX-License-Identifier: AGPL-3.0
from fastapi import APIRouter

router = APIRouter(prefix="/api/manual-buff", tags=["manual-buff"])


@router.get("/consumable-presets")
def list_consumable_presets() -> list[dict[str, object]]:
    from games.endfield.calc.manual_buff.consumable_presets import (
        CONSUMABLE_PRESETS,
        list_consumable_preset_names,
    )

    names = list_consumable_preset_names()
    return [
        {
            "name": name,
            "entries": [
                {"effect_type": entry["effect_type"], "value": float(entry["value"])}
                for entry in next(entries for n, entries in CONSUMABLE_PRESETS if n == name)
            ],
        }
        for name in names
    ]
