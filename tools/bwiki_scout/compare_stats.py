#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""

仅根据已有 output/raw 缓存生成逐级数值对比报告（不访问网络）。



若缺 */详细数据 页，请先运行 scout.py。

"""

from __future__ import annotations


import argparse

import sys

from pathlib import Path


_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent

if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))


from bwiki_scout.config import LOCAL_CHARACTERS_JSON, OUTPUT_ROOT

from bwiki_scout.detail_levels import build_operator_stats_diff

from bwiki_scout.report import write_stats_diff_report


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(description="BWIKI 干员逐级数值对比（离线）")

    parser.add_argument(
        "--input",
        type=Path,
        default=OUTPUT_ROOT,
        help="scout 输出目录",
    )

    args = parser.parse_args(argv)

    stats = build_operator_stats_diff(
        output_root=args.input,
        characters_json=LOCAL_CHARACTERS_JSON,
    )

    path = write_stats_diff_report(args.input / "reports", stats)

    print(f"报告: {path}")

    print(
        f"缺详细页 {len(stats['missing_detail_pages'])}，"
        f"完全一致 {len(stats['perfect_match'])}，"
        f"已对比 {len(stats['operators'])} 人"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
