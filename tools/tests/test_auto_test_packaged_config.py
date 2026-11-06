# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""打包 exe 自动测试配置与发布布局的一致性回归测试。

覆盖审查项 P2-02 的前置条件：自动测试必须针对当前唯一的 launcher 产物，
否则 `--target calculator` 会直接构建失败，测试结果不可信。
"""

from __future__ import annotations

from release_bundle.release_layout import TARGET_APP_NAMES
from scripts.auto_test import config


def test_packaged_build_target_matches_current_release_layout() -> None:
    assert config.PACKAGED_BUILD_TARGET == "launcher"


def test_packaged_app_dir_and_exe_names_match_release_layout() -> None:
    expected_app_dir = TARGET_APP_NAMES["launcher"]
    expected_exe_name = f"{expected_app_dir}.exe"

    assert expected_app_dir == config.PACKAGED_APP_DIR_NAME
    assert expected_exe_name == config.PACKAGED_EXE_NAME


def test_packaged_exe_launches_through_launcher() -> None:
    assert config.PACKAGED_EXE_ARGS == ()
    assert config.PACKAGED_LAUNCHER_TITLE == "游戏计算器启动器"


def test_packaged_startup_timeout_covers_onefile_extraction() -> None:
    assert config.PACKAGED_STARTUP_TIMEOUT >= 120
    assert config.APP_STARTUP_TIMEOUT < config.PACKAGED_STARTUP_TIMEOUT


def test_packaged_scenarios_require_real_flow_steps() -> None:
    steps = [step for scenario in config.TEST_SCENARIOS["packaged"] for step in scenario["steps"]]

    assert "等待启动器" in steps
    assert "等待主窗口" in steps
    assert "确认计算" in steps
