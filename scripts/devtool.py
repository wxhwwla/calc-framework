#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""开发者 CLI 工具箱 — 已移动到 scripts/tools/。

用法::
    python scripts/tools/devtool.py <command> [options]
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    target = str(Path(__file__).parent / "tools" / "devtool.py")
    print(f"NOTE: devtool.py 已移至 scripts/tools/，正在重导向…", file=sys.stderr)
    sys.exit(subprocess.call([sys.executable, target] + sys.argv[1:]))
