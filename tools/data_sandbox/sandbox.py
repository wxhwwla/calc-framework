#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据沙箱 CLI — 在隔离环境中测试自定义游戏数据的命令行工具。

用法::

    # 验证 JSON 文件格式
    python -m tools.data_sandbox.sandbox validate <file>

    # 运行快速计算测试
    python -m tools.data_sandbox.sandbox test <file>

    # 生成完整验证+测试+差异报告
    python -m tools.data_sandbox.sandbox report <file> [-o output.md]

    # 对比自定义数据与本地参考数据
    python -m tools.data_sandbox.sandbox diff <file> <reference>

    # 查看帮助
    python -m tools.data_sandbox.sandbox --help
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from .reporter import Reporter
from .tester import Tester
from .validator import Validator


def main() -> None:
    """CLI 主入口。"""
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        _show_help()
        return

    command = args[0]
    command_args = args[1:]

    commands = {
        "validate": _cmd_validate,
        "test": _cmd_test,
        "report": _cmd_report,
        "diff": _cmd_diff,
    }

    cmd_fn = commands.get(command)
    if cmd_fn is None:
        print(f"未知命令: {command}", file=sys.stderr)
        print("可用命令: validate, test, report, diff", file=sys.stderr)
        sys.exit(1)

    try:
        exit_code = cmd_fn(command_args)
        sys.exit(exit_code)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def _parse_file_arg(args: List[str], index: int) -> Optional[str]:
    """_parse_file_arg 实现。"""
    if index < len(args):
        return args[index]
    return None


def _cmd_validate(args: List[str]) -> int:
    """执行 validate 命令。"""
    file_path = _parse_file_arg(args, 0)
    if not file_path:
        print("用法: sandbox validate <文件路径>", file=sys.stderr)
        return 1

    path = Path(file_path)
    if not path.exists():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        return 1

    print(f"🔍 正在校验: {path}")
    print("")

    validator = Validator()
    result = validator.validate_file(str(path))

    if result.parse_error:
        print(f"❌ 解析错误: {result.parse_error}")
        return 1

    if result.passed:
        print(f"✅ 校验通过 — {result.total_entities} 个实体，0 个错误")
        return 0

    print(f"❌ 校验失败 — {result.total_entities} 个实体，{result.total_errors} 个错误")
    print("")
    for entity in result.entities:
        if entity.errors:
            print(f"  [{entity.index}] {entity.name}:")
            for err in entity.errors:
                print(f"    - ❌ {err}")
    print("")
    return 1


def _cmd_test(args: List[str]) -> int:
    """执行 test 命令。"""
    file_path = _parse_file_arg(args, 0)
    if not file_path:
        print("用法: sandbox test <文件路径>", file=sys.stderr)
        return 1

    path = Path(file_path)
    if not path.exists():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        return 1

    print(f"🧪 正在测试: {path}")
    print("")

    tester = Tester()
    result = tester.test_file(str(path))

    if result.load_error:
        print(f"❌ 加载错误: {result.load_error}")
        return 1

    print(f"共 {result.total} 项测试，"
          f"✅ {result.passed_count} 项通过，"
          f"❌ {result.failed_count} 项未通过")
    print("")

    failed = [item for item in result.items if not item.passed]
    if failed:
        print("--- 失败项 ---")
        for item in failed:
            print(f"  ❌ [{item.entity_name}] {item.test_name}: {item.detail}")
        print("")

    if result.passed:
        return 0
    return 1


def _cmd_report(args: List[str]) -> int:
    """执行 report 命令。"""
    if not args:
        print("用法: sandbox report <文件路径> [-o 输出路径]", file=sys.stderr)
        return 1

    file_path = args[0]
    output_path: Optional[str] = None

    i = 1
    while i < len(args):
        if args[i] == "-o" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        else:
            print(f"未知参数: {args[i]}", file=sys.stderr)
            return 1

    path = Path(file_path)
    if not path.exists():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        return 1

    print(f"📊 正在生成报告: {path}")
    print("")

    reporter = Reporter()
    report = reporter.generate_from_file(str(path))

    markdown = reporter.render_markdown(report)

    if output_path:
        output = Path(output_path)
        with open(output, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"✅ 报告已写入: {output}")
    else:
        print(markdown)

    return 0 if report.validation.passed and report.test.passed else 1


def _cmd_diff(args: List[str]) -> int:
    """执行 diff 命令。"""
    if len(args) < 2:
        print("用法: sandbox diff <自定义文件> <参考文件>", file=sys.stderr)
        return 1

    file_path = args[0]
    ref_path = args[1]

    path = Path(file_path)
    ref = Path(ref_path)

    if not path.exists():
        print(f"错误: 文件不存在: {path}", file=sys.stderr)
        return 1
    if not ref.exists():
        print(f"错误: 参考文件不存在: {ref}", file=sys.stderr)
        return 1

    print(f"🔍 正在对比: {path} ↔ {ref}")
    print("")

    reporter = Reporter()
    report = reporter.generate_from_file(
        str(path),
        reference_path=str(ref),
        reference_label=str(ref),
    )

    if report.diff is None:
        print("⚠️ 差异比较无数据")
        return 1

    if not report.diff.has_changes:
        print("✅ 无差异 — 自定义数据与参考数据完全一致")
        return 0

    diff = report.diff
    print(f"📊 数据差异报告")
    print(f"   参考数据: {diff.total_old} 条")
    print(f"   自定义数据: {diff.total_new} 条")
    print(f"   差异: ", end="")
    parts = []
    if diff.added:
        parts.append(f"+{diff.added} 新增")
    if diff.removed:
        parts.append(f"-{diff.removed} 删除")
    if diff.modified:
        parts.append(f"~{diff.modified} 修改")
    print(", ".join(parts))
    print("")

    for line in diff.detail_lines:
        print(line)

    return 2


def _show_help() -> None:
    """_show_help 实现。"""
    print(__doc__)


if __name__ == "__main__":
    main()
