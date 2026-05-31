#!/usr/bin/env python3
"""手动场外 buff 包。"""

from calc_engine.endfield.calc.manual_buff.model import (
    MANUAL_BUFF_ZONE_OPTIONS,
    ManualBuffEntry,
    build_active_keys_from_counts,
    empty_buff_dict,
    get_buffs_for_key,
    set_buffs_for_key,
)
