#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0


# SPDX-License-Identifier: AGPL-3.0
"""

列出 GUI / 开发可选依赖是否已安装（维护者与 CI 本地自检）。



用法（仓库根目录）：

    python tools/check_optional_deps.py

"""

from __future__ import annotations


import sys

from importlib.util import find_spec

from pathlib import Path


_PKG = Path(__file__).resolve().parent.parent / "games" / "endfield"

if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))


from utils.optional_deps import (
    DEV_OPTIONAL_DEPS,
    GUI_OPTIONAL_DEPS,
    RUNTIME_PIP_PACKAGES,
    is_matplotlib_available,
)


def _print_group(title: str, deps: tuple) -> int:
    """_print_group 实现。"""
    print(title)

    missing = 0

    for dep in deps:
        ok = dep.available()

        mark = "OK" if ok else "缺失"

        print(f"  [{mark}] {dep.feature}")

        if not ok:
            print(f"         → {dep.pip_hint}")

            missing += 1

    print()

    return missing


def _print_runtime() -> int:
    """打印运行时依赖的状态并返回缺失数。"""
    print("运行时（pyproject dependencies）")

    missing = 0

    for module, spec in RUNTIME_PIP_PACKAGES:
        ok = find_spec(module) is not None if module != "matplotlib" else is_matplotlib_available()

        mark = "OK" if ok else "缺失"

        print(f"  [{mark}] {spec}")

        if not ok:
            print("         → pip install -e .")

            missing += 1

    print()

    return missing


def main() -> int:
    """CLI 入口：检查所有可选依赖和运行时依赖的安装状态。

    Returns:
        退出码（0 全部已安装，1 有缺失）
    """
    print("终末地伤害计算器 — 依赖检查\n")

    n = 0

    n += _print_runtime()

    n += _print_group("GUI 可选", GUI_OPTIONAL_DEPS)

    n += _print_group("开发/打包", DEV_OPTIONAL_DEPS)

    if n:
        print(f"共 {n} 项未安装。")

        return 1

    print("全部已安装。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
