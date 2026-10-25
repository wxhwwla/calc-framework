# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""DAG 分步调试器 CLI — 交互式命令行界面。



用法::



    python -m calc_framework.dag.debugger_cli path/to/dag.json



进入交互模式后，输入 ``h`` 查看帮助：



    n       执行下一步

    r       执行到结束

    t <id>  执行到指定节点

    b <id>  设置断点

    d <id>  移除断点

    l       列出所有断点

    c       清除所有断点

    p       查看下一个节点

    v       查看当前所有节点值

    o       查看输出值

    s       显示进度

    i <id>  查看节点信息

    q       退出

"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path
from typing import NoReturn

from calc_framework.dag.sandbox import register_function
from calc_framework.logging import get_logger

logger = get_logger(__name__)


# ── Color helpers ─────────────────────────────────────


def _color(s: str, code: int) -> str:
    if not sys.stdout.isatty():
        return s

    return f"\033[{code}m{s}\033[0m"


def green(s: str) -> str:
    return _color(s, 32)


def cyan(s: str) -> str:
    return _color(s, 36)


def yellow(s: str) -> str:
    return _color(s, 33)


def red(s: str) -> str:
    return _color(s, 31)


def bold(s: str) -> str:
    return _color(s, 1)


def _load_functions(meta_path: Path) -> None:
    """从适配包的 ``meta.json`` 加载自定义函数。"""

    import json

    if not meta_path.is_file():
        return

    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    funcs = meta.get("functions", {})

    if not funcs:
        return

    base = meta_path.parent

    for fname, fpath in funcs.items():
        full_path = base / fpath

        if not full_path.is_file():
            continue

        try:
            _exec_and_register(full_path, fname)

        except Exception as exc:
            print(yellow(f"  加载函数 {fname} 失败: {exc}"))


def _exec_and_register(fpath: Path, fname: str) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(fpath.stem, fpath)

    if spec is None or spec.loader is None:
        return

    mod = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(mod)

    fn = getattr(mod, fname, None)

    if fn is not None:
        register_function(fname, fn)


