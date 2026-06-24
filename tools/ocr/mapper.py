#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

OCR 输出 → 计算器数据映射层。



将 OCR 识别的文本（角色名、武器名、等级等）与游戏数据匹配，

输出 ``LoadoutPreset`` 兼容的 dict，供 GUI 一键填入计算器。



用法:

    from tools.ocr.mapper import OcrMapper



    mapper = OcrMapper()

    result = mapper.map_texts([

        ("秋栗", 0.95, "character_panel"),

        ("逐鳞", 0.88, "weapon_panel"),

        ("80", 0.99, None),

    ])

    print(result.to_dict())

"""

from __future__ import annotations

import difflib
import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OcrMatchResult:
    """OCR 文本匹配结果。"""

    char_name: str = ""

    char_match_score: float = 0.0

    weapon_name: str = ""

    weapon_match_score: float = 0.0

    char_level: int = 0

    weapon_level: int = 0

    trust_level: int = 0

    skill_levels: tuple[int, int, int] = (0, 0, 0)

    @property
    def is_valid(self) -> bool:
        """is_valid 实现。"""
        return bool(self.char_name and self.weapon_name)

    def to_loadout_preset_dict(self) -> dict[str, Any]:
        """转换为 LoadoutPreset 兼容的 dict。"""

        return {
            "schema": "endfield_loadout_preset_v2",
            "char_name": self.char_name,
            "weapon_name": self.weapon_name,
            "char_level": self.char_level or 1,
            "weapon_level": self.weapon_level or 1,
            "trust_level": self.trust_level,
            "skill_levels": list(self.skill_levels),
            "calculation_mode": "zone_snapshot",
            "weapon_scope": "当前武器",
            "equipment_scope": "全部装备",
            "fixed_equipment_names": {
                "chest": None,
                "gloves": None,
                "accessory_a": None,
                "accessory_b": None,
            },
            "multi_skill_counts": {},
            "use_manual_multi_skill_counts": False,
            "weapon_normal_levels": [],
            "weapon_special_states": [],
        }

    def summary(self) -> str:
        """summary 实现。"""
        parts = []

        if self.char_name:
            parts.append(f"角色: {self.char_name} (匹配度 {self.char_match_score:.0%})")

        if self.weapon_name:
            parts.append(f"武器: {self.weapon_name} (匹配度 {self.weapon_match_score:.0%})")

        if self.char_level:
            parts.append(f"角色等级: {self.char_level}")

        if self.weapon_level:
            parts.append(f"武器等级: {self.weapon_level}")

        if self.trust_level:
            parts.append(f"信赖: {self.trust_level}")

        return " | ".join(parts) if parts else "未匹配到有效数据"


class OcrMapper:
    """OCR 文本 → 计算器数据映射器。"""

    def __init__(self) -> None:
        self._char_names: list[str] = []

        self._weapon_names: list[str] = []

        self._load_game_data()

    def _load_game_data(self) -> None:
        """_load_game_data 实现。"""
        try:
            from games.endfield.data_loading.loader import get_characters, get_weapons

            chars = get_characters()

            weapons = get_weapons()

            self._char_names = [c.get("名称", "") for c in chars if c.get("名称")]

            self._weapon_names = [w.get("名称", "") for w in weapons if w.get("名称")]

        except Exception:
            logger.warning("加载角色/武器名称列表失败", exc_info=True)
            self._char_names = []
            self._weapon_names = []

    @property
    def characters_loaded(self) -> bool:
        """characters_loaded 实现。"""
        return len(self._char_names) > 0

    @property
    def weapons_loaded(self) -> bool:
        """weapons_loaded 实现。"""
        return len(self._weapon_names) > 0

    def match_character(self, text: str, min_score: float = 0.4) -> tuple[str, float]:
        """模糊匹配角色名。"""

        return self._fuzzy_match(text, self._char_names, min_score)

    def match_weapon(self, text: str, min_score: float = 0.4) -> tuple[str, float]:
        """模糊匹配武器名。"""

        return self._fuzzy_match(text, self._weapon_names, min_score)

    def _fuzzy_match(self, text: str, candidates: list[str], min_score: float) -> tuple[str, float]:
        """_fuzzy_match 实现。"""
        text = text.strip()

        if not text or not candidates:
            return ("", 0.0)

        matches = difflib.get_close_matches(text, candidates, n=1, cutoff=min_score)

        if matches:
            score = difflib.SequenceMatcher(None, text, matches[0]).ratio()

            return (matches[0], score)

        # Try substring match

        for c in candidates:
            if text in c or c in text:
                score = difflib.SequenceMatcher(None, text, c).ratio()

                if score >= min_score:
                    return (c, score)

        return ("", 0.0)

    def _extract_number(self, text: str) -> int | None:
        """从文本中提取数字。"""

        nums = re.findall(r"\d+", text.strip())

        if nums:
            val = int(nums[0])

            if 1 <= val <= 90:
                return val

        return None

    def map_texts(
        self,
        ocr_texts: list[tuple[str, float, str | None]],
    ) -> OcrMatchResult:
        """映射一组 OCR 文本到配装数据。



        Args:

            ocr_texts: 每个元素为 (text, confidence, region_name)

                        region_name 可选，如 "character_panel"、"weapon_panel"

                        region_name 为 None 时自动推断



        Returns:

            OcrMatchResult 匹配结果

        """

        result = OcrMatchResult()

        numbers: list[int] = []

        raw_texts: list[str] = []

        for text, _conf, _region in ocr_texts:
            text = text.strip()

            if not text:
                continue

            raw_texts.append(text)

            # Try to extract numbers

            num = self._extract_number(text)

            if num is not None:
                numbers.append(num)

                continue

            # Try character name match

            if not result.char_name:
                name, score = self.match_character(text)

                if name:
                    result.char_name = name

                    result.char_match_score = score

                    continue

            # Try weapon name match

            if not result.weapon_name:
                name, score = self.match_weapon(text)

                if name:
                    result.weapon_name = name

                    result.weapon_match_score = score

                    continue

        # Need to retry if level detection skipped name detection

        for text, _conf, _region in ocr_texts:
            text = text.strip()

            if not text:
                continue

            if not result.char_name:
                name, score = self.match_character(text, min_score=0.3)

                if name:
                    result.char_name = name

                    result.char_match_score = score

        for text, _conf, _region in ocr_texts:
            text = text.strip()

            if not text:
                continue

            if not result.weapon_name:
                name, score = self.match_weapon(text, min_score=0.3)

                if name:
                    result.weapon_name = name

                    result.weapon_match_score = score

        # Assign numbers to levels (heuristic: higher number = char/weapon level)

        numbers = sorted(set(numbers), reverse=True)

        level_candidates = [n for n in numbers if 1 <= n <= 90]

        trust_candidates = [n for n in level_candidates if 1 <= n <= 50]

        if level_candidates:
            if len(level_candidates) >= 2:
                result.char_level = level_candidates[0]

                result.weapon_level = level_candidates[1]

            else:
                result.char_level = level_candidates[0]

                result.weapon_level = level_candidates[0]

        if trust_candidates:
            result.trust_level = (
                min(t for t in trust_candidates if t <= 50) if any(t <= 10 for t in trust_candidates) else 0
            )

        return result

    def map_region_texts(
        self,
        region_map: dict[str, list[str]],
    ) -> OcrMatchResult:
        """按区域名称分组映射 OCR 文本。



        Args:

            region_map: {region_name: [texts...]}

                        支持 region: character_panel, weapon_panel, skill_panel, zone_values



        Returns:

            OcrMatchResult

        """

        flat: list[tuple[str, float, str | None]] = []

        for region, texts in region_map.items():
            for t in texts:
                flat.append((t, 0.8, region))

        return self.map_texts(flat)


def map_texts(texts: list[str]) -> OcrMatchResult:
    """快捷方式：从纯文本列表映射（自动推断）。"""

    mapper = OcrMapper()

    return mapper.map_texts([(t, 0.8, None) for t in texts])
