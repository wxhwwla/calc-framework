# SPDX-License-Identifier: AGPL-3.0
"""配置包设计器 data_editor profiles 单元测试。"""

from tools.designer.data_editor.profiles import (
    ADAPTER_NAME_TO_PROFILE,
    ARKNIGHTS_OPERATORS_JSON,
    PROFILES,
    data_dir_for_profile,
)


def test_endfield_profile_data_dir():
    prof = PROFILES["endfield"]
    d = data_dir_for_profile(prof)
    assert d == prof.adapter_dir / "data"
    assert (d / "characters_standard.json").is_file()


def test_arknights_profile_points_to_parsed_operators():
    prof = PROFILES["arknights"]
    d = data_dir_for_profile(prof)
    assert d == ARKNIGHTS_OPERATORS_JSON.parent
    assert ARKNIGHTS_OPERATORS_JSON.is_file()


def test_adapter_name_mapping():
    assert ADAPTER_NAME_TO_PROFILE["终末地伤害计算"] == "endfield"
    assert ADAPTER_NAME_TO_PROFILE["明日方舟伤害计算"] == "arknights"
