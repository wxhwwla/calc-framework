#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""CalcPack 导入工具 — 已移动到 scripts/tools/。

用法::
    python scripts/tools/import_calcpack.py [options]
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    target = str(Path(__file__).parent / "tools" / "import_calcpack.py")
    print("NOTE: import_calcpack.py 已移至 scripts/tools/，正在重导向…", file=sys.stderr)
    sys.exit(subprocess.call([sys.executable, target, *sys.argv[1:]]))
