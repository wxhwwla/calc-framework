#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向后兼容：请改用 utils.app_paths。"""

from utils.app_paths import (
    SEARCH_OUTPUT_DIR_NAME,
    allocate_search_run_directory,
    default_search_output_root,
)

__all__ = (
    "SEARCH_OUTPUT_DIR_NAME",
    "allocate_search_run_directory",
    "default_search_output_root",
)
