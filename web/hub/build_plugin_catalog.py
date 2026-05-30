"""
构建 Calc Hub 插件目录 (plugins_catalog.json)。

从 framework 的内置插件注册表扫描插件元信息，
同时扫描 web/hub/plugins/ 下的外部插件包，
生成为 hub 可消费的 JSON 目录。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _find_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _discover_builtin_plugins() -> list[dict]:
    """通过 import 内置插件模块获取元信息。"""
    repo = _find_repo_root()
    src = repo / "framework" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

    plugins: list[dict] = []
    try:
        from calc_framework.plugin.base import BasePlugin
        from calc_framework.plugin.builtin import CritPlugin, DistanceDecayPlugin, DodgePlugin

        for plugin_cls in [CritPlugin, DodgePlugin, DistanceDecayPlugin]:
            instance: BasePlugin = plugin_cls()
            meta = instance.meta
            data = instance.on_load()
            var_count = len(data.get("variables", {}))
            tpl_count = len(data.get("templates", {}))
            func_count = len(data.get("functions", {}))
            plugins.append({
                "name": meta.name,
                "version": meta.version,
                "description": meta.description,
                "author": meta.author,
                "type": "builtin",
                "dependencies": meta.dependencies,
                "stats": {
                    "variables": var_count,
                    "templates": tpl_count,
                    "functions": func_count,
                },
                "tags": ["内置"],
            })
    except ImportError as e:
        print(f"警告: 无法导入内置插件模块: {e}", file=sys.stderr)
    return plugins


def _discover_external_plugins(repo_root: Path) -> list[dict]:
    """扫描 web/hub/plugins/ 下的外部插件包。"""
    plugins_dir = repo_root / "web" / "hub" / "plugins"
    if not plugins_dir.is_dir():
        return []
    plugins: list[dict] = []
    for pdir in sorted(plugins_dir.iterdir()):
        meta_path = pdir / "plugin.json"
        if meta_path.is_file():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta.setdefault("type", "external")
                meta.setdefault("tags", [])
                plugins.append(meta)
            except Exception as e:
                print(f"警告: 无法加载 {meta_path}: {e}", file=sys.stderr)
    return plugins


def build_plugin_catalog(output_path: str | Path | None = None) -> dict:
    repo_root = _find_repo_root()
    builtin = _discover_builtin_plugins()
    external = _discover_external_plugins(repo_root)

    catalog = {
        "schema_version": "plugins-v1",
        "name": "Calc Hub Plugin Catalog",
        "updated": "2026-05-30",
        "plugins": builtin + external,
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"插件目录已写入: {out} ({len(catalog['plugins'])} 个插件)")

    return catalog


if __name__ == "__main__":
    repo_root = _find_repo_root()
    output = repo_root / "web" / "hub" / "plugins_catalog.json"
    build_plugin_catalog(output)
