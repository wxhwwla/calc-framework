# SPDX-License-Identifier: AGPL-3.0
"""pytest 配置：控制台进度指示器，防止测试静默看起来像卡死。"""

from __future__ import annotations

import sys


def pytest_runtest_logreport(report):
    """每完成一个测试输出一个 '.'，防止长时间静默。"""
    if report.when == "call" and report.passed:
        sys.stdout.write(".")
        sys.stdout.flush()


def pytest_sessionfinish(session):
    sys.stdout.write("\n")
