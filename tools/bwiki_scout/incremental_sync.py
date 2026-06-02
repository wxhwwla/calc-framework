#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""增量同步状态管理 — 追踪 BWIKI 缓存内容变更，只同步有差异的条目。

工作方式：
  1. 每次成功同步后，记录每条目 wikitext + html 的内容哈希到 ``sync_state.json``
  2. 下次同步前，比较当前缓存内容的哈希值
  3. 哈希不变的条目跳过（无需重新解析/反推/写入）
  4. 哈希变化 / 新增缓存 / 首次同步的条目进入同步队列
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


SYNC_STATE_FILENAME = "sync_state.json"
"""同步状态文件名，存放在输出根目录 (output_root)。"""


def _content_hash(text: str) -> str:
    """计算文本内容的 SHA256 哈希。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bundle_hash(bundle: Dict[str, Any]) -> str:
    """根据 bundle 中的 wikitext + html 计算复合哈希。"""
    wikitext = (bundle.get("wikitext") or "") + (bundle.get("html") or "")
    return _content_hash(wikitext)


def load_sync_state(output_root: Path) -> Dict[str, Any]:
    """加载同步状态文件，无文件时返回空状态。"""
    path = output_root / SYNC_STATE_FILENAME
    if not path.is_file():
        return {"version": 1, "entities": {}}
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def save_sync_state(output_root: Path, state: Dict[str, Any]) -> None:
    """保存同步状态文件。"""
    path = output_root / SYNC_STATE_FILENAME
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_entity_hash(state: Dict[str, Any], name: str) -> Optional[str]:
    """获取指定条目的已记录哈希，无记录则返回 None。"""
    return (state.get("entities") or {}).get(name)


def record_entity_sync(state: Dict[str, Any], name: str, bundle: Dict[str, Any]) -> None:
    """记录一次同步后的内容哈希。"""
    entities = state.setdefault("entities", {})
    entities[name] = _bundle_hash(bundle)


def record_entity_sync_batch(
    state: Dict[str, Any],
    updates: Dict[str, Dict[str, Any]],
) -> None:
    """批量记录同步后的哈希值。

    Args:
        state: 同步状态字典（会被原地修改）
        updates: {名称: bundle_dict} 映射
    """
    for name, bundle in updates.items():
        record_entity_sync(state, name, bundle)


def content_changed(state: Dict[str, Any], name: str, bundle: Dict[str, Any]) -> bool:
    """检查条目内容是否自上次同步后发生了变化。

    如果是首次同步（无历史记录），返回 True（需要同步）。

    Args:
        state: 同步状态字典
        name: 条目名称
        bundle: 当前缓存数据 bundle

    Returns:
        True = 内容变化或首次同步，需要处理
        False = 内容未变，可跳过
    """
    old_hash = get_entity_hash(state, name)
    if old_hash is None:
        return True
    new_hash = _bundle_hash(bundle)
    return old_hash != new_hash


def remove_entity(state: Dict[str, Any], name: str) -> None:
    """从同步状态中删除条目记录（本地已删但状态中残留时清理）。"""
    entities = state.get("entities")
    if entities and name in entities:
        del entities[name]


def cleanup_stale_entities(state: Dict[str, Any], known_names: set[str]) -> int:
    """清理状态中已不存在的条目记录（本地数据删除后清除状态）。"""
    entities = state.get("entities", {})
    stale = [name for name in entities if name not in known_names]
    for name in stale:
        del entities[name]
    return len(stale)


def get_stale_entities_from_cache(
    raw_dir: Path,
    manifest_titles: list[str],
    kind: str,
    *,
    local_names: set[str],
    output_root: Optional[Path] = None,
    include_new: bool = False,
) -> list[str]:
    """从缓存目录扫描出需要（重新）同步的条目。

    判断规则：
    - 首次同步（无历史记录）→ 需要
    - 缓存内容哈希变化 → 需要
    - 缓存内容未变 → 跳过

    Args:
        raw_dir: 缓存根目录 (output/raw)
        manifest_titles: manifest 中某类的 Wiki 标题列表
        kind: 实体类型 ("operator" / "weapon")
        local_names: 本地已有的实体名称集合
        output_root: 输出根目录（用于读取 sync_state.json）
        include_new: 是否包含本地尚无、但缓存齐全的新条目

    Returns:
        需要同步的条目名称列表
    """
    if output_root is None:
        output_root = raw_dir.parent

    state = load_sync_state(output_root)
    from bwiki_scout.storage import load_page_bundle
    from bwiki_scout.import_targets import (
        filter_operator_titles,
        operator_wiki_cache_ready,
        weapon_wiki_import_ready,
    )

    candidates: set[str] = set(local_names)

    if include_new:
        if kind == "operator":
            for title in filter_operator_titles(manifest_titles):
                if title not in candidates and operator_wiki_cache_ready(raw_dir, title):
                    candidates.add(title)
        elif kind == "weapon":
            for title in manifest_titles:
                if title not in candidates and weapon_wiki_import_ready(raw_dir, title):
                    candidates.add(title)

    stale: list[str] = []
    for name in sorted(candidates):
        bundle = load_page_bundle(raw_dir, name)
        if bundle is None:
            continue
        if content_changed(state, name, bundle):
            stale.append(name)

    return stale
