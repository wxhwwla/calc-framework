# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""启动被测 exe 的子进程封装。"""

from __future__ import annotations

import subprocess
from pathlib import Path

__all__ = ["start_exe_process"]


def start_exe_process(
    exe_path: Path,
    args: tuple[str, ...] = (),
) -> subprocess.Popen[bytes]:
    """启动 exe，并把 stdout/stderr 重定向到 DEVNULL。

    windowed 版 exe 冻结后仍会向继承的 stdout 写 INFO 日志。若父进程用
    不读取的 ``subprocess.PIPE`` 承接，管道写满后 logging 锁会让 UI 线程
    阻塞，窗口变成「未响应」。测试不需要这些输出（应用日志已落盘到
    ``logs/``），因此统一丢弃。

    Args:
        exe_path: 可执行文件路径。
        args: 额外命令行参数。

    Returns:
        已启动的子进程。
    """
    return subprocess.Popen(
        [str(exe_path), *args],
        cwd=str(exe_path.parent),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
