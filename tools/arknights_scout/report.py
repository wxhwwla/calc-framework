# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""侦察报告生成。"""

import json
from pathlib import Path
from typing import Any


def write_summary_report(reports_dir: Path, *, manifest: dict[str, Any], **kwargs: Any) -> Path:
    """write_summary_report 实现。

    Args:
        reports_dir: 参数描述。

    Returns:
        返回值描述。
    """
    path = reports_dir / "summary.json"
    data = {
        "manifest": manifest,
        "total_pages": manifest.get("fetched_pages", 0),
        **{k: v for k, v in kwargs.items()},
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_names_diff_report(reports_dir: Path, name_diff: dict[str, Any]) -> Path:
    """write_names_diff_report 实现。

    Args:
        reports_dir: 参数描述。
        name_diff: 参数描述。

    Returns:
        返回值描述。
    """
    path = reports_dir / "names_diff.json"
    path.write_text(json.dumps(name_diff, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_schema_diff_report(
    reports_dir: Path,
    local_schema: list[dict[str, Any]],
    **kwargs: Any,
) -> Path:
    """write_schema_diff_report 实现。

    Args:
        reports_dir: 参数描述。
        local_schema: 参数描述。

    Returns:
        返回值描述。
    """
    path = reports_dir / "schema_diff.json"
    data = {"local_schema": local_schema, **{k: v for k, v in kwargs.items()}}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_sample_bundle(
    reports_dir: Path,
    kind: str,
    *,
    wiki_bundle: dict[str, Any] | None = None,
    local_sample: Any = None,
) -> Path:
    """write_sample_bundle 实现。

    Args:
        reports_dir: 参数描述。
        kind: 参数描述。

    Returns:
        返回值描述。
    """
    path = reports_dir / f"sample_{kind}.json"
    data = {
        "kind": kind,
        "wiki_title": (wiki_bundle or {}).get("title", ""),
        "wiki_snippet": ((wiki_bundle or {}).get("wikitext") or "")[:2000],
    }
    if local_sample:
        data["local_sample"] = local_sample
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_stats_diff_report(reports_dir: Path, stats_diff: Any) -> Path:
    """write_stats_diff_report 实现。

    Args:
        reports_dir: 参数描述。
        stats_diff: 参数描述。

    Returns:
        返回值描述。
    """
    path = reports_dir / "stats_diff.json"
    path.write_text(json.dumps(stats_diff, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
