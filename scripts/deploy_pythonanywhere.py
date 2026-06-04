#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""PythonAnywhere 部署工具 — 已移动到 scripts/tools/。

用法::
    python scripts/tools/deploy_pythonanywhere.py [options]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    target = str(Path(__file__).parent / "tools" / "deploy_pythonanywhere.py")
    print("NOTE: deploy_pythonanywhere.py 已移至 scripts/tools/，正在重导向…", file=sys.stderr)
    sys.exit(subprocess.call([sys.executable, target, *sys.argv[1:]]))
