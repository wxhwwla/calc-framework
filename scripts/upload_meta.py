#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
上传脚本用的版本号与临时提交说明。

💡 版本常量与核心逻辑已迁移到 `_version.py`。
此文件为向后兼容的导入包装器。
"""

from __future__ import annotations

from scripts._version import (  # noqa: F401
    _EXE_VERSION,
    _EXE_VERSION_PATTERN,
    _VERSION,
    _VERSION_PATTERN,
    SUMMARY_BEGIN,
    SUMMARY_END,
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
    read_summary_for_commit,
    read_version,
    remove_summary_block,
    strip_summary_block,
    summarize_changes,
    write_summary_block,
    write_version,
)

__all__ = [
    "SUMMARY_BEGIN",
    "SUMMARY_END",
    "_EXE_VERSION_PATTERN",
    "_VERSION_PATTERN",
    "build_commit_message",
    "bump_minor",
    "bump_patch",
    "classify_changed_paths",
    "format_semver",
    "parse_semver",
    "please_read_me_path",
    "read_exe_version",
    "read_summary_for_commit",
    "read_version",
    "remove_summary_block",
    "strip_summary_block",
    "summarize_changes",
    "write_summary_block",
    "write_version",
]
