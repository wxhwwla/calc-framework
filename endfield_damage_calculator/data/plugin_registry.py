#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
插件化数据：从应用目录 ``plugins/`` 热加载 JSON/YAML 敌人等配置。

核心引擎仍读内置 ``characters.json``；插件用于扩展敌方参数等，不替换主数据。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - 可选依赖
    yaml = None  # type: ignore[assignment]


def _read_config_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("加载 YAML 插件需要安装 PyYAML: pip install pyyaml")
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"插件文件根节点必须是对象: {path}")
    return data


class PluginRegistry:
    """已加载插件数据的内存注册表。"""

    def __init__(self) -> None:
        self._enemies: dict[str, dict[str, Any]] = {}

    def load_from_directory(self, root: Path) -> int:
        """
        扫描 ``root/enemies/*.{json,yaml,yml}`` 并注册。

        返回本次加载的条目数。
        """
        self._enemies.clear()
        enemies_dir = Path(root) / "enemies"
        if not enemies_dir.is_dir():
            return 0
        loaded = 0
        patterns = ("*.json", "*.yaml", "*.yml")
        paths: list[Path] = []
        for pattern in patterns:
            paths.extend(sorted(enemies_dir.glob(pattern)))
        for path in paths:
            record = _read_config_file(path)
            enemy_id = str(record.get("id") or path.stem)
            record.setdefault("id", enemy_id)
            self._enemies[enemy_id] = record
            loaded += 1
        return loaded

    def get_enemy(self, enemy_id: str) -> Optional[dict[str, Any]]:
        return self._enemies.get(enemy_id)

    def list_enemy_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._enemies))

    def enemy_count(self) -> int:
        return len(self._enemies)


_registry: Optional[PluginRegistry] = None


def get_plugin_registry() -> PluginRegistry:
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
    return _registry


def load_default_plugins(base_dir: Path) -> int:
    """从 ``base_dir/plugins`` 加载；目录不存在时返回 0。"""
    plugin_root = Path(base_dir) / "plugins"
    if not plugin_root.is_dir():
        return 0
    return get_plugin_registry().load_from_directory(plugin_root)
