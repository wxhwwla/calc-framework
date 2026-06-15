#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""搜索结果导出。"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path

from games.endfield.calc.loadout.optimizer import LoadoutScore


def _sorted_scores(scores: Iterable[LoadoutScore]) -> list[LoadoutScore]:
    """sorted scores。"""
    return sorted(scores, key=lambda s: s.final_damage, reverse=True)


def _score_to_row(score: LoadoutScore, rank: int) -> dict[str, object]:
    return {
        "rank": rank,
        "weapon_name": score.weapon_name,
        "final_damage": score.final_damage,
        "chest": score.loadout_names.get("chest", ""),
        "gloves": score.loadout_names.get("gloves", ""),
        "accessory_a": score.loadout_names.get("accessory_a", ""),
        "accessory_b": score.loadout_names.get("accessory_b", ""),
    }
    """score to row。"""


def export_search_outputs(
    *,
    scores: Iterable[LoadoutScore],
    output_dir: Path,
    top_n: int = 10,
    export_all: bool = True,
) -> dict[str, Path]:
    """导出 TopN（JSON/CSV）与全量 NDJSON。"""

    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    sorted_scores = _sorted_scores(scores)

    top_scores = sorted_scores[: max(1, int(top_n))]

    top_rows = [_score_to_row(score, idx + 1) for idx, score in enumerate(top_scores)]

    top_json = output_dir / "top_results.json"

    top_json.write_text(json.dumps(top_rows, ensure_ascii=False, indent=2), encoding="utf-8")

    top_csv = output_dir / "top_results.csv"

    with top_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "weapon_name",
                "final_damage",
                "chest",
                "gloves",
                "accessory_a",
                "accessory_b",
            ],
        )

        writer.writeheader()

        writer.writerows(top_rows)

    outputs: dict[str, Path] = {"top_json": top_json, "top_csv": top_csv}

    if export_all:
        all_ndjson = output_dir / "all_results.ndjson"

        with all_ndjson.open("w", encoding="utf-8") as f:
            for idx, score in enumerate(sorted_scores, start=1):
                f.write(json.dumps(_score_to_row(score, idx), ensure_ascii=False) + "\n")

        outputs["all_ndjson"] = all_ndjson

    return outputs
