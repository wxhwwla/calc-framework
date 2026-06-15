#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""Windows 平台 WMI 补丁测试。"""

from __future__ import annotations

import sys
import unittest
from unittest.mock import MagicMock, patch

_WIN_ONLY = unittest.skipUnless(sys.platform.startswith("win"), "winreg 仅 Windows 可用")


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

    @_WIN_ONLY
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

    @_WIN_ONLY
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
            release, _version, _machine = pwp._read_windows_version_from_registry()

            self.assertEqual(release, "11")

    @_WIN_ONLY
    def test_read_windows_version_major_version_oserror(self) -> None:
        """CurrentMajorVersionNumber OSError 时根据 build 降级。"""

        import utils.platform_win32_patch as pwp

        mock_key = MagicMock()

        mock_key.__enter__.return_value = mock_key

        calls: dict = {}

        def query_side_effect(key, name):
            calls[name] = True

            if name == "CurrentBuildNumber":
                return (19045, None)

            raise OSError

        with (
            patch("winreg.OpenKeyEx", return_value=mock_key),
            patch("winreg.QueryValueEx", side_effect=query_side_effect),
            patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "AMD64"}, clear=True),
        ):
            release, version, _machine = pwp._read_windows_version_from_registry()

            self.assertEqual(release, "10")

            self.assertIn("10.0.", version)

            self.assertTrue(calls.get("CurrentMajorVersionNumber"))

    def test_machine_from_architew6432(self) -> None:
        from utils.platform_win32_patch import _windows_machine_from_env

        with patch.dict("os.environ", {"PROCESSOR_ARCHITEW6432": "AMD64"}, clear=True):
            self.assertEqual(_windows_machine_from_env(), "AMD64")

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

    def test_apply_twice_early_return(self) -> None:
        """第二次调用应提前返回（_edc_no_wmi_patch 已标记）。"""

        import platform

        import utils.platform_win32_patch as pwp

        with (
            patch.object(pwp, "sys") as mock_sys,
            patch("platform.win32_ver", return_value=("10", "10.0.0", "", "Multiprocessor Free")),
        ):
            mock_sys.platform = "win32"

            pwp.apply_platform_win32_patch()

            platform.win32_ver._edc_no_wmi_patch = True  # type: ignore[attr-defined]

            pwp.apply_platform_win32_patch()

    @_WIN_ONLY
    def test_apply_and_call_patched_functions(self) -> None:
        """apply 后调用 patched 函数应触发闭包。"""

        import platform

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
            patch.object(pwp, "sys") as mock_sys,
            patch("winreg.OpenKeyEx", return_value=mock_key),
            patch("winreg.QueryValueEx", side_effect=query_side_effect),
            patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "AMD64"}, clear=True),
        ):
            mock_sys.platform = "win32"

            pwp.apply_platform_win32_patch()

            ver = platform.win32_ver()

            self.assertEqual(ver[0], "11")

            sys_str = platform.system()

            self.assertEqual(sys_str, "Windows")

            machine = platform.machine()

            self.assertEqual(machine, "AMD64")

    @_WIN_ONLY
    def test_apply_and_call_patched_uname(self) -> None:
        """apply 后调用 platform.uname() 触发闭包。"""

        import platform

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
            patch.object(pwp, "sys") as mock_sys,
            patch("winreg.OpenKeyEx", return_value=mock_key),
            patch("winreg.QueryValueEx", side_effect=query_side_effect),
            patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "AMD64"}, clear=True),
            patch.dict("os.environ", {"COMPUTERNAME": "MYPC"}, clear=False),
        ):
            mock_sys.platform = "win32"

            pwp.apply_platform_win32_patch()

            uname_result = platform.uname()

            self.assertEqual(uname_result.system, "Windows")

            self.assertIn(uname_result.release, ("10", "11"))

            self.assertEqual(uname_result.machine, "AMD64")

    @_WIN_ONLY
    def test_apply_and_call_release_and_version(self) -> None:
        """apply 后调用 release/version 闭包。"""

        import platform

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
            patch.object(pwp, "sys") as mock_sys,
            patch("winreg.OpenKeyEx", return_value=mock_key),
            patch("winreg.QueryValueEx", side_effect=query_side_effect),
            patch.dict("os.environ", {"PROCESSOR_ARCHITECTURE": "AMD64"}, clear=True),
        ):
            mock_sys.platform = "win32"

            pwp.apply_platform_win32_patch()

            release = platform.release()

            self.assertEqual(release, "11")

            version = platform.version()

            self.assertIn("10.0.", version)

    @_WIN_ONLY
    def test_win32_ver_oserror_fallback(self) -> None:
        """win32_ver 在 registry 异常时回退原函数。"""

        import platform

        import utils.platform_win32_patch as pwp

        with (
            patch.object(pwp, "sys") as mock_sys,
            patch("winreg.OpenKeyEx", side_effect=OSError),
            patch("platform.win32_ver", return_value=("10", "10.0.0", "", "MP")) as mock_orig,
        ):
            mock_sys.platform = "win32"

            pwp.apply_platform_win32_patch()

            ver = platform.win32_ver()

            mock_orig.assert_called()

            self.assertEqual(ver[0], "10")

    @_WIN_ONLY
    def test_uname_oserror_fallback(self) -> None:
        """uname 在 registry 异常时回退默认值。"""

        import platform

        import utils.platform_win32_patch as pwp

        with (
            patch.object(pwp, "sys") as mock_sys,
            patch("winreg.OpenKeyEx", side_effect=OSError),
            patch.dict("os.environ", {}, clear=True),
        ):
            mock_sys.platform = "win32"

            pwp.apply_platform_win32_patch()

            uname_result = platform.uname()

            self.assertEqual(uname_result.release, "10")

            self.assertEqual(uname_result.version, "10.0.0")
