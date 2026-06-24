#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

运行时与可选依赖：探测、启动提示（开发模式）、打包前检查。



matplotlib 已写入 ``pyproject.toml`` 运行时依赖；应在 ``pip install -e .`` 时装好。

开发模式启动时仅提示缺失项，不在 GUI 启动路径内同步 pip install（避免 pip 无输出/锁等待假死）。

"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib.util import find_spec

from calc_framework.logging import get_logger

_logger = get_logger(__name__)


# (import 名, pip 规格) — 与 [project].dependencies 一致

RUNTIME_PIP_PACKAGES: tuple[tuple[str, str], ...] = (("matplotlib", "matplotlib>=3.8"),)


@dataclass(frozen=True)
class OptionalDependency:
    """一项可选能力及其安装方式。"""

    feature: str

    module: str

    pip_hint: str

    probe: Callable[[], bool] | None = None

    def available(self) -> bool:
        if self.probe is not None:
            return self.probe()

        return find_spec(self.module) is not None


def _probe_matplotlib() -> bool:
    try:
        import matplotlib  # noqa: F401

        return True

    except ImportError:
        return False


# 仍可选（未写入运行时 dependencies）

GUI_OPTIONAL_DEPS: tuple[OptionalDependency, ...] = (
    OptionalDependency(
        feature="plugins/*.yaml 敌人配置",
        module="yaml",
        pip_hint='pip install pyyaml  或  pip install -e ".[plugins]"',
    ),
)


DEV_OPTIONAL_DEPS: tuple[OptionalDependency, ...] = (
    OptionalDependency(
        feature="pytest 测试",
        module="pytest",
        pip_hint='pip install -e ".[dev]"',
    ),
    OptionalDependency(
        feature="PyInstaller 打包",
        module="PyInstaller",
        pip_hint='pip install -e ".[build]"',
    ),
)


def is_matplotlib_available() -> bool:
    return _probe_matplotlib()


def matplotlib_install_hint() -> str:
    return "pip install -e .  或  pip install matplotlib>=3.8"


def missing_runtime_packages() -> list[tuple[str, str]]:
    """返回缺失的运行时 (import 名, pip 规格) 列表。"""

    missing: list[tuple[str, str]] = []

    for module, spec in RUNTIME_PIP_PACKAGES:
        if module == "matplotlib":
            if not is_matplotlib_available():
                missing.append((module, spec))

            continue

        if find_spec(module) is None:
            missing.append((module, spec))

    return missing


def format_missing_runtime_dependencies() -> str:
    """供 main.py 在开发模式启动时提示缺失的运行时依赖。"""

    missing = missing_runtime_packages()

    if not missing:
        return ""

    specs = "、".join(spec for _, spec in missing)

    lines = [
        f"警告: 缺少运行时依赖: {specs}",
        "请在本 venv 的 [包] 目录执行:",
        "  pip install -e .",
        "（仪表盘需要 matplotlib；其余 GUI 功能可正常使用）",
    ]

    return "\n".join(lines)


def ensure_runtime_dependencies() -> None:
    """开发模式：提示缺失运行时依赖，不阻塞 GUI（打包 exe 不执行）。"""

    if getattr(sys, "frozen", False):
        return

    message = format_missing_runtime_dependencies()

    if message:
        _logger.warning("%s", message)


def missing_dependencies(deps: Sequence[OptionalDependency]) -> list[OptionalDependency]:
    return [dep for dep in deps if not dep.available()]


def format_missing_lines(
    deps: Sequence[OptionalDependency],
    *,
    prefix: str = "  - ",
) -> str:
    missing = missing_dependencies(deps)

    if not missing:
        return ""

    lines = [f"{prefix}{dep.feature}: {dep.pip_hint}" for dep in missing]

    return "\n".join(lines)


def format_missing_gui_extras() -> str:
    """供 main.py 提示仍缺失的可选功能（如 PyYAML 插件）。"""

    body = format_missing_lines(GUI_OPTIONAL_DEPS)

    if not body:
        return ""

    return "可选功能未安装：\n" + body
