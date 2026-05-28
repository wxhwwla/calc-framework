"""适配器管理器 — 发现、缓存和加载适配包。

适配器搜索路径：
1. ``CALC_ADAPTERS_DIR`` 环境变量（如果设置）
2. 相对于框架安装目录的 ``../adapters/``
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from calc_framework.config.adapter import AdapterPackage


def _default_adapters_dir() -> Path:
    """默认适配器路径：相对于框架包所在树的 ``adapters/``。"""
    return Path(__file__).resolve().parents[3] / "adapters"


def _get_adapters_dir() -> Path:
    env = os.environ.get("CALC_ADAPTERS_DIR")
    if env:
        p = Path(os.fspath(env))
        if p.is_dir():
            return p
    return _default_adapters_dir()


def discover_adapters(adapters_dir: Path | None = None) -> dict[str, Path]:
    """扫描适配器目录，返回 {适配器名: 目录路径} 字典。

    每个适配包必须包含 ``meta.json``。
    """
    base = adapters_dir or _get_adapters_dir()
    if not base.is_dir():
        return {}

    adapters: dict[str, Path] = {}
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        meta_path = entry / "meta.json"
        if not meta_path.is_file():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            name = meta.get("name") or entry.name
            adapters[name] = entry
        except (json.JSONDecodeError, OSError):
            continue
    return adapters


class AdapterManager:
    """适配器管理器 — 单例服务。

    自动发现适配器目录下的适配包，提供按名称加载的能力。
    """

    def __init__(self, adapters_dir: Path | None = None) -> None:
        self._dir = adapters_dir or _get_adapters_dir()
        self._cache: dict[str, AdapterPackage] = {}
        self._available: dict[str, Path] = {}
        self._discover()

    def _discover(self) -> None:
        self._available = discover_adapters(self._dir)
        for name in list(self._cache.keys()):
            if name not in self._available:
                self._cache.pop(name, None)

    @property
    def available_adapters(self) -> dict[str, Path]:
        return dict(self._available)

    @property
    def names(self) -> list[str]:
        return list(self._available.keys())

    def load(self, name: str) -> AdapterPackage:
        """按名称加载适配包（带缓存）。"""
        if name in self._cache:
            return self._cache[name]

        if name not in self._available:
            self._discover()
            if name not in self._available:
                raise KeyError(f"适配器 {name!r} 未找到。可用: {list(self._available.keys())}")

        pkg = AdapterPackage(self._available[name])
        self._cache[name] = pkg
        return pkg

    def reload(self, name: str) -> AdapterPackage:
        """强制重新加载指定适配包。"""
        self._cache.pop(name, None)
        return self.load(name)

    def refresh(self) -> None:
        """刷新所有发现。"""
        self._cache.clear()
        self._discover()

    def summary(self) -> list[dict[str, Any]]:
        """返回所有适配器的摘要信息。"""
        results: list[dict[str, Any]] = []
        for name, path in self._available.items():
            meta_path = path / "meta.json"
            meta: dict[str, Any] = {}
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
            results.append({
                "name": name,
                "path": str(path),
                "version": meta.get("version", "?"),
                "description": meta.get("description", ""),
            })
        return results
