# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""打包 exe 自动测试启动子进程的方式回归测试。

覆盖 P2-02 实机复验发现的问题：``packaged_test`` 曾用 ``subprocess.PIPE``
承接 exe 的 stdout/stderr 却从不读取。windowed 版 exe 在冻结模式下仍会把
INFO 日志写到 stdout，管道写满后 UI 线程阻塞在写入上，窗口变成「未响应」，
确认计算与后续控件查询全部超时。
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.auto_test.utils import launch


def test_start_exe_process_discards_output() -> None:
    exe_path = Path("C:/fake/Game Calc Platform.exe")
    fake_proc = Mock(pid=4321)

    with patch.object(launch.subprocess, "Popen", return_value=fake_proc) as popen:
        assert launch.start_exe_process(exe_path, ("--game", "endfield")) is fake_proc

    args, kwargs = popen.call_args
    assert args[0] == [str(exe_path), "--game", "endfield"]
    assert kwargs["cwd"] == str(exe_path.parent)
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL
