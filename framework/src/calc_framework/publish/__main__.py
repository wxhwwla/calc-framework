# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""适配包校验与静态 catalog 生成命令行入口。"""

from __future__ import annotations

import argparse

from calc_framework.publish.catalog import build_catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 Calc Framework 适配器静态目录")
    parser.add_argument("--output", help="可选输出目录；省略时仅打印 HTML")
    args = parser.parse_args()
    html = build_catalog(args.output)
    if not args.output:
        print(html)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
