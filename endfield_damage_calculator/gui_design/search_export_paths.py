#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全量/MVP 搜索导出目录（落在包目录下，不使用系统临时盘）。"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from utils.path_utils import get_application_dir

SEARCH_OUTPUT_DIR_NAME = "search_output"


def application_data_dir() -> Path:
    """应用根目录（开发=包目录；打包=exe 同级发布文件夹）。"""
    return get_application_dir()


def default_search_output_root(*, base_dir: Path | None = None) -> Path:
    """默认搜索输出根目录：<应用根>/search_output。"""
    root = base_dir if base_dir is not None else application_data_dir()
    return root / SEARCH_OUTPUT_DIR_NAME


def allocate_search_run_directory(
    *,
    purpose: str,
    base_dir: Path | None = None,
) -> Path:
    """在 search_output 下创建本次运行的子目录。"""
    output_root = default_search_output_root(base_dir=base_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_purpose = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in purpose)
    run_dir = output_root / f"{safe_purpose}_{stamp}_{time.time_ns()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir
