# SPDX-License-Identifier: AGPL-3.0
"""集成测试用 Admin Token 环境辅助。"""

from __future__ import annotations

import os

from api.internal.auth import ADMIN_TOKEN_ENV, ADMIN_TOKEN_HEADER

TEST_ADMIN_TOKEN = "test-admin-token-32chars-minimum!!"


def install_test_admin_token(token: str = TEST_ADMIN_TOKEN) -> None:
    """为测试注入 CALC_ADMIN_TOKEN。"""
    os.environ[ADMIN_TOKEN_ENV] = token


def remove_test_admin_token() -> None:
    """清理测试注入的 CALC_ADMIN_TOKEN。"""
    os.environ.pop(ADMIN_TOKEN_ENV, None)


def admin_headers(token: str = TEST_ADMIN_TOKEN) -> dict[str, str]:
    """返回带管理 Token 的请求头。"""
    return {ADMIN_TOKEN_HEADER: token}


__all__ = [
    "TEST_ADMIN_TOKEN",
    "admin_headers",
    "install_test_admin_token",
    "remove_test_admin_token",
]
