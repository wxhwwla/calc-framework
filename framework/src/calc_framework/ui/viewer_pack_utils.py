# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
".calcpack I/O 工具 — 加载/解压/资源提取 + 实体 context 构建。"

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from utils.zip_safety import validate_zip_member_name

from calc_framework.data.entity_sources import (
    DATA_STEM_SOURCE,
    SOURCE_DATA_STEMS,
    SOURCE_DISPLAY_NAMES,
)

_MAX_PACK_ENTRIES = 10_000
_MAX_PACK_BYTES = 64 * 1024 * 1024

_VARIABLE_FIELD_MAP: dict[str, str] = {
    "基础攻击力": "基础攻击",
}

_SOURCE_TO_DATA_FILE: dict[str, str] = dict(SOURCE_DATA_STEMS)

_DATA_FILE_TO_SOURCE: dict[str, str] = dict(DATA_STEM_SOURCE)

_SOURCE_DISPLAY_NAMES: dict[str, str] = dict(SOURCE_DISPLAY_NAMES)

_FALLBACK_DEFAULTS: dict[str, float] = {
    "技能倍率": 1.0,
    "伤害加成": 0.0,
    "伤害减免": 0.0,
    "增幅": 0.0,
    "虚弱": 0.0,
    "庇护": 0.0,
    "脆弱": 0.0,
    "易伤": 0.0,
    "失衡易伤": 0.0,
    "抗性": 0.0,
    "非主控减伤": 0.0,
    "连击增伤": 0.0,
    "特殊乘区": 1.0,
    "主能力平值加算": 0.0,
    "副能力平值加算": 0.0,
    "主能力百分比": 0.0,
    "副能力百分比": 0.0,
    "力量加成值": 0.0,
    "敏捷加成值": 0.0,
    "智识加成值": 0.0,
    "意志加成值": 0.0,
    "防御": 100.0,
    "暴击率": 0.05,
    "暴击伤害": 0.5,
}

_ASSETS_DIR = "assets/"


def _validated_infos(zf: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    """校验条目名、数量与解压后总大小，返回文件条目。"""
    infos = [info for info in zf.infolist() if not info.is_dir()]
    if len(infos) > _MAX_PACK_ENTRIES:
        raise ValueError(f"calcpack 条目过多（上限 {_MAX_PACK_ENTRIES}）")

    total_bytes = 0
    for info in infos:
        validate_zip_member_name(info.filename)
        total_bytes += info.file_size
        if total_bytes > _MAX_PACK_BYTES:
            raise ValueError(f"calcpack 解压后超过 {_MAX_PACK_BYTES // (1024 * 1024)} MiB 限制")
    return infos


def load_calcpack(path: str | Path) -> dict[str, Any]:
    """加载 .calcpack 文件，返回内部文件映射 {arcname: raw_bytes}。

    Raises:
        FileNotFoundError: 文件不存在。
        ValueError: 条目越界、条目过多、解压后总大小超限或 JSON 无效。
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f".calcpack 文件未找到: {p}")
    result: dict[str, Any] = {}
    with zipfile.ZipFile(p, "r") as zf:
        for info in _validated_infos(zf):
            name = info.filename
            raw = zf.read(info)
            if name.endswith(".json"):
                result[name] = json.loads(raw.decode("utf-8"))
            else:
                result[name] = raw
    return result


def _resolve_adapter_path(root: Path, relative: Any, label: str) -> Path:
    """把适配器内的相对 JSON 路径解析为绝对路径，并阻止目录穿越。"""
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError(f"{label} 必须是非空相对路径")
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError(f"{label} 必须是相对于适配器目录的路径: {relative}")
    resolved = (root / rel).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} 路径越界: {relative}")
    if resolved.suffix.lower() != ".json":
        raise ValueError(f"{label} 必须是 .json 文件: {relative}")
    return resolved


def _read_adapter_json(path: Path, label: str) -> Any:
    """读取适配器 JSON；文件缺失时给出带字段名的错误。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"{label} 未找到: {path}") from exc


