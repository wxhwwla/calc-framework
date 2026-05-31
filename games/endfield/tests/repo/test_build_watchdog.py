#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""build.py 看门狗：心跳与超时终止。"""

from __future__ import annotationsimport unittestfrom pathlib import Pathfrom unittest.mock import MagicMock, patchfrom main_build import _read_int_env, _run_with_watchdogclass TestBuildWatchdog(unittest.TestCase):
    def test_read_int_env_default(self) -> None:
        self.assertEqual(_read_int_env("ENDFIELD_TEST_UNSET_VAR", 42), 42)

    def test_run_with_watchdog_success(self) -> None:
        proc = MagicMock()
        proc.poll.side_effect = [None, 0]
        with patch("main_build.subprocess.Popen", return_value=proc), patch("main_build.time.sleep"):
            _run_with_watchdog(
                ["dummy"],
                cwd=Path("."),
                timeout_seconds=30,
                heartbeat_seconds=15,
            )

    def test_run_with_watchdog_timeout(self) -> None:
        proc = MagicMock()
        proc.poll.return_value = None
        proc.pid = 1234
        clock = iter([0.0, 0.0, 31.0, 31.0])

        def _mono() -> float:
            return next(clock)

        with (
            patch("main_build.subprocess.Popen", return_value=proc),
            patch("main_build.time.monotonic", side_effect=_mono),
            patch("main_build.time.sleep"),
            patch("main_build._terminate_process_tree") as kill,
        ):
            with self.assertRaises(TimeoutError):
                _run_with_watchdog(
                    ["dummy"],
                    cwd=Path("."),
                    timeout_seconds=30,
                    heartbeat_seconds=15,
                )
            kill.assert_called_once_with(proc)


if __name__ == "__main__":
    unittest.main()
