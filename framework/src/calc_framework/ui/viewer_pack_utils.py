# SPDX-License-Identifier: AGPL-3.0
".calcpack I/O 工具 — 加载/解压/资源提取 + 实体 context 构建。"

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

_VARIABLE_FIELD_MAP: dict[str, str] = {
    "基础攻击力": "基础攻击",
}

_SOURCE_TO_DATA_FILE: dict[str, str] = {
    "character": "characters",
    "weapon": "weapons",
    "equipment": "equipments",
}

_DATA_FILE_TO_SOURCE: dict[str, str] = {
    "characters": "character",
    "weapons": "weapon",
    "equipments": "equipment",
}

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


def load_calcpack(path: str | Path) -> dict[str, Any]:
    """加载 .calcpack 文件，返回内部文件映射 {arcname: raw_bytes}。"""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f".calcpack 文件未找到: {p}")
    result: dict[str, Any] = {}
    with zipfile.ZipFile(p, "r") as zf:
        for name in zf.namelist():
            raw = zf.read(name)
            if name.endswith(".json"):
                result[name] = json.loads(raw.decode("utf-8"))
            else:
                result[name] = raw
    return result


def extract_assets_from_calcpack(pack_path: str | Path, target_dir: str | Path) -> dict[str, str]:
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


def build_context_from_entity(
    entity: dict[str, Any],
    namespace: str,
    level: int = 90,
) -> dict[str, float]:
    """从实体数据构建 context 命名空间字典。

    level 为 1-indexed（1 = 最低等级）。
    """
    ctx: dict[str, float] = {}
    IGNORED_KEYS = {"名称", "技能", "_entity_type", "类型", "星级", "武器",
                    "主能力", "副能力", "装备种类", "部位", "稀有度",
                    "所属套组", "套装", "属性词条", "效果", "三件套效果", "_source",
                    "等级", "潜能", "信赖", "信赖加成"}
    for key, val in entity.items():
        if key in IGNORED_KEYS:
            continue
        if isinstance(val, list) and all(isinstance(v, (int, float)) for v in val):
            idx = min(level, len(val)) - 1
            resolved = resolve_field_name(key)
            ctx[resolved] = float(val[idx])
        elif isinstance(val, (int, float)):
            resolved = resolve_field_name(key)
            ctx[resolved] = float(val)
    return ctx
