# SPDX-License-Identifier: AGPL-3.0
"""游戏选择器启动器 — 命令行选择适配包并启动 ComputeSheet。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from calc_framework.config.manager import AdapterManager, discover_adapters
from calc_framework.data.context import make_context
from calc_framework.logging import get_logger

logger = get_logger(__name__)

_ADAPTERS_DIR = Path(__file__).resolve().parents[2] / "adapters"


def _list_adapters() -> dict[str, Path]:
    return discover_adapters()


def _auto_detect_meta_path(path: Path) -> Path | None:
    """尝试自动找到适配包根目录（含 meta.json 的目录）。"""
    for candidate in (path, path.parent, path / "meta.json"):
        meta = candidate if candidate.name == "meta.json" else candidate / "meta.json"
        if meta.is_file():
            return meta.parent
    return None


def cli_selector() -> str | None:
    """命令行交互选择游戏适配器。

    Returns:
        选择的适配器名称，无选择时返回 None。
    """
    available = _list_adapters()
    if not available:
        print("错误：未发现任何适配包。请确认 framework/adapters/ 目录下有包含 meta.json 的适配包。")
        return None

    print("\n可用的游戏适配器：\n")
    names = sorted(available.keys())
    for i, name in enumerate(names, 1):
        meta_path = available[name] / "meta.json"
        desc = ""
        try:
            import json
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            desc = meta.get("description", "")
        except Exception:
            pass
        print(f"  [{i}] {name}" + (f" — {desc}" if desc else ""))

    print("\n  [q] 退出\n")

    while True:
        choice = input("请选择（输入编号或名称）：").strip()
        if choice.lower() in ("q", "quit", "exit"):
            return None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                return names[idx]
        elif choice in available:
            return choice
        print(f"无效选择，请重试（1-{len(names)} 或名称）。")


def run_launcher(adapter_name: str | None = None) -> None:
    """启动适配器的计算表 UI。

    若 adapter_name 为 None 则进入交互选择。
    """
    if adapter_name is None:
        adapter_name = cli_selector()
        if adapter_name is None:
            print("已退出。")
            return

    try:
        mgr = AdapterManager()
        pkg = mgr.load(adapter_name)
    except KeyError as exc:
        print(f"错误：{exc}")
        sys.exit(1)

    print(f"\n加载适配器: {adapter_name} v{pkg.meta.get('version', '?')}")
    print(f"描述: {pkg.meta.get('description', '无')}")
    print(f"DAG: {pkg.meta.get('dag_files', ['未知'])}")
    print()

    # 尝试启动 UI
    _launch_ui(adapter_name, pkg)


def _launch_ui(adapter_name: str, pkg: Any) -> None:
    """尝试启动 ComputeSheet GUI。"""
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QStatusBar, QVBoxLayout, QWidget

        from calc_framework.ui.compute_sheet import ComputeSheet
        from calc_framework.ui.controls import format_output
    except ImportError as exc:
        print(f"提示：UI 依赖未安装（{exc}），仅 DAG 引擎可工作。")
        _run_headless_demo(adapter_name, pkg)
        return

    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle(f"游戏计算器 — {adapter_name}")
    window.setMinimumSize(800, 600)

    help_menu = window.menuBar().addMenu("帮助")
    from utils.gui.donation import append_donation_help_menu_action

    append_donation_help_menu_action(help_menu, window)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    header = QLabel(f"<h2>{adapter_name}</h2>")
    layout.addWidget(header)

    # 从适配包的 layout.json 加载布局
    ui_layout_rel = pkg.meta.get("ui_layout", "")
    layout_path = pkg._adapter_dir / ui_layout_rel if ui_layout_rel else pkg._adapter_dir / "ui" / "layout.json"

    if layout_path.is_file():
        from calc_framework.ui.layout import load_layout_json
        ui_layout = load_layout_json(layout_path.read_text(encoding="utf-8"))
    else:
        from calc_framework.ui.layout import Layout
        ui_layout = Layout(schema_version="ui-v1", name="default", sections=[])

    variables = pkg.dag_service.dag.variables if hasattr(pkg.dag_service.dag, "variables") else {}
    sheet = ComputeSheet(pkg.dag_service, ui_layout, variables)
    layout.addWidget(sheet)

    status = QStatusBar()
    window.setStatusBar(status)

    # 实时显示结果
    def _on_evaluated(result):
        lines = format_output(result.outputs)
        status.showMessage("   ".join(lines), 5000)

    sheet.evaluated.connect(_on_evaluated)

    window.show()
    sys.exit(app.exec())


def _run_headless_demo(adapter_name: str, pkg: Any) -> None:
    """无 UI 时演示 DAG 求值。"""
    print(f"运行无 UI 演示：{adapter_name}")
    print("-" * 40)
    try:
        ctx = make_context()
        result = pkg.dag_service.evaluate(ctx)
        print("DAG 求值结果：")
        for name, val in result.outputs.items():
            print(f"  {name}: {val}")
    except Exception as exc:
        print(f"DAG 求值失败: {exc}")


if __name__ == "__main__":
    adapter = sys.argv[1] if len(sys.argv) > 1 else None
    run_launcher(adapter)
