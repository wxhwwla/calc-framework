#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""GitHub 上传 — 重导向到 scripts/github_upload_module.py。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent
    target = repo_root / "scripts" / "tools" / "github_upload_module.py"
    sys.exit(
        subprocess.call(
            [sys.executable, str(target), *sys.argv[1:]],
            cwd=str(repo_root),
        )
    )
