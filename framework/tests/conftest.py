# SPDX-License-Identifier: AGPL-3.0
"""pytest 配置：加入仓库根路径 + 控制台进度指示器。"""

from __future__ import annotations

import sys
from pathlib import Path

# 加入仓库根路径，使 tests/ocr/ 和 tests/utils/ 中的测试
# 能正确导入 tools/ 和 utils/ 模块
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def pytest_runtest_logreport(report):
    """每完成一个测试输出一个 '.'，防止长时间静默。"""
    if report.when == "call" and report.passed:
        sys.stdout.write(".")
        sys.stdout.flush()


def pytest_sessionfinish(session):
    sys.stdout.write("\n")
