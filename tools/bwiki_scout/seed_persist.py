#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""seed 脚本持久化接缝（解析/写入 _SEED_* 列表）。"""



from __future__ import annotations



import ast

import pprint

import re

from pathlib import Path

from typing import Any





def _flatten_seed_list(raw: list[Any]) -> list[dict[str, Any]]:

    """兼容旧版 `[[{...}, ...]]` 误嵌套为单层列表。"""

    if len(raw) == 1 and isinstance(raw[0], list):

        inner = raw[0]

        if inner and isinstance(inner[0], dict):

            return inner

    return [item for item in raw if isinstance(item, dict)]





def _load_seed_list(seed_path: Path, marker: str) -> list[dict[str, Any]]:

    text = seed_path.read_text(encoding="utf-8")

    match = re.search(

        rf"{marker}\s*=\s*(\[.*?\])\s*\ndef\s+main\s*\(",

        text,

        re.DOTALL,

    )

    if not match:

        raise ValueError(f"无法解析 {marker}: {seed_path}")

    return _flatten_seed_list(ast.literal_eval(match.group(1)))





def _write_seed_list(seed_path: Path, marker: str, specs: list[dict[str, Any]]) -> None:

    text = seed_path.read_text(encoding="utf-8")

    formatted = pprint.pformat(specs, width=100, sort_dicts=False)

    new_text, n = re.subn(

        rf"{marker}\s*=\s*\[.*?\]\s*\n\n\ndef\s+main\s*\(",

        f"{marker} = {formatted}\n\n\ndef main(",

        text,

        count=1,

        flags=re.DOTALL,

    )

    if n != 1:

        raise ValueError(f"未能替换 {marker}: {seed_path}")

    seed_path.write_text(new_text, encoding="utf-8")





def load_seed_character_specs(seed_path: Path) -> list[dict[str, Any]]:

    return _load_seed_list(seed_path, "_SEED_CHARACTERS")





def write_seed_character_specs(seed_path: Path, specs: list[dict[str, Any]]) -> None:

    _write_seed_list(seed_path, "_SEED_CHARACTERS", specs)





def load_seed_weapon_specs(seed_path: Path) -> list[dict[str, Any]]:

    return _load_seed_list(seed_path, "_SEED_WEAPONS")





def write_seed_weapon_specs(seed_path: Path, specs: list[dict[str, Any]]) -> None:

    _write_seed_list(seed_path, "_SEED_WEAPONS", specs)





def replace_seed_specs(

    specs: list[dict[str, Any]],

    updates: dict[str, dict[str, Any]],

    *,

    admin_first: bool = False,

) -> list[dict[str, Any]]:

    """按 name 覆盖或追加 seed 条目。"""

    by_name = {s["name"]: s for s in specs}

    for name, spec in updates.items():

        by_name[name] = spec

    if admin_first:

        return [by_name[n] for n in sorted(by_name.keys(), key=lambda x: (x != "管理员", x))]

    return [by_name[n] for n in sorted(by_name.keys())]

