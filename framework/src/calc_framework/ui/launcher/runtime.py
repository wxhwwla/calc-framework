# SPDX-License-Identifier: AGPL-3.0
"""启动器运行时：适配器发现与子进程启动。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from calc_framework.config.manager import _get_adapters_dir

# 完整桌面计算器入口（按 adapters/ 子目录 id）
_FULL_APP_SCRIPTS: dict[str, str] = {
    "endfield": "scripts/main.py",
    "arknights": "scripts/main_arknights.py",
}


@dataclass(frozen=True)
class AdapterEntry:
    """已发现的适配包摘要。"""

    adapter_id: str
    name: str
    game: str
    version: str
    description: str
    path: Path

    @property
    def has_full_app(self) -> bool:
        return self.adapter_id in _FULL_APP_SCRIPTS


def repo_root() -> Path:
    """仓库根目录（framework/src/calc_framework/ui/launcher → 上溯 5 级）。"""
    return Path(__file__).resolve().parents[5]


def build_pythonpath(root: Path | None = None) -> str:
    """子进程 PYTHONPATH：framework 源码 + 根 + tools + endfield GUI 包。"""
    base = root or repo_root()
    parts = [
        str(base / "framework" / "src"),
        str(base),
        str(base / "tools"),
        str(base / "games" / "endfield"),
    ]
    existing = os.environ.get("PYTHONPATH", "")
    if existing:
        parts.append(existing)
    return os.pathsep.join(parts)


def list_adapter_entries(adapters_dir: Path | None = None) -> list[AdapterEntry]:
    """扫描 adapters/，返回按名称排序的条目。"""
    base = adapters_dir or _get_adapters_dir()
    if not base.is_dir():
        return []

    entries: list[AdapterEntry] = []
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        meta_path = entry / "meta.json"
        if not meta_path.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        entries.append(
            AdapterEntry(
                adapter_id=entry.name,
                name=str(meta.get("name") or entry.name),
                game=str(meta.get("game") or ""),
                version=str(meta.get("version") or "?"),
                description=str(meta.get("description") or ""),
                path=entry,
            )
        )
    return sorted(entries, key=lambda e: e.name)


def argv_for_adapter(entry: AdapterEntry, root: Path | None = None) -> list[str]:
    """构造启动适配器的命令行参数。"""
    base = root or repo_root()
    script = _FULL_APP_SCRIPTS.get(entry.adapter_id)
    if script:
        return [sys.executable, str(base / script)]
    return [sys.executable, "-m", "calc_framework.launcher", entry.name]


def argv_for_tool(tool_id: str, root: Path | None = None) -> list[str]:
    """构造启动工具的命令行参数。"""
    base = root or repo_root()
    mapping: dict[str, list[str]] = {
        "designer": [sys.executable, str(base / "scripts" / "main_designer.py")],
        "pack_designer": [sys.executable, str(base / "scripts" / "main_pack_designer.py")],
        "viewer": [sys.executable, "-m", "calc_framework.ui.viewer"],
        "graph_editor": [sys.executable, "-m", "calc_framework.graph_editor"],
        "layout_editor": [sys.executable, "-m", "calc_framework.editor"],
    }
    if tool_id not in mapping:
        raise KeyError(f"未知工具: {tool_id}")
    return mapping[tool_id]


def argv_for_calcpack(path: Path, root: Path | None = None) -> list[str]:
    """打开 .calcpack 文件。"""
    base = root or repo_root()
    return [sys.executable, "-m", "calc_framework.ui.viewer", str(path.resolve())]


def spawn_detached(argv: list[str], root: Path | None = None) -> subprocess.Popen[bytes]:
    """在独立子进程中启动（不阻塞启动器）。"""
    base = root or repo_root()
    env = os.environ.copy()
    env["PYTHONPATH"] = build_pythonpath(base)
    kwargs: dict = {
        "cwd": str(base),
        "env": env,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE  # type: ignore[attr-defined]
    return subprocess.Popen(argv, **kwargs)  # noqa: S603
