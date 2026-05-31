"""tools.ocr.mapper 单元测试。"""

from __future__ import annotations


from tools.ocr.mapper import OcrMapper, OcrMatchResult


class TestOcrMatchResult:
    def test_invalid_by_default(self) -> None:
        r = OcrMatchResult()
        assert not r.is_valid
        assert r.summary() == "未匹配到有效数据"

    def test_valid_with_char_and_weapon(self) -> None:
        r = OcrMatchResult(char_name="秋栗", weapon_name="逐鳞", char_match_score=0.95, char_level=80)
        assert r.is_valid
        assert "秋栗" in r.summary()
        assert "逐鳞" in r.summary()

    def test_to_loadout_preset_dict(self) -> None:
        r = OcrMatchResult(
            char_name="秋栗",
            weapon_name="逐鳞",
            char_level=80,
            weapon_level=70,
            trust_level=4,
            skill_levels=(10, 10, 8),
        )
        d = r.to_loadout_preset_dict()
        assert d["schema"] == "endfield_loadout_preset_v2"
        assert d["char_name"] == "秋栗"
        assert d["weapon_name"] == "逐鳞"
        assert d["char_level"] == 80
        assert d["weapon_level"] == 70
        assert d["trust_level"] == 4
        assert d["skill_levels"] == [10, 10, 8]

    def test_partial_to_dict(self) -> None:
        r = OcrMatchResult(char_name="A", weapon_name="B")
        d = r.to_loadout_preset_dict()
        assert d["char_level"] == 1  # default fallback
        assert d["weapon_level"] == 1


class TestOcrMapper:
    def test_fuzzy_match_character(self) -> None:
        mapper = OcrMapper()
        mapper._char_names = ["秋栗", "陈", "佩丽卡", "狼卫"]
        name, score = mapper.match_character("秋栗")
        assert name == "秋栗"
        assert score > 0.9

    def test_fuzzy_match_weapon(self) -> None:
        mapper = OcrMapper()
        mapper._weapon_names = ["逐鳞", "凛冬", "炎华", "星鎏"]
        name, score = mapper.match_weapon("逐鳞")
        assert name == "逐鳞"
        assert score > 0.9

    def test_fuzzy_match_typo(self) -> None:
        mapper = OcrMapper()
        mapper._char_names = ["秋栗", "佩丽卡"]
        name, score = mapper.match_character("秋票")
        assert name == "秋栗"
        assert score > 0.4

    def test_no_match(self) -> None:
        mapper = OcrMapper()
        mapper._char_names = ["秋栗", "陈"]
        name, score = mapper.match_character("齐宣王")
        assert name == ""
        assert score == 0.0

    def test_extract_number_from_text(self) -> None:
        mapper = OcrMapper()
        val = mapper._extract_number("80")
        assert val == 80

    def test_extract_number_out_of_range(self) -> None:
        mapper = OcrMapper()
        val = mapper._extract_number("999")
        assert val is None

    def test_map_texts_full(self) -> None:
        mapper = OcrMapper()
        mapper._char_names = ["秋栗", "陈"]
        mapper._weapon_names = ["逐鳞", "凛冬"]

        result = mapper.map_texts([
            ("秋栗", 0.95, None),
            ("逐鳞", 0.88, None),
            ("80", 0.99, None),
        ])
        assert result.is_valid
        assert result.char_name == "秋栗"
        assert result.weapon_name == "逐鳞"

    def test_map_texts_missing_weapon(self) -> None:
        mapper = OcrMapper()
        mapper._char_names = ["秋栗"]
        mapper._weapon_names = ["逐鳞"]

        result = mapper.map_texts([
            ("秋栗", 0.90, None),
        ])
        assert not result.is_valid
        assert result.char_name == "秋栗"
        assert result.weapon_name == ""

    def test_map_texts_empty(self) -> None:
        mapper = OcrMapper()
        mapper._char_names = ["秋栗"]
        result = mapper.map_texts([])
        assert not result.is_valid

    def test_map_texts_deduplicates_numbers(self) -> None:
        """数字不应被误识别为角色名或武器名。"""
        mapper = OcrMapper()
        mapper._char_names = ["秋栗"]
        mapper._weapon_names = ["逐鳞", "凛冬"]
        result = mapper.map_texts([
            ("80", 0.99, None),
            ("1", 0.95, None),
        ])
        assert not result.is_valid
        assert result.char_name == ""
        assert result.weapon_name == ""
        assert result.char_level == 80
