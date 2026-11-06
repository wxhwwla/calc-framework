# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout 命令行入口。

用法:
    python -m tools.wiki_scout list
    python -m tools.wiki_scout fetch warfarin --limit 5
    python -m tools.wiki_scout parse warfarin
    python -m tools.wiki_scout run all

产物:
    tools/wiki_scout/output/<provider>/raw.json   原始响应（可重复解析）
    tools/wiki_scout/output/<provider>/<provider>.json  标准化数据
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any

from .fetcher import Fetcher
from .providers.base import BaseProvider
from .registry import get_provider, list_providers

_OUTPUT = Path(__file__).resolve().parent / "output"


def main(argv: list[str] | None = None) -> int:
    """CLI 入口，返回进程退出码。"""
    importlib.import_module("tools.wiki_scout.providers")  # 触发 provider 注册
    parser = argparse.ArgumentParser(
        prog="python -m tools.wiki_scout",
        description="模块化 Wiki 数据采集工具",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="列出已注册数据源")

    for command in ("fetch", "parse", "run"):
        sub = subparsers.add_parser(command, help=_COMMAND_HELP[command])
        sub.add_argument("provider", help="provider 名称，或 all")
        sub.add_argument("--limit", type=int, default=None, help="限制每个集合抓取条目数")
        sub.add_argument("--out-dir", type=Path, default=_OUTPUT, help="输出目录")
        if command != "parse":
            sub.add_argument("--refresh", action="store_true", help="忽略缓存重新抓取")

    args = parser.parse_args(argv)

    if args.command == "list":
        for name, description in list_providers().items():
            print(f"{name}: {description}")
        return 0

    names = list(list_providers()) if args.provider == "all" else [args.provider]
    exit_code = 0
    for name in names:
        try:
            provider = get_provider(name)
            _run_one(args.command, provider, args)
        except Exception as exc:
            print(f"[FAIL] {name}: {exc}", file=sys.stderr)
            exit_code = 1
    return exit_code


_COMMAND_HELP = {
    "fetch": "只抓取原始响应（写入 raw.json）",
    "parse": "只解析本地 raw.json（离线）",
    "run": "抓取并解析",
}


def _run_one(command: str, provider: BaseProvider, args: argparse.Namespace) -> None:
    provider_dir = args.out_dir / provider.name
    raw_path = provider_dir / "raw.json"
    parsed_path = provider_dir / f"{provider.name}.json"

    if command in ("fetch", "run"):
        fetcher = Fetcher(args.out_dir / ".cache")
        raw = provider.fetch(fetcher, limit=args.limit, refresh=args.refresh)
        _write_json(raw_path, raw)
        print(f"[fetch] {provider.name} -> {raw_path}")
        if command == "fetch":
            return
    else:
        raw = json.loads(raw_path.read_text(encoding="utf-8"))

    parsed = provider.parse(raw)
    _write_json(parsed_path, parsed)
    print(f"[parse] {provider.name} -> {parsed_path} ({_summary(parsed)})")


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _summary(data: dict[str, Any]) -> str:
    parts = [f"{key}={len(value)}" for key, value in data.items() if isinstance(value, list)]
    return " ".join(parts) or "ok"
