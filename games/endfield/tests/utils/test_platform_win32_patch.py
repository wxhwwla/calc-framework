#!/usr/bin/env python3
"""Windows 平台 WMI 补丁测试。"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch


class TestPlatformWin32Patch(unittest.TestCase):
    def test_patch_imports_cleanly(self) -> None:
        if "utils.platform_win32_patch" in sys.modules:
            del sys.modules["utils.platform_win32_patch"]
        import utils.platform_win32_patch  # noqa: F811

        self.assertIsNotNone(utils.platform_win32_patch)

    def test_apply_patches_skipped_on_non_windows(self) -> None:
        import utils.platform_win32_patch as pwp

        with patch.object(pwp, "sys") as mock_sys:
            mock_sys.platform = "linux"
            pwp.apply_platform_win32_patch()

    def test_windows_machine_from_env(self) -> None:
        from utils.platform_win32_patch import _windows_machine_from_env

        with patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "ARM64"}, clear=True):
            self.assertEqual(_windows_machine_from_env(), "ARM64")

    def test_windows_machine_fallback(self) -> None:
        from utils.platform_win32_patch import _windows_machine_from_env

        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(_windows_machine_from_env(), "AMD64")

    def test_read_windows_version_from_registry(self) -> None:
        import utils.platform_win32_patch as pwp

        mock_key = MagicMock()
        mock_key.__enter__.return_value = mock_key

        def query_side_effect(key, name):
            values = {
                "CurrentBuildNumber": (19045, None),
                "CurrentMajorVersionNumber": (10, None),
                "CurrentMinorVersionNumber": (0, None),
            }
            if name in values:
                return values[name]
            raise OSError

        with (
            patch("winreg.OpenKeyEx", return_value=mock_key),
            patch("winreg.QueryValueEx", side_effect=query_side_effect),
            patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "AMD64"}, clear=True),
        ):
            release, version, machine = pwp._read_windows_version_from_registry()
            self.assertEqual(release, "10")
            self.assertIn("10.0.", version)
            self.assertEqual(machine, "AMD64")

    def test_read_windows_version_registry_build_gte_22000(self) -> None:
        import utils.platform_win32_patch as pwp

        mock_key = MagicMock()
        mock_key.__enter__.return_value = mock_key

        def query_side_effect(key, name):
            values = {
                "CurrentBuildNumber": (22631, None),
                "CurrentMajorVersionNumber": (10, None),
                "CurrentMinorVersionNumber": (0, None),
            }
            if name in values:
                return values[name]
            raise OSError

        with (
            patch("winreg.OpenKeyEx", return_value=mock_key),
            patch("winreg.QueryValueEx", side_effect=query_side_effect),
            patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "AMD64"}, clear=True),
        ):
            release, version, machine = pwp._read_windows_version_from_registry()
            self.assertEqual(release, "11")

    def test_apply_patches_marks_functions(self) -> None:
        import utils.platform_win32_patch as pwp

        with (
            patch.object(pwp, "sys") as mock_sys,
            patch("platform.win32_ver", return_value=("10", "10.0.0", "", "Multiprocessor Free")),
            patch("platform.release", return_value="10"),
            patch("platform.version", return_value="10.0.0"),
            patch("platform.system", return_value="Windows"),
            patch("platform.machine", return_value="AMD64"),
        ):
            mock_sys.platform = "win32"
            pwp.apply_platform_win32_patch()
            import platform
            self.assertTrue(getattr(platform.win32_ver, "_edc_no_wmi_patch", False))


if __name__ == "__main__":
    unittest.main()
