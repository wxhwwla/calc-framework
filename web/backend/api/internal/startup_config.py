# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""启动配置自检 — 集中校验可选 SaaS / 管理接口相关环境变量。

设计口径（见审查清单 R-17）：

- ``CALC_API_KEY_PEPPER`` 是可选配置：未设置时 SaaS API Key 功能不可用，
  匿名计算不受影响，仅记录警告。
- 一旦显式设置但短于 32 字符，视为部署错误，启动即失败（``RuntimeError``），
  避免短 pepper 与文档宣称的安全强度不符。
- ``CALC_ADMIN_TOKEN`` 未设置时管理接口返回 503，同样只警告、不阻断启动。
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass

logger = logging.getLogger(__name__)

API_KEY_PEPPER_ENV = "CALC_API_KEY_PEPPER"  # pragma: allowlist secret（环境变量名，非密钥）
ADMIN_TOKEN_ENV = "CALC_ADMIN_TOKEN"  # pragma: allowlist secret（环境变量名，非密钥）
MIN_PEPPER_LENGTH = 32


@dataclass(frozen=True)
class StartupConfigReport:
    """启动配置检查结果。

    Attributes:
        errors: 阻断启动的配置错误。
        warnings: 不阻断启动、但需要部署者知晓的配置缺失。
        saas_enabled: 是否具备启用 SaaS API Key 功能的完整配置。
    """

    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    saas_enabled: bool = False


def check_startup_config(env: Mapping[str, str] | None = None) -> StartupConfigReport:
    """检查启动配置，返回错误与警告（不产生副作用）。

    Args:
        env: 待检查的环境变量映射；``None`` 时读取 ``os.environ``。

    Returns:
        汇总后的 :class:`StartupConfigReport`。
    """
    source = env if env is not None else _environ()
    pepper = (source.get(API_KEY_PEPPER_ENV) or "").strip()
    admin_token = (source.get(ADMIN_TOKEN_ENV) or "").strip()

    errors: list[str] = []
    warnings: list[str] = []

    if pepper:
        if len(pepper) < MIN_PEPPER_LENGTH:
            errors.append(f"{API_KEY_PEPPER_ENV} 至少需要 {MIN_PEPPER_LENGTH} 字符（当前 {len(pepper)} 字符）")
    else:
        warnings.append(
            f"{API_KEY_PEPPER_ENV} 未设置：SaaS API Key 功能不可用（匿名计算不受影响）；"
            f"如需启用请设置 ≥{MIN_PEPPER_LENGTH} 字符的随机串"
        )

    if not admin_token:
        warnings.append(f"{ADMIN_TOKEN_ENV} 未设置：/api/admin 管理接口将返回 503（匿名计算不受影响）")

    saas_enabled = bool(pepper) and len(pepper) >= MIN_PEPPER_LENGTH
    return StartupConfigReport(
        errors=tuple(errors),
        warnings=tuple(warnings),
        saas_enabled=saas_enabled,
    )


def run_startup_config_checks(
    env: Mapping[str, str] | None = None,
) -> StartupConfigReport:
    """记录配置检查结果；存在错误时抛出 ``RuntimeError`` 阻断启动。

    Args:
        env: 待检查的环境变量映射；``None`` 时读取 ``os.environ``。

    Returns:
        汇总后的 :class:`StartupConfigReport`。

    Raises:
        RuntimeError: 存在阻断启动的配置错误（如 pepper 过短）。
    """
    report = check_startup_config(env)
    for warning in report.warnings:
        logger.warning("启动配置：%s", warning)
    if report.errors:
        joined = "；".join(report.errors)
        logger.error("启动配置错误：%s", joined)
        raise RuntimeError(f"启动配置错误：{joined}")
    if report.saas_enabled:
        logger.info("SaaS API Key 功能已启用（%s 长度校验通过）", API_KEY_PEPPER_ENV)
    return report


def _environ() -> Mapping[str, str]:
    """延迟导入 ``os``，避免模块导入期读取环境变量造成不可测试的副作用。"""
    import os

    return os.environ


__all__ = [
    "ADMIN_TOKEN_ENV",
    "API_KEY_PEPPER_ENV",
    "MIN_PEPPER_LENGTH",
    "StartupConfigReport",
    "check_startup_config",
    "run_startup_config_checks",
]
