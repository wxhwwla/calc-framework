#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""从 framework/adapters 导出示例 .calcpack（fps / moba / card_rpg）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools.designer.exporter import export_calcpack

ADAPTER_ROOT = _REPO / "framework" / "adapters"
OUTPUT_DIR = _REPO / "web" / "hub" / "samples"
SAMPLE_IDS = ("fps", "moba", "card_rpg")


def _load_json(path: Path) -> dict | list:
    """_load_json 实现。"""
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_dag_path(adapter_dir: Path, meta: dict) -> Path:
    """_resolve_dag_path 实现。"""
    entry = meta.get("entry_dag", "dag/formula.dag.json")
    candidates = [
        adapter_dir / entry,
        adapter_dir / "dag" / "formula.dag.json",
        adapter_dir / f"{adapter_dir.name}.dag.json",
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(f"DAG not found for {adapter_dir.name}")


def export_one(adapter_id: str) -> Path:
    """ export_one 实现。

    Args:
        adapter_id: 参数描述。

    Returns:
        返回值描述。
    """
    adapter_dir = ADAPTER_ROOT / adapter_id
    meta = _load_json(adapter_dir / "meta.json")
    meta = dict(meta)
    meta["entry_dag"] = "dag/formula.dag.json"
    meta.setdefault("ui_layout", "ui/layout.json")

    dag = _load_json(_resolve_dag_path(adapter_dir, meta))
    layout_path = adapter_dir / meta.get("ui_layout", "ui/layout.json")
    layout = _load_json(layout_path)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"{adapter_id}_sample.calcpack"
    export_calcpack(
        output_path=out,
        meta=meta,
        dag=dag,
        layout=layout,
        theme=None,
        data_files=None,
    )
    return out


def main() -> int:
    """CLI 入口：导出所有示例 .calcpack 文件。"""
    written: list[str] = []
    for aid in SAMPLE_IDS:
        path = export_one(aid)
        written.append(str(path.relative_to(_REPO)))
        print(f"OK {path}")
    print(f"Exported {len(written)} sample calcpacks to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
