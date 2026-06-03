#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""GitHub 上传模块 — 已移动到 scripts/tools/。

重导向包装器，保持向后兼容。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts._path_setup import ensure_root  # noqa: E402

ensure_root()

from scripts.tools.github_upload_module import *  # noqa: F401, F403, E402
from scripts.tools.github_upload_module import main  # noqa: E402

if __name__ == "__main__":
    main()