def load_adapter_dir(adapter_dir: str | Path) -> dict[str, Any]:
    """加载适配器目录，返回与 ``load_calcpack`` 相同形状的映射。

    适配器目录的 ``meta.entry_dag`` / ``meta.ui_layout`` 可指向任意相对
    JSON 路径；这里统一归一到 ``dag/formula.dag.json`` / ``ui/layout.json``，
    数据文件归一到 ``data/<stem>.json``，供查看器复用同一套渲染逻辑。

    Args:
        adapter_dir: 适配器包目录（含 ``meta.json``）。

    Returns:
        ``{内部路径: 解析后的 JSON}``。

    Raises:
        FileNotFoundError: 目录、meta、DAG、layout 或声明的数据文件缺失。
        ValueError: 路径越界、非 JSON、entry_data 类型错误或数据不是数组。
    """
    root = Path(adapter_dir).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"适配器目录未找到: {root}")

    meta_path = root / "meta.json"
    if not meta_path.is_file():
        raise FileNotFoundError(f"适配器缺少 meta.json: {root}")
    meta = _read_adapter_json(meta_path, "meta.json")
    if not isinstance(meta, dict):
        raise ValueError(f"meta.json 必须是 JSON 对象: {meta_path}")

    result: dict[str, Any] = {"meta.json": meta}

    dag_path = _resolve_adapter_path(root, meta.get("entry_dag") or "dag/formula.dag.json", "entry_dag")
    layout_path = _resolve_adapter_path(root, meta.get("ui_layout") or "ui/layout.json", "ui_layout")
    result["dag/formula.dag.json"] = _read_adapter_json(dag_path, "entry_dag")
    result["ui/layout.json"] = _read_adapter_json(layout_path, "ui_layout")

    attr_schema = meta.get("attr_schema")
    if attr_schema:
        attr_path = _resolve_adapter_path(root, attr_schema, "attr_schema")
        result["attr_schema.json"] = _read_adapter_json(attr_path, "attr_schema")

    theme_path: Path | None = None
    theme = meta.get("ui_theme")
    if theme:
        theme_path = _resolve_adapter_path(root, theme, "ui_theme")
    else:
        candidate = root / "ui" / "theme.json"
        if candidate.is_file():
            theme_path = candidate.resolve()
            if not theme_path.is_relative_to(root):
                raise ValueError(f"ui_theme 路径越界: {candidate}")
    if theme_path is not None:
        result["ui/theme.json"] = _read_adapter_json(theme_path, "ui_theme")

    entry_data = meta.get("entry_data")
    data_paths: list[Path] = []
    if entry_data is None:
        data_dir = root / "data"
        if data_dir.is_dir():
            data_paths = sorted(path for path in data_dir.glob("*.json") if path.is_file())
    elif isinstance(entry_data, list):
        data_paths = [_resolve_adapter_path(root, item, "entry_data") for item in entry_data]
    else:
        raise ValueError("meta.entry_data 必须是路径列表")

    seen: set[str] = set()
    for path in data_paths:
        key = f"data/{path.stem}.json"
        if key in seen:
            continue
        seen.add(key)
        payload = _read_adapter_json(path, "entry_data")
        if not isinstance(payload, list):
            raise ValueError(f"数据文件必须是 JSON 数组: {path}")
        result[key] = payload

    return result


def extract_assets_from_adapter_dir(adapter_dir: str | Path, target_dir: str | Path) -> dict[str, str]:
    """把适配器 ``assets/`` 复制到目标目录。

    Returns:
        ``{assets/相对路径: 复制后的完整路径}``；没有 assets 目录时返回空字典。
    """
    root = Path(adapter_dir).resolve()
    assets_dir = root / "assets"
    if not assets_dir.is_dir():
        return {}

    dest_root = Path(target_dir) / "assets"
    result: dict[str, str] = {}
    for src in sorted(assets_dir.rglob("*")):
        if src.is_symlink() or not src.is_file():
            continue
        rel = src.relative_to(assets_dir)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        result[f"assets/{rel.as_posix()}"] = str(dest)
    return result


