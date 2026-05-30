#!/usr/bin/env python3
""".calcpack 导出器 — 将内存中的适配包数据打包为 ZIP 文件。

用法::

    from tools.designer.exporter import export_calcpack

    export_calcpack(
        output_path="终末地.calcpack",
        meta={...},
        dag={...},
        layout={...},
        theme={...},
        data_files={"characters": [...], "weapons": [...]},
    )
"""

from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path
from typing import Any


def export_calcpack(
    output_path: str | Path,
    meta: dict[str, Any],
    dag: dict[str, Any],
    layout: dict[str, Any],
    *,
    theme: dict[str, Any] | None = None,
    data_files: dict[str, list[dict[str, Any]]] | None = None,
    asset_files: dict[str, str] | None = None,
) -> str:
    """将适配包数据导出为 .calcpack 文件。

    Args:
        output_path: 输出路径（自动补 .calcpack 后缀）
        meta: meta.json 内容
        dag: 主 DAG 公式图
        layout: layout.json 内容
        theme: 可选 theme.json
        data_files: 数据文件映射，key 为文件名（不含路径），
                    value 为实体列表。如 ``{"characters": [...], "weapons": [...]}``
        asset_files: 资产文件映射 {本地路径: ZIP 内目标名称}。
                    文件会复制到 .calcpack 的 assets/ 目录下，
                    layout.json 中的 image_path 会被重写为 assets/<名称>。

    Returns:
        实际写入的路径
    """
    path = Path(output_path)
    if path.suffix.lower() not in (".calcpack", ".zip"):
        path = path.with_suffix(".calcpack")

    patched_layout = _rewrite_layout_asset_paths(layout, asset_files)

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        _write_json_in_zip(zf, "meta.json", meta)
        _write_json_in_zip(zf, "dag/formula.dag.json", dag)
        _write_json_in_zip(zf, "ui/layout.json", patched_layout)

        if theme:
            _write_json_in_zip(zf, "ui/theme.json", theme)

        if data_files:
            for key, records in data_files.items():
                _write_json_in_zip(zf, f"data/{key}.json", records)

        if asset_files:
            for local_path, name in asset_files.items():
                src = Path(local_path)
                if src.is_file():
                    zf.write(str(src), f"assets/{name}")

    return str(path)


def _rewrite_layout_asset_paths(
    layout: dict[str, Any],
    asset_files: dict[str, str] | None,
) -> dict[str, Any]:
    """重写 layout 中 widget 的 image_path 为 assets/ 路径。"""
    if not asset_files:
        return layout

    # 建立反向映射：原始路径 → assets/<name>
    reverse_map: dict[str, str] = {}
    for local_path, name in asset_files.items():
        reverse_map[os.path.normpath(local_path)] = f"assets/{name}"

    patched = json.loads(json.dumps(layout))
    sections = patched.get("sections", [])
    for sec in sections:
        if sec.get("widget_type") == "donation":
            cfg = sec.get("widget_config", {})
            raw = cfg.get("image_path", "")
            if raw:
                normalized = os.path.normpath(raw)
                if normalized in reverse_map:
                    cfg["image_path"] = reverse_map[normalized]
    return patched


_ASSETS_DIR = "assets/"


def extract_assets(pack_path: str | Path, target_dir: str | Path) -> dict[str, str]:
    """从 .calcpack 中提取 assets/ 文件到目标目录。

    Returns:
        {ZIP 内路径: 解压后完整路径} 的映射。
    """
    result: dict[str, str] = {}
    target = Path(target_dir)
    with zipfile.ZipFile(str(pack_path), "r") as zf:
        for name in zf.namelist():
            if name.startswith(_ASSETS_DIR) and not name.endswith("/"):
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                result[name] = str(dest)
    return result


def resolve_asset_paths_in_layout(
    layout: dict[str, Any],
    asset_map: dict[str, str],
) -> dict[str, Any]:
    """将 layout 中的 assets/ 路径替换为解压后的实际文件路径。"""
    patched = json.loads(json.dumps(layout))
    sections = patched.get("sections", [])
    for sec in sections:
        if sec.get("widget_type") == "donation":
            cfg = sec.get("widget_config", {})
            raw = cfg.get("image_path", "")
            if raw in asset_map:
                cfg["image_path"] = asset_map[raw]
            elif raw.startswith(_ASSETS_DIR) and raw in asset_map:
                cfg["image_path"] = asset_map[raw]
    return patched


def _write_json_in_zip(
    zf: zipfile.ZipFile,
    arcname: str,
    data: Any,
) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    zf.writestr(arcname, content)