class DebuggerCLI:
    """交互式 DAG 分步调试器 CLI。"""

    def __init__(self) -> None:
        self._debugger = None

        self._dag_path = None

    def run(self, dag_path: str, context: dict | None = None) -> None:
        """启动 CLI 调试会话。"""

        from calc_framework.dag.debugger import StepDebugger
        from calc_framework.dag.serializer import load_dag

        dag_file = Path(dag_path)

        if not dag_file.is_file():
            print(red(f"文件不存在: {dag_path}"))

            sys.exit(1)

        self._dag_path = dag_file

        graph = load_dag(dag_file)

        ctx = context or {}

        # 尝试加载适配包的自定义函数

        meta_path = dag_file.parent / "meta.json"

        if meta_path.is_file():
            _load_functions(meta_path)

        self._debugger = StepDebugger(graph, ctx)

        self._interactive()

    def _interactive(self) -> NoReturn:
        print(bold("DAG 分步调试器 — 输入 h 查看帮助\n"))

        while True:
            try:
                line = input(cyan("dag> ")).strip()

            except (EOFError, KeyboardInterrupt):
                print()

                sys.exit(0)

            if not line:
                continue

            cmd, *args = shlex.split(line)

            self._dispatch(cmd, args)

    def _dispatch(self, cmd: str, args: list[str]) -> None:
        dispatch = {
            "n": self._cmd_next,
            "r": self._cmd_run,
            "t": self._cmd_run_to,
            "b": self._cmd_break,
            "d": self._cmd_delete_breakpoint,
            "l": self._cmd_list_breakpoints,
            "c": self._cmd_clear_breakpoints,
            "p": self._cmd_peek,
            "v": self._cmd_values,
            "o": self._cmd_outputs,
            "s": self._cmd_status,
            "i": self._cmd_info,
            "h": self._cmd_help,
            "q": self._cmd_quit,
        }

        handler = dispatch.get(cmd)

        if handler is None:
            print(red(f"未知命令: {cmd}  (输入 h 查看帮助)"))

            return

        try:
            handler(args)

        except Exception as e:
            print(red(f"错误: {e}"))

    # ── 命令实现 ─────────────────────────────────────

    def _cmd_next(self, args: list[str]) -> None:
        if self._debugger.finished:
            print(yellow("所有节点已执行完毕，输入 r 重新开始"))

            return

        result = self._debugger.step()

        if result is None:
            print(yellow("所有节点已执行完毕"))

            return

        status = "⏸ BREAKPOINT" if result.status.name == "BREAKPOINT" else "→"

        print(f"  {green(result.node_id):35s} = {cyan(str(result.value)):15s}  [{status}]  ({result.node_type})")

    def _cmd_run(self, args: list[str]) -> None:
        if self._debugger.finished:
            print(yellow("已执行完毕，重置后重试"))

            return

        results = self._debugger.run_all()

        for r in results:
            status = "⏸ BP" if r.status.name == "BREAKPOINT" else "→"

            print(f"  {green(r.node_id):35s} = {cyan(str(r.value)):15s}  [{status}]  ({r.node_type})")

        if self._debugger.finished:
            print(green("  全部执行完成"))

    def _cmd_run_to(self, args: list[str]) -> None:
        if not args:
            print(yellow("用法: t <node_id>"))

            return

        results = self._debugger.run_to(args[0])

        for r in results:
            status = "⏸ BP" if r.status.name == "BREAKPOINT" else "→"

            print(f"  {green(r.node_id):35s} = {cyan(str(r.value)):15s}  [{status}]  ({r.node_type})")

    def _cmd_break(self, args: list[str]) -> None:
        if not args:
            print(yellow("用法: b <node_id>"))

            return

        self._debugger.add_breakpoint(args[0])

        print(green(f"  断点已设置: {args[0]}"))

    def _cmd_delete_breakpoint(self, args: list[str]) -> None:
        if not args:
            print(yellow("用法: d <node_id>"))

            return

        self._debugger.remove_breakpoint(args[0])

        print(f"  断点已移除: {args[0]}")

    def _cmd_list_breakpoints(self, args: list[str]) -> None:
        bps = self._debugger.list_breakpoints()

        if not bps:
            print("  (无断点)")

        else:
            print("  断点列表:")

            for bp in bps:
                print(f"    • {bp}")

    def _cmd_clear_breakpoints(self, args: list[str]) -> None:
        self._debugger.clear_breakpoints()

        print("  所有断点已清除")

    def _cmd_peek(self, args: list[str]) -> None:
        nid = self._debugger.peek()

        if nid is None:
            print(yellow("  (已无待执行节点)"))

        else:
            info = self._debugger.get_node_info(nid)

            desc = f"  [{info.type}]" if info else ""

            print(f"  下一个: {green(nid)} {desc}")

    def _cmd_values(self, args: list[str]) -> None:
        nv = self._debugger.node_values

        if not nv:
            print("  (尚无已执行节点)")

        else:
            print(f"  当前节点值 ({len(nv)}):")

            for nid, val in nv.items():
                info = self._debugger.get_node_info(nid)

                label = f"  [{info.type}]" if info and info.label else (f"  [{info.type}]" if info else "")

                print(f"    {green(nid):35s} = {cyan(str(val)):15s} {label}")

    def _cmd_outputs(self, args: list[str]) -> None:
        outs = self._debugger.outputs

        if not outs:
            print(yellow("  (尚无可用的输出)"))

        else:
            for oid, val in outs.items():
                print(f"    {green(oid):35s} = {cyan(str(val))}")

    def _cmd_status(self, args: list[str]) -> None:
        done, total = self._debugger.progress

        pct = done / total * 100 if total else 0

        print(f"  进度: {done}/{total} ({pct:.0f}%)")

        bp_count = len(self._debugger.list_breakpoints())

        print(f"  断点: {bp_count}")

    def _cmd_info(self, args: list[str]) -> None:
        if not args:
            print(yellow("用法: i <node_id>"))

            return

        info = self._debugger.get_node_info(args[0])

        if info is None:
            print(yellow(f"  未知节点: {args[0]}"))

        else:
            print(f"  ID:   {green(args[0])}")

            print(f"  类型: {cyan(info.type)}")

            if info.label:
                print(f"  标签: {info.label}")

            if info.description:
                print(f"  描述: {info.description}")

    def _cmd_help(self, args: list[str]) -> None:
        print(bold("命令列表:"))

        print("  n        执行下一步")

        print("  r        执行到结束（遇断点停）")

        print("  t <id>   执行到指定节点（遇断点停）")

        print("  b <id>   设置断点")

        print("  d <id>   移除断点")

        print("  l        列出所有断点")

        print("  c        清除所有断点")

        print("  p        查看下一个待执行节点")

        print("  v        查看当前所有节点值")

        print("  o        查看已完成的输出值")

        print("  s        显示进度")

        print("  i <id>   查看节点信息")

        print("  q        退出")

    def _cmd_quit(self, args: list[str]) -> NoReturn:
        print("再见")

        sys.exit(0)


def main() -> None:
    parser = argparse.ArgumentParser(description="DAG 分步调试器 CLI")

    parser.add_argument("dag_file", type=str, help="DAG JSON 文件路径")

    parser.add_argument("--ctx", type=str, default=None, help="JSON 上下文文件路径（可选）")

    args = parser.parse_args()

    ctx = None

    if args.ctx:
        import json

        ctx = json.loads(Path(args.ctx).read_text(encoding="utf-8"))

    cli = DebuggerCLI()

    cli.run(args.dag_file, ctx)


if __name__ == "__main__":
    main()
