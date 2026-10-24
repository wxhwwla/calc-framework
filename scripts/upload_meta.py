#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""上传脚本用的版本号与提交说明辅助。

版本常量与核心逻辑在 `_version.py`。此文件为向后兼容导入包装器。
"""

from __future__ import annotations

from scripts._version import (
    _EXE_VERSION,
    _EXE_VERSION_PATTERN,
    _VERSION,
    _VERSION_PATTERN,
    build_commit_message,
    bump_minor,
    bump_patch,
    classify_changed_paths,
    format_semver,
    get_exe_version,
    get_version,
    parse_semver,
    please_read_me_path,
    read_exe_version,
    read_version,
    summarize_changes,
    write_version,
)

__all__ = [
    "_EXE_VERSION",
    "_EXE_VERSION_PATTERN",
    "_VERSION",
    "_VERSION_PATTERN",
    "build_commit_message",
    "bump_minor",
    "bump_patch",
    "classify_changed_paths",
    "format_semver",
    "get_exe_version",
    "get_version",
    "parse_semver",
    "please_read_me_path",
    "read_exe_version",
    "read_version",
    "summarize_changes",
    "write_version",
]
