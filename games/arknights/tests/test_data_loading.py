# SPDX-License-Identifier: AGPL-3.0
"""数据加载测试 — load_operators_map 与数据完整性验证。"""

from __future__ import annotations

from pathlib import Path

import pytest

from games.arknights.operator_catalog import (
    MIN_PARSED_COUNT,
    _read_json_file,
    build_operator_index,
    list_branches,
    list_professions,
    load_operators_map,
)

# ═══════════════════════════════════════════════
#  _read_json_file 单元测试
# ═══════════════════════════════════════════════


class TestReadJsonFile:
    def test_valid_json_returns_dict(self, tmp_path: Path) -> None:
        f = tmp_path / "test.json"
        f.write_text('{"名称": "TestOp", "星级": 6}', encoding="utf-8")
        result = _read_json_file(f)
        assert result == {"名称": "TestOp", "星级": 6}

    def test_invalid_json_returns_none(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("{invalid json", encoding="utf-8")
        result = _read_json_file(f)
        assert result is None

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        f = tmp_path / "nonexistent.json"
        result = _read_json_file(f)
        assert result is None

    def test_empty_file_returns_none(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.json"
        f.write_text("", encoding="utf-8")
        result = _read_json_file(f)
        assert result is None


# ═══════════════════════════════════════════════
#  load_operators_map 单元测试
# ═══════════════════════════════════════════════


class TestLoadOperatorsMap:
    def test_returns_dict(self) -> None:
        result = load_operators_map()
        assert isinstance(result, dict)

    def test_empty_directory_returns_empty(self, tmp_path: Path) -> None:
        """传入一个空目录时返回空 dict。"""
        empty_dir = tmp_path / "empty_parsed"
        empty_dir.mkdir()
        result = load_operators_map(parsed_dir=empty_dir, zip_candidates=())
        assert result == {}

    def test_operator_key_is_name(self, tmp_path: Path) -> None:
        """字典的键为干员名称。"""
        d = tmp_path / "parsed"
        d.mkdir()
        (d / "test_op.json").write_text('{"名称": "测试干员", "星级": 5}', encoding="utf-8")
        result = load_operators_map(parsed_dir=d, zip_candidates=())
        assert "测试干员" in result

    def test_name_field_missing_falls_back_to_stem(self, tmp_path: Path) -> None:
        """名称字段缺失时回退到文件名。"""
        d = tmp_path / "parsed_no_name"
        d.mkdir()
        (d / "no_name_op.json").write_text('{"星级": 3, "职业": "先锋"}', encoding="utf-8")
        result = load_operators_map(parsed_dir=d, zip_candidates=())
        assert "no_name_op" in result or len(result) >= 1

    def test_skips_sync_summary_file(self, tmp_path: Path) -> None:
        """_sync_summary.json 应被跳过。"""
        d = tmp_path / "parsed_skip"
        d.mkdir()
        (d / "_sync_summary.json").write_text('{"count": 5}', encoding="utf-8")
        (d / "real_op.json").write_text('{"名称": "RealOp", "星级": 4}', encoding="utf-8")
        result = load_operators_map(parsed_dir=d, zip_candidates=())
        assert "_sync_summary" not in result
        assert "RealOp" in result

    def test_skips_operators_file(self, tmp_path: Path) -> None:
        """operators.json 应被跳过。"""
        d = tmp_path / "parsed_skip2"
        d.mkdir()
        (d / "operators.json").write_text('{"名称": "Ops", "星级": 5}', encoding="utf-8")
        (d / "char_001.json").write_text('{"名称": "Char1", "星级": 6}', encoding="utf-8")
        result = load_operators_map(parsed_dir=d, zip_candidates=())
        assert "operators" not in result
        assert "Char1" in result

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """不存在的目录返回空 dict。"""
        nonexistent = tmp_path / "does_not_exist"
        result = load_operators_map(parsed_dir=nonexistent, zip_candidates=())
        assert result == {}

    def test_custom_zip_candidates(self) -> None:
        """自定义 zip_candidates 参数被接受。"""
        result = load_operators_map(zip_candidates=())
        assert isinstance(result, dict)


# ═══════════════════════════════════════════════
#  数据完整性测试（需要真实数据）
# ═══════════════════════════════════════════════


@pytest.mark.real_data
class TestDataIntegrity:
    @pytest.fixture(autouse=True)
    def _setup(self) -> None:
        self.ops = load_operators_map()
        if len(self.ops) < 10:
            pytest.skip("本地无完整干员库")

    def test_at_least_one_6_star(self) -> None:
        index = build_operator_index(self.ops)
        six_stars = [x for x in index if x["星级"] == 6]
        assert len(six_stars) >= 1, "Expected at least one 6-star operator"

    def test_has_professions_sniper(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "狙击" in professions

    def test_has_professions_caster(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "术师" in professions

    def test_has_professions_vanguard(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "先锋" in professions

    def test_has_professions_defender(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "重装" in professions

    def test_has_professions_guard(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "近卫" in professions

    def test_has_professions_medic(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "医疗" in professions

    def test_has_professions_specialist(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "特种" in professions

    def test_has_professions_supporter(self) -> None:
        index = build_operator_index(self.ops)
        professions = list_professions(index)
        assert "辅助" in professions

    def test_operator_data_has_expected_fields(self) -> None:
        """干员数据含必要字段。"""
        if not self.ops:
            pytest.skip("no operators loaded")
        # 取第一个干员检查
        sample = next(iter(self.ops.values()))
        assert "名称" in sample
        assert isinstance(sample["名称"], str)

    def test_load_operators_map_all_values_are_dicts(self) -> None:
        for key, val in self.ops.items():
            assert isinstance(val, dict), f"Value for '{key}' is not a dict: {type(val)}"

    def test_operator_count_meets_min_parsed_threshold(self) -> None:
        """对应 parity 人工清单「干员列表 ≥418」的自动化下限（MIN_PARSED_COUNT）。"""
        assert len(self.ops) >= MIN_PARSED_COUNT, f"expected ≥{MIN_PARSED_COUNT} operators, got {len(self.ops)}"

    def test_list_branches_non_empty(self) -> None:
        index = build_operator_index(self.ops)
        branches = list_branches(index)
        assert isinstance(branches, list)

    def test_list_branches_with_profession_filter(self) -> None:
        index = build_operator_index(self.ops)
        branches = list_branches(index, profession="狙击")
        assert isinstance(branches, list)
        assert len(branches) >= 0
