#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""共享重导向逻辑：设计师 / 生成器 / 配置包设计器 → 开发者工具箱。

由 `scripts/main_designer.py` / `main_generator.py` / `main_pack_designer.py`
调用。通过 sys.argv[0] 自动识别工具名。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 脚本名(stem) → 显示名称
_TOOL_NAMES: dict[str, str] = {
    "main_designer": "数据设计器",
    "main_generator": "AI 计算器生成器",
    "main_pack_designer": "配置包设计器",
}


def redirect(tool_key: str = "") -> None:
    """打印提示消息并打开开发者工具箱。

    Args:
        tool_key: 工具键名（如 "main_designer"）。
                  为空时从 sys.argv[0] 自动推断。
    """
    if not tool_key:
        tool_key = Path(sys.argv[0]).stem
    tool_name = _TOOL_NAMES.get(tool_key, tool_key)

    print("=" * 60)
    print(f"  💡 提示：{tool_name}已整合到「开发者工具箱」")
    print()
    print("  推荐入口：")
    print("    python scripts/启动.bat 工具箱")
    print("    python scripts/main_dev_toolkit.py")
    print()
    print("  即将自动打开开发者工具箱…")
    print("=" * 60)
    print()

    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve().parent.parent / "main_dev_toolkit.py")],
        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0),
    )


if __name__ == "__main__":
    redirect()
