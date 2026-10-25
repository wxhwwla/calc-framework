# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import patch

from games.endfield.gui.controls.search.search_settings import (
    build_worker_option_labels,
    get_cpu_parallel_info,
)
from utils.platform_win32_patch import apply_platform_win32_patch


class TestSearchSettingsUnusualCpu:
    def test_build_labels_with_unusual_max_workers(self) -> None:
        info = get_cpu_parallel_info(cpu_count=7)

        labels = build_worker_option_labels(cpu_count=7)

        assert str(info.max_workers) in labels


class TestPlatformWin32PatchClosure:
    def test_apply_on_non_win32_returns_early(self) -> None:
        import utils.platform_win32_patch as pwp

        with patch.object(pwp, "sys") as mock_sys:
            mock_sys.platform = "linux"

            apply_platform_win32_patch()

    def test_apply_twice_returns_early(self) -> None:
        apply_platform_win32_patch()

        apply_platform_win32_patch()
