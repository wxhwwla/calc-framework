# SPDX-License-Identifier: AGPL-3.0
"""按适配器 ID 加载 layout / DAG / 导出用 data_files（配置包设计器 Web 版）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parents[3]
ADAPTER_ROOT = REPO_ROOT / "framework" / "adapters"
ENDFIELD_GAME_DATA = REPO_ROOT / "games" / "endfield" / "data"
ARKNIGHTS_OPERATORS_JSON = (
    REPO_ROOT / "tools" / "arknights_scout" / "output" / "parsed" / "operators.json"
)


def _adapter_path(adapter_id: str) -> Path:
    path = ADAPTER_ROOT / adapter_id
    if not (path / "meta.json").is_file():
        raise HTTPException(status_code=404, detail=f"adapter not found: {adapter_id}")
    return path


def _read_json(path: Path) -> Any:
    """读取并解析 JSON 文件。"""
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"file not found: {path.name}")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {path.name}: {e}") from e


def load_adapter_meta(adapter_id: str) -> dict[str, Any]:
    return _read_json(_adapter_path(adapter_id) / "meta.json")


def resolve_dag_path(adapter_id: str) -> Path:
    adapter_dir = _adapter_path(adapter_id)
    meta = load_adapter_meta(adapter_id)
    entry = meta.get("entry_dag", "dag/formula.dag.json")
    candidates = [
        (adapter_dir / entry).resolve(),
        adapter_dir / entry,
        adapter_dir / "dag" / "formula.dag.json",
        adapter_dir / "dag" / f"{adapter_id}_full.dag.json",
        adapter_dir / f"{adapter_id}.dag.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise HTTPException(status_code=404, detail=f"DAG not found for adapter: {adapter_id}")


def resolve_layout_path(adapter_id: str) -> Path:
    adapter_dir = _adapter_path(adapter_id)
    meta = load_adapter_meta(adapter_id)
    layout_rel = meta.get("ui_layout", "ui/layout.json")
    path = adapter_dir / layout_rel
    if not path.is_file():
        path = adapter_dir / "ui" / "layout.json"
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"layout not found for adapter: {adapter_id}")
    return path


def get_adapter_layout(adapter_id: str) -> dict[str, Any]:
    data = _read_json(resolve_layout_path(adapter_id))
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="layout root must be object")
    return data


def get_adapter_dag(adapter_id: str) -> dict[str, Any]:
    data = _read_json(resolve_dag_path(adapter_id))
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="DAG root must be object")
    return data


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    """加载 JSON 文件并验证根节点为数组。"""
    data = _read_json(path)
    if not isinstance(data, list):
        raise HTTPException(status_code=500, detail=f"{path.name} root must be array")
    return data


def data_entity_summary(adapter_id: str) -> list[dict[str, Any]]:
    """各实体类型条数与是否只读（Web 录入）。"""
    if adapter_id == "endfield":
        entities: list[dict[str, Any]] = []
        mapping = (
            ("characters", "角色", ENDFIELD_GAME_DATA / "characters.json"),
            ("weapons", "武器", ENDFIELD_GAME_DATA / "weapons.json"),
            ("equipments", "装备", ENDFIELD_GAME_DATA / "equipments.json"),
        )
        for key, label, path in mapping:
            count = len(_load_json_list(path)) if path.is_file() else 0
            entities.append({"key": key, "label": label, "count": count, "read_only": False})
        return entities

    if adapter_id == "arknights":
        count = 0
        if ARKNIGHTS_OPERATORS_JSON.is_file():
            count = len(_load_json_list(ARKNIGHTS_OPERATORS_JSON))
        return [{"key": "operators", "label": "干员", "count": count, "read_only": False}]

    return []


def get_data_files_for_export(adapter_id: str) -> dict[str, list[dict[str, Any]]]:
    """导出 .calcpack 时写入的 data_files。"""
    result: dict[str, list[dict[str, Any]]] = {}
    for ent in data_entity_summary(adapter_id):
        key = ent["key"]
        if adapter_id == "endfield":
            paths = {
                "characters": ENDFIELD_GAME_DATA / "characters.json",
                "weapons": ENDFIELD_GAME_DATA / "weapons.json",
                "equipments": ENDFIELD_GAME_DATA / "equipments.json",
            }
            path = paths.get(key)
            if path and path.is_file():
                result[key] = _load_json_list(path)
        elif adapter_id == "arknights" and key == "operators":
            if ARKNIGHTS_OPERATORS_JSON.is_file():
                result[key] = _load_json_list(ARKNIGHTS_OPERATORS_JSON)
    return result


def get_pack_export_bundle(adapter_id: str) -> dict[str, Any]:
    """获取适配器完整打包导出内容（meta + layout + DAG + data_files）。"""
    meta = load_adapter_meta(adapter_id)
    meta = dict(meta)
    meta["entry_dag"] = "dag/formula.dag.json"
    meta.setdefault("ui_layout", "ui/layout.json")
    meta.setdefault("ui_theme", "ui/theme.json")
    data_files = get_data_files_for_export(adapter_id)
    if data_files:
        meta["entry_data"] = [f"data/{k}.json" for k in data_files]
    return {
        "adapter_id": adapter_id,
        "meta": meta,
        "layout": get_adapter_layout(adapter_id),
        "dag": get_adapter_dag(adapter_id),
        "data_files": data_files,
        "data_summary": {k: len(v) for k, v in data_files.items()},
    }
