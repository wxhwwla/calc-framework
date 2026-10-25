# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
语义化版本工具（纯函数，游戏无关）。

可用于任何需要 semver 管理的项目脚本。
"""

from __future__ import annotations


def parse_semver(version: str) -> tuple[int, int, int]:
    """解析语义化版本字符串为 (major, minor, patch) 三元组。

    Args:
        version: 语义化版本字符串，如 "3.23.5"

    Returns:
        (major, minor, patch) 整数三元组

    Raises:
        ValueError: 格式不符合 MAJOR.MINOR.PATCH 时
    """
    parts = version.strip().split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"无效语义化版本: {version!r}（需要 MAJOR.MINOR.PATCH）")
    return int(parts[0]), int(parts[1]), int(parts[2])


def format_semver(major: int, minor: int, patch: int) -> str:
    """将整数三元组格式化为 "MAJOR.MINOR.PATCH" 字符串。"""
    return f"{major}.{minor}.{patch}"


def bump_patch(version: str) -> str:
    """版本号第三位 +1（如 3.23.5 → 3.23.6）。"""
    major, minor, patch = parse_semver(version)
    return format_semver(major, minor, patch + 1)


def bump_minor(version: str) -> str:
    """版本号第二位 +1，第三位置零（如 3.23.5 → 3.24.0）。"""
    major, minor, _patch = parse_semver(version)
    return format_semver(major, minor + 1, 0)
