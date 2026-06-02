# SPDX-License-Identifier: AGPL-3.0
"""布局编辑器 CLI — 从 DAG 编排 layout.json。

用法::

    python -m calc_framework.editor --dag path/to/dag.json
    python -m calc_framework.editor --dag path/to/dag.json --auto -o layout.json
    calc-layout --dag path/to/dag.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from calc_framework.dag.serializer import load_dag
from calc_framework.editor import LayoutEditor


def _interactive(editor: LayoutEditor) -> None:
    print(f"已加载 DAG: {editor.dag.name or '(未命名)'}")
    print(f"  可用输入变量 ({len(editor.available_input_vars)}):")
    for v in editor.available_input_vars:
        print(f"    - {v}")
    print(f"  可用输出 ({len(editor.available_outputs)}):")
    for o in editor.available_outputs:
        print(f"    - {o}")
    print()

    editor.set_name(input("布局名称: ").strip() or "计算布局")

    while True:
        print("\n--- 当前 section ---")
        if editor.state.sections:
            for s in editor.state.sections:
                if s.type == "inputs":
                    print(f"  [{s.id}] inputs: {s.variables}")
                else:
                    print(f"  [{s.id}] outputs: {s.outputs}")
        else:
            print("  (空)")

        print("\n操作: [a]添加section  [d]删除section  [s]设置变量  [o]设置输出")
        print("       [e]导出  [x]退出")
        cmd = input("> ").strip().lower()

        if cmd == "x":
            break
        elif cmd == "a":
            sec_id = input("  section id: ").strip()
            sec_type = input("  类型 (inputs/outputs) [outputs]: ").strip() or "outputs"
            if sec_type not in ("inputs", "outputs"):
                print("  类型必须为 inputs 或 outputs")
                continue
            title = input("  标题: ").strip() or sec_id
            editor.add_section(sec_id, type=sec_type, title=title)
            print(f"  已添加 section [{sec_id}]")
        elif cmd == "d":
            sec_id = input("  section id: ").strip()
            if editor.remove_section(sec_id):
                print(f"  已删除 [{sec_id}]")
            else:
                print(f"  未找到 [{sec_id}]")
        elif cmd == "s":
            sec_id = input("  section id: ").strip()
            print("  可用输入变量:")
            for v in editor.available_input_vars:
                print(f"    - {v}")
            raw = input("  变量名（逗号分隔）: ").strip()
            names = [n.strip() for n in raw.split(",") if n.strip()]
            try:
                editor.set_section_variables(sec_id, names)
                print(f"  已设置 {sec_id} variables = {names}")
            except KeyError as e:
                print(f"  错误: {e}")
        elif cmd == "o":
            sec_id = input("  section id: ").strip()
            print("  可用输出:")
            for o in editor.available_outputs:
                print(f"    - {o}")
            raw = input("  输出名（逗号分隔）: ").strip()
            names = [n.strip() for n in raw.split(",") if n.strip()]
            try:
                editor.set_section_outputs(sec_id, names)
                print(f"  已设置 {sec_id} outputs = {names}")
            except KeyError as e:
                print(f"  错误: {e}")
        elif cmd == "e":
            path = input("  导出路径 [layout.json]: ").strip() or "layout.json"
            editor.export(path)
            print(f"  已导出 → {path}")
        else:
            print(f"  未知命令: {cmd}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="calc-framework 布局编辑器 — 从 DAG 编排 layout.json",
    )
    parser.add_argument("--dag", required=True, help="DAG JSON 文件路径")
    parser.add_argument(
        "--auto", action="store_true",
        help="自动生成布局（所有 user_input → inputs, 所有 outputs → outputs）",
    )
    parser.add_argument("-o", "--output", default="layout.json", help="输出 layout.json 路径")
    parser.add_argument("--name", default="Computed Layout", help="布局名称")
    args = parser.parse_args(argv)

    dag_path = Path(args.dag)
    if not dag_path.exists():
        print(f"错误: DAG 文件不存在: {dag_path}", file=sys.stderr)
        return 1

    try:
        dag = load_dag(dag_path)
    except Exception as e:
        print(f"错误: 无法加载 DAG: {e}", file=sys.stderr)
        return 1

    try:
        editor = LayoutEditor(dag=dag)
    except Exception as e:
        print(f"错误: 无法初始化编辑器: {e}", file=sys.stderr)
        return 1

    if args.auto:
        editor.auto_layout(name=args.name)
        editor.export(args.output)
        print(f"已自动生成 → {args.output}")
        return 0

    _interactive(editor)

    if editor.state.sections:
        save = input("\n是否导出 layout.json? [y/N]: ").strip().lower()
        if save in ("y", "yes"):
            out = input(f"  导出路径 [{args.output}]: ").strip() or args.output
            editor.export(out)
            print(f"  已导出 → {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
