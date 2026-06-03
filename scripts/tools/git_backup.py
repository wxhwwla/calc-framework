#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""上传前备份本地 .git 目录（minor 级别上传触发）。"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

GIT_BACKUP_ROOT = "git_backup"
SNAPSHOTS_SUBDIR = "snapshots"
MAX_SNAPSHOTS = 5
MANIFEST_NAME = "MANIFEST.json"


def snapshots_dir(repo_root: Path | None = None) -> Path:
    root = repo_root or Path.cwd()
    return root / GIT_BACKUP_ROOT / SNAPSHOTS_SUBDIR


def _git_head(repo_root: Path) -> str | None:
    git_dir = repo_root / ".git"
    if not git_dir.is_dir():
        return None
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return value or None


def _snapshot_name(current_version: str, bump_kind: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_version = current_version.replace("/", "_")
    return f"{stamp}_v{safe_version}_{bump_kind}"


def _write_manifest(
    dest: Path,
    *,
    current_version: str,
    bump_kind: str,
    head: str | None,
) -> None:
    payload = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "current_version": current_version,
        "bump_kind": bump_kind,
        "head": head,
        "restore_hint": ("关闭 IDE 后删除工作区 .git，再将本目录下的 .git 复制回仓库根目录"),
    }
    dest.joinpath(MANIFEST_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _prune_old_snapshots(root: Path, *, keep: int = MAX_SNAPSHOTS) -> None:
    if keep <= 0 or not root.is_dir():
        return
    entries = [p for p in root.iterdir() if p.is_dir()]
    entries.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for old in entries[keep:]:
        shutil.rmtree(old, ignore_errors=True)


def backup_git_dir(
    repo_root: Path | None = None,
    *,
    current_version: str,
    bump_kind: str = "minor",
) -> Path:
    """复制 .git 到 git_backup/snapshots/，返回快照目录路径。"""
    root = (repo_root or Path.cwd()).resolve()
    src = root / ".git"
    if not src.is_dir():
        raise FileNotFoundError(f"未找到 .git 目录: {src}")

    dest_root = snapshots_dir(root)
    dest_root.mkdir(parents=True, exist_ok=True)
    dest = dest_root / _snapshot_name(current_version, bump_kind)
    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(src, dest / ".git", symlinks=True)
    _write_manifest(dest, current_version=current_version, bump_kind=bump_kind, head=_git_head(root))
    _prune_old_snapshots(dest_root)
    return dest
