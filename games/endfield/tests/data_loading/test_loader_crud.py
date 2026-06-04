# SPDX-License-Identifier: AGPL-3.0
"""覆盖 loader_crud / web_search_bridge。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from games.endfield.data_loading.loader_crud import (
    check_and_save_characters,
    check_and_save_weapons,
    save_characters,
    save_equipments,
    save_weapons,
)
from games.endfield.data_loading.web_search_bridge import enrich_search_request_fields

# ── loader_crud.py ───────────────────────────────────────────────────────


class TestSaveCharacters:
    """save_characters / save_weapons / save_equipments / check_and_save_*。"""

    @patch("games.endfield.data_loading.loader_crud.get_resource_path")
    @patch("builtins.open")
    @patch("games.endfield.data_loading.loader_crud.reload_characters")
    def test_save_characters_success(self, mock_reload: MagicMock, mock_open: MagicMock, mock_path: MagicMock) -> None:
        mock_path.return_value = "dummy.json"
        result = save_characters([{"名称": "测试"}])
        assert result is True
        mock_open.assert_called_once()
        mock_reload.assert_called_once()

    @patch("games.endfield.data_loading.loader_crud.get_resource_path")
    @patch("builtins.open")
    @patch("games.endfield.data_loading.loader_crud.reload_weapons")
    def test_save_weapons_success(self, mock_reload: MagicMock, mock_open: MagicMock, mock_path: MagicMock) -> None:
        mock_path.return_value = "dummy.json"
        result = save_weapons([{"名称": "测试武器"}])
        assert result is True
        mock_open.assert_called_once()
        mock_reload.assert_called_once()

    @patch("games.endfield.data_loading.loader_crud.get_resource_path")
    @patch("builtins.open")
    @patch("games.endfield.data_loading.loader_crud.reload_equipments")
    def test_save_equipments_success(self, mock_reload: MagicMock, mock_open: MagicMock, mock_path: MagicMock) -> None:
        mock_path.return_value = "dummy.json"
        result = save_equipments([{"名称": "测试装备"}])
        assert result is True
        mock_open.assert_called_once()
        mock_reload.assert_called_once()

    @patch("games.endfield.data_loading.loader_crud.get_resource_path")
    def test_save_characters_failure(self, mock_path: MagicMock) -> None:
        mock_path.side_effect = Exception("IO error")
        result = save_characters([{"名称": "测试"}])
        assert result is False

    @patch("games.endfield.data_loading.loader_crud.get_characters")
    @patch("games.endfield.data_loading.loader_crud.save_characters")
    def test_check_and_save_same_data(self, mock_save: MagicMock, mock_get: MagicMock) -> None:
        data = [{"名称": "A"}]
        mock_get.return_value = [{"名称": "A"}]
        check_and_save_characters(data)
        mock_save.assert_not_called()

    @patch("games.endfield.data_loading.loader_crud.get_characters")
    @patch("games.endfield.data_loading.loader_crud.save_characters")
    def test_check_and_save_different_data(self, mock_save: MagicMock, mock_get: MagicMock) -> None:
        data = [{"名称": "B"}]
        mock_get.return_value = [{"名称": "A"}]
        check_and_save_characters(data)
        mock_save.assert_called_once()

    @patch("games.endfield.data_loading.loader_crud.get_characters")
    @patch("games.endfield.data_loading.loader_crud.save_characters")
    def test_check_and_save_empty_input(self, mock_save: MagicMock, mock_get: MagicMock) -> None:
        check_and_save_characters([])
        mock_save.assert_not_called()
        mock_get.assert_not_called()

    @patch("games.endfield.data_loading.loader_crud.get_characters")
    @patch("games.endfield.data_loading.loader_crud.save_characters")
    def test_check_and_save_no_cache(self, mock_save: MagicMock, mock_get: MagicMock) -> None:
        mock_get.return_value = None
        check_and_save_characters([{"名称": "test"}])
        mock_save.assert_called_once()

    @patch("games.endfield.data_loading.loader_crud.get_weapons")
    @patch("games.endfield.data_loading.loader_crud.save_weapons")
    def test_check_and_save_weapons(self, mock_save: MagicMock, mock_get: MagicMock) -> None:
        mock_get.return_value = [{"名称": "A"}]
        check_and_save_weapons([{"名称": "A"}])
        mock_save.assert_not_called()

    @patch("games.endfield.data_loading.loader_crud.get_weapons")
    @patch("games.endfield.data_loading.loader_crud.save_weapons")
    def test_check_and_save_weapons_empty(self, mock_save: MagicMock, mock_get: MagicMock) -> None:
        check_and_save_weapons([])
        mock_save.assert_not_called()


# ── web_search_bridge.py ─────────────────────────────────────────────────


class TestEnrichSearchRequestFields:
    """enrich_search_request_fields。"""

    def test_basic_enrich(self) -> None:
        char_data = {"名称": "测试", "战技倍率": [[1.0]], "战技类型": "战技", "战技伤害类型": "物理"}
        req = SimpleNamespace(
            char_data=char_data,
            skill_1_level=8,
            skill_2_level=8,
            skill_3_level=8,
            weapon_skill_values=None,
        )
        updates = enrich_search_request_fields(req)
        assert "skill_name" in updates
        assert "skill_type" in updates
        assert "weapon_normal_levels" in updates
        # 已有技能等级 > 0，不会自动补 8
        assert "skill_1_level" not in updates

    def test_enrich_defaults_skill_levels(self) -> None:
        """所有技能等级为 0 时，自动补 8。"""
        char_data = {"名称": "测试", "战技倍率": [[1.0]], "战技类型": "战技", "战技伤害类型": "物理"}
        req = SimpleNamespace(
            char_data=char_data,
            skill_1_level=0,
            skill_2_level=0,
            skill_3_level=0,
            weapon_skill_values={},
        )
        updates = enrich_search_request_fields(req)
        assert updates["skill_1_level"] == 8
        assert updates["skill_2_level"] == 8
        assert updates["skill_3_level"] == 8

    def test_enrich_empty_weapon_skills(self) -> None:
        char_data = {"名称": "测试", "战技倍率": [[1.0]], "战技类型": "战技", "战技伤害类型": "物理"}
        req = SimpleNamespace(
            char_data=char_data,
            skill_1_level=8,
            skill_2_level=0,
            skill_3_level=0,
            weapon_skill_values=None,
        )
        updates = enrich_search_request_fields(req)
        assert "weapon_normal_levels" in updates
