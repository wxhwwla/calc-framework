#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""运行 ScanCode Toolkit 许可证/版权扫描，只扫描项目源代码。

用法（仓库根目录）::

    python tools/run_scancode.py

只扫与终末地相关的源代码目录，排除其他游戏数据和第三方依赖。

输出文件: ``scan_report.json``（在仓库根目录）。

依赖::

    pip install scancode-toolkit
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent

    cmd = [
        "scancode",
        "--license", "--copyright", "--info",
        "--json-pp", str(repo_root / "scan_report.json"),
        # 只扫与终末地直接相关的源代码目录
        "framework",
        "games/endfield",
        "tools/endfield_designer",
        "tools/endfield_scripts",
        "tools/ocr",
        "tools/data_pipeline",
        "tools/designer",
        "tools/audit",
        "tools/tests",
        "scripts",
        "utils",
        "docs",
        # 用 --ignore 确保 .venv 不会被扫进来
        "--ignore", ".venv",
    ]

    print("运行: scancode --license --copyright --info --json-pp scan_report.json \\")
    for arg in cmd[5:]:  # skip scancode and fixed flags
        print(f"  {arg}")
    print()
    print(f"输出: {repo_root / 'scan_report.json'}")
    print()

    result = subprocess.run(cmd, cwd=repo_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
