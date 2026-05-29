#!/usr/bin/env python3
"""应用路径：读资源、写搜索导出。"""

from __future__ import annotations

import secrets
import time
from datetime import datetime
from pathlib import Path

from utils.path_utils import get_application_dir

SEARCH_OUTPUT_DIR_NAME = "search_output"


def default_search_output_root(*, base_dir: Path | None = None) -> Path:
    root = base_dir if base_dir is not None else get_application_dir()
    return root / SEARCH_OUTPUT_DIR_NAME


def allocate_search_run_directory(
    *,
    purpose: str,
    base_dir: Path | None = None,
) -> Path:
    output_root = default_search_output_root(base_dir=base_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_purpose = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in purpose)
    run_dir = output_root / f"{safe_purpose}_{stamp}_{time.time_ns()}_{secrets.token_hex(4)}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
