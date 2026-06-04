# SPDX-License-Identifier: AGPL-3.0
"""将缓存 wikitext 解析为结构化 JSON，写入 parsed/ 目录。"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from arknights_scout.parse_operator import parse_operator
from arknights_scout.storage import load_page_bundle


def sync_operators(
    raw_dir: Path,
    output_dir: Path,
    *,
    names: list[str] | None = None,
) -> dict[str, Any]:
    """sync_operators 实现。

    Args:
        raw_dir: 参数描述。
        output_dir: 参数描述。

    Returns:
        返回值描述。
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    all_operators: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    stats = {"total": 0, "parsed": 0, "failed": 0}

    candidates = sorted(raw_dir.iterdir())
    for d in candidates:
        if not d.is_dir():
            continue
        bundle = load_page_bundle(raw_dir, d.name)
        if not bundle or not bundle.get("wikitext", "").strip():
            continue
        title = bundle.get("title", d.name)
        if names is not None and title not in names:
            continue

        stats["total"] += 1
        try:
            result = parse_operator(bundle["wikitext"])
        except Exception as exc:
            errors.append({"title": title, "error": str(exc)})
            stats["failed"] += 1
            continue

        if result is None:
            errors.append({"title": title, "error": "parse_operator returned None"})
            stats["failed"] += 1
            continue

        result["_source"] = "arknights_bwiki"
        result["_updated_at"] = datetime.now(timezone.utc).isoformat()

        safe_name = d.name
        op_path = output_dir / f"{safe_name}.json"
        op_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        all_operators.append(result)
        stats["parsed"] += 1

    all_path = output_dir / "operators.json"
    all_path.write_text(
        json.dumps(all_operators, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = {
        "stats": stats,
        "errors": errors,
        "output_dir": str(output_dir),
        "all_operators_path": str(all_path),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path = output_dir / "_sync_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return summary


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    import argparse

    parser = argparse.ArgumentParser(description="同步干员 wikitext → 结构化 JSON")
    parser.add_argument("--raw-dir", type=Path, default=None, help="原始缓存目录")
    parser.add_argument("--output", type=Path, default=None, help="输出目录")
    parser.add_argument("--names", nargs="*", default=None, help="仅处理指定干员名")
    args = parser.parse_args(argv)

    output_root = Path("tools/arknights_scout/output")
    raw_dir = args.raw_dir or (output_root / "raw")
    output_dir = args.output or (output_root / "parsed")

    summary = sync_operators(raw_dir, output_dir, names=args.names)

    s = summary["stats"]
    print(f"同步完成: {s['total']} 总 / {s['parsed']} 成功 / {s['failed']} 失败")
    if summary["errors"]:
        for e in summary["errors"]:
            print(f"  FAIL: {e['title']}: {e['error']}")
    print(f"输出目录: {summary['output_dir']}")
    return 0 if s["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
