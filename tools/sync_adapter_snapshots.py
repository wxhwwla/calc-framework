#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""将层 A 运行时数据同步为层 B 适配器快照（ADR-0023 Step 4.3）。

终末地：``games/endfield/data/*.json`` → ``framework/adapters/endfield/data/*_standard.json``
明日方舟：``tools/arknights_scout/output/parsed/`` → ``operators_standard.json``

用法::

    python tools/sync_adapter_snapshots.py --game endfield --dry-run
    python tools/sync_adapter_snapshots.py --game endfield --apply
    python tools/sync_adapter_snapshots.py --game arknights --apply
    python tools/sync_adapter_snapshots.py --game all --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.data_pipeline.transformers.from_legacy_endfield import from_characters, from_weapons
from utils.game_data_paths import (
    ENDFIELD_CHARACTERS_JSON,
    ENDFIELD_CHARACTERS_STANDARD,
    ENDFIELD_EQUIPMENTS_JSON,
    ENDFIELD_EQUIPMENTS_STANDARD,
    ENDFIELD_WEAPONS_JSON,
    ENDFIELD_WEAPONS_STANDARD,
    ARKNIGHTS_PARSED_DIR,
    ARKNIGHTS_OPERATORS_STANDARD,
)


def _write_json(path: Path, data: Any, *, apply: bool) -> dict[str, Any]:
    """写入 JSON 或 dry-run 仅统计。"""
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    return {"path": str(path), "bytes": len(payload.encode("utf-8")), "written": apply}


def _load_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"{path} 根节点必须是 JSON 数组")
    return [dict(x) for x in raw if isinstance(x, dict)]


def sync_endfield_snapshots(*, apply: bool = False) -> dict[str, Any]:
    """终末地层 A → 层 B：角色/武器迁移，装备直拷贝。"""
    results: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        chars = from_characters(_load_json_array(ENDFIELD_CHARACTERS_JSON))
        results.append(_write_json(ENDFIELD_CHARACTERS_STANDARD, chars, apply=apply))
        results[-1]["records"] = len(chars)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"characters: {exc}")

    try:
        weapons = from_weapons(_load_json_array(ENDFIELD_WEAPONS_JSON))
        results.append(_write_json(ENDFIELD_WEAPONS_STANDARD, weapons, apply=apply))
        results[-1]["records"] = len(weapons)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"weapons: {exc}")

    try:
        equipments = _load_json_array(ENDFIELD_EQUIPMENTS_JSON)
        results.append(_write_json(ENDFIELD_EQUIPMENTS_STANDARD, equipments, apply=apply))
        results[-1]["records"] = len(equipments)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"equipments: {exc}")

    return {
        "success": not errors,
        "game": "endfield",
        "apply": apply,
        "outputs": results,
        "errors": errors,
    }


def sync_arknights_snapshot(
    *,
    parsed_dir: Path | None = None,
    apply: bool = False,
) -> dict[str, Any]:
    """明日方舟 parsed → ``operators_standard.json``（层 B）。"""
    from tools.data_pipeline.transformers.from_arknights_scout import convert_all

    parsed = parsed_dir or ARKNIGHTS_PARSED_DIR
    out = ARKNIGHTS_OPERATORS_STANDARD
    if not apply:
        # dry-run：不写盘，仅统计可转换条数
        if not parsed.is_dir():
            return {"success": False, "game": "arknights", "error": f"目录不存在: {parsed}"}
        count = sum(1 for f in parsed.glob("*.json") if f.stem not in {"_sync_summary", "operators"})
        return {
            "success": True,
            "game": "arknights",
            "apply": False,
            "parsed_dir": str(parsed),
            "would_write": str(out),
            "estimated_records": count,
        }

    stats = convert_all(parsed, out)
    stats["game"] = "arknights"
    stats["apply"] = True
    return stats


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="同步适配器快照（层 A → 层 B）")
    parser.add_argument(
        "--game",
        choices=("endfield", "arknights", "all"),
        required=True,
        help="要同步的游戏",
    )
    parser.add_argument("--apply", action="store_true", help="写入文件（默认 dry-run）")
    parser.add_argument(
        "--parsed-dir",
        type=Path,
        default=None,
        help="明日方舟 parsed 目录（默认 tools/arknights_scout/output/parsed）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口。"""
    args = _parse_args(argv)
    apply = args.apply
    mode = "apply" if apply else "dry-run"
    exit_code = 0

    if args.game in ("endfield", "all"):
        stats = sync_endfield_snapshots(apply=apply)
        print(f"[{mode}] endfield success={stats['success']}")
        for out in stats.get("outputs", []):
            rec = out.get("records", "?")
            print(f"  {out['path']}: {rec} 条, {out['bytes']} bytes, written={out['written']}")
        for err in stats.get("errors", []):
            print(f"  [错误] {err}")
            exit_code = 1

    if args.game in ("arknights", "all"):
        stats = sync_arknights_snapshot(parsed_dir=args.parsed_dir, apply=apply)
        print(f"[{mode}] arknights success={stats.get('success')}")
        if stats.get("error"):
            print(f"  [错误] {stats['error']}")
            exit_code = 1
        elif apply:
            print(f"  {stats.get('output_file')}: {stats.get('converted')}/{stats.get('total_files')} 干员")
        else:
            print(f"  would_write={stats.get('would_write')} estimated={stats.get('estimated_records')}")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