def extract_assets_from_calcpack(pack_path: str | Path, target_dir: str | Path) -> dict[str, str]:
    """从 .calcpack 中提取 assets/ 文件到目标目录。

    Returns:
        {ZIP 内路径: 解压后完整路径} 的映射。
    """
    result: dict[str, str] = {}
    target = Path(target_dir).resolve()
    with zipfile.ZipFile(str(pack_path), "r") as zf:
        for info in _validated_infos(zf):
            name = info.filename
            if not name.startswith(_ASSETS_DIR) or name.endswith("/"):
                continue
            dest = (target / name).resolve()
            if not dest.is_relative_to(target):
                raise ValueError(f"calcpack 条目越界: {name!r}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as dst:
                dst.write(src.read())
            result[name] = str(dest)
    return result


def resolve_asset_paths_in_layout(layout_data: dict[str, Any], asset_map: dict[str, str]) -> dict[str, Any]:
    """将 layout 中的 assets/ 路径替换为解压后的实际文件路径。"""
    patched = json.loads(json.dumps(layout_data))
    sections = patched.get("sections", [])
    for sec in sections:
        if sec.get("widget_type") == "donation":
            cfg = sec.get("widget_config", {})
            raw = cfg.get("image_path", "")
            if raw in asset_map or (raw.startswith(_ASSETS_DIR) and raw in asset_map):
                cfg["image_path"] = asset_map[raw]
    return patched


def resolve_field_name(field: str) -> str:
    """将实体数据字段名映射为 DAG context 字段名。

    例如 "基础攻击力" → "基础攻击"（Endfield 命名差异）。
    通用情况下直接返回原字段名。
    """
    return _VARIABLE_FIELD_MAP.get(field, field)


def has_leveled_fields(data_files: dict[str, list[dict[str, Any]]]) -> bool:
    """判断实体数据中是否存在按等级索引的数值列表字段。

    等级输入框只用于索引数值列表；没有任何这类字段时（例如舰船/武器
    本身没有等级），显示等级输入框只会造成误导，应自动隐藏。

    Args:
        data_files: ``{数据文件名: 记录列表}``。

    Returns:
        任一记录含非空且全为数值的列表字段时返回 True。
    """
    for records in data_files.values():
        for record in records:
            for value in record.values():
                if (
                    isinstance(value, list)
                    and value
                    and all(isinstance(item, int | float) and not isinstance(item, bool) for item in value)
                ):
                    return True
    return False


def build_context_from_entity(
    entity: dict[str, Any],
    namespace: str,
    level: int = 90,
) -> dict[str, float]:
    """从实体数据构建 context 命名空间字典。

    level 为 1-indexed（1 = 最低等级）。
    """
    ctx: dict[str, float] = {}
    ignored_keys = {
        "名称",
        "技能",
        "_entity_type",
        "类型",
        "星级",
        "武器",
        "主能力",
        "副能力",
        "装备种类",
        "部位",
        "稀有度",
        "所属套组",
        "套装",
        "属性词条",
        "效果",
        "三件套效果",
        "_source",
        "等级",
        "潜能",
        "信赖",
        "信赖加成",
    }
    for key, val in entity.items():
        if key in ignored_keys:
            continue
        if isinstance(val, list) and all(isinstance(v, int | float) for v in val):
            idx = min(level, len(val)) - 1
            resolved = resolve_field_name(key)
            ctx[resolved] = float(val[idx])
        elif isinstance(val, int | float):
            resolved = resolve_field_name(key)
            ctx[resolved] = float(val)
    return ctx
