# SPDX-License-Identifier: AGPL-3.0
"""Calc Hub 存储层：SQLite 存储包元数据 + 文件系统存储包文件。"""

from __future__ import annotations

import io
import json
import shutil
import sqlite3
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class HubPack:
    """Calc Hub 配置包元数据。"""

    id: str
    name: str
    version: str
    description: str
    author: str
    tags: list[str] = field(default_factory=list)
    rating: float = 0.0
    rating_count: int = 0
    download_count: int = 0
    file_size: int = 0
    screenshot_urls: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


_HUB_DIR = Path(__file__).resolve().parent.parent / "data" / "hub"
_PACKS_DIR = _HUB_DIR / "packs"
_DB_PATH = _HUB_DIR / "catalog.db"


def _ensure_db() -> sqlite3.Connection:
    """获取 SQLite 连接，确保数据库和表已创建。"""
    _PACKS_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS packs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            author TEXT NOT NULL DEFAULT '',
            tags TEXT NOT NULL DEFAULT '[]',
            rating REAL NOT NULL DEFAULT 0.0,
            rating_count INTEGER NOT NULL DEFAULT 0,
            download_count INTEGER NOT NULL DEFAULT 0,
            file_size INTEGER NOT NULL DEFAULT 0,
            screenshot_urls TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id TEXT NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
            comment TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (pack_id) REFERENCES packs(id)
        )
    """)
    conn.commit()
    return conn


def list_packs(
    *,
    search: str = "",
    tag: str = "",
    sort: str = "updated_at",
    order: str = "desc",
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    conn = _ensure_db()
    conditions: list[str] = []
    params: list[Any] = []

    if search:
        conditions.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if tag:
        conditions.append("tags LIKE ?")
        params.append(f"%{tag}%")

    where = " AND ".join(conditions) if conditions else "1=1"
    allowed_sorts = {"name", "version", "rating", "download_count", "created_at", "updated_at"}
    sort_col = sort if sort in allowed_sorts else "updated_at"
    sort_dir = "DESC" if order == "desc" else "ASC"

    count_row = conn.execute(f"SELECT COUNT(*) FROM packs WHERE {where}", params).fetchone()
    total = count_row[0] if count_row else 0

    rows = conn.execute(
        f"SELECT * FROM packs WHERE {where} ORDER BY {sort_col} {sort_dir} LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()

    packs = [_row_to_dict(r) for r in rows]
    conn.close()
    return packs, total


def get_pack(pack_id: str) -> dict[str, Any] | None:
    conn = _ensure_db()
    row = conn.execute("SELECT * FROM packs WHERE id = ?", [pack_id]).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def create_pack(
    name: str,
    version: str,
    description: str,
    author: str,
    *,
    tags: list[str] | None = None,
    file_size: int = 0,
) -> HubPack:
    """创建新配置包元数据记录。

    参数:
        name: 包名。
        version: 版本号。
        description: 描述。
        author: 作者。
        tags: 标签列表。
        file_size: 包文件大小（字节）。

    返回:
        创建的 HubPack 实例。
    """
    conn = _ensure_db()
    now = datetime.now(timezone.utc).isoformat()
    pack_id = uuid4().hex[:12]
    pack = HubPack(
        id=pack_id,
        name=name,
        version=version,
        description=description,
        author=author,
        tags=tags or [],
        created_at=now,
        updated_at=now,
        file_size=file_size,
    )
    conn.execute(
        "INSERT INTO packs (id, name, version, description, author, tags, file_size, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [pack.id, pack.name, pack.version, pack.description, pack.author,
         json.dumps(pack.tags), pack.file_size, pack.created_at, pack.updated_at],
    )
    conn.commit()
    conn.close()
    return pack


def update_pack(pack_id: str, **kwargs: Any) -> dict[str, Any] | None:
    conn = _ensure_db()
    now = datetime.now(timezone.utc).isoformat()
    fields = {k: v for k, v in kwargs.items() if k in {
        "name", "version", "description", "author", "tags", "file_size",
    }}
    if not fields:
        conn.close()
        return get_pack(pack_id)

    fields["updated_at"] = now
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    params = [json.dumps(v) if isinstance(v, list) else v for v in fields.values()]
    params.append(pack_id)
    conn.execute(f"UPDATE packs SET {set_clause} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return get_pack(pack_id)


def rate_pack(pack_id: str, score: int, comment: str = "") -> dict[str, Any] | None:
    """为配置包评分，自动更新平均分和评分次数。

    参数:
        pack_id: 包 ID。
        score: 评分（1~5）。
        comment: 评论文本。

    返回:
        更新后的包字典。
    """
    conn = _ensure_db()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO ratings (pack_id, score, comment, created_at) VALUES (?, ?, ?, ?)",
        [pack_id, score, comment, now],
    )
    stats = conn.execute(
        "SELECT AVG(score) as avg, COUNT(*) as cnt FROM ratings WHERE pack_id = ?",
        [pack_id],
    ).fetchone()
    if stats and stats["cnt"] > 0:
        avg = round(stats["avg"], 2)
        conn.execute(
            "UPDATE packs SET rating = ?, rating_count = ?, updated_at = ? WHERE id = ?",
            [avg, stats["cnt"], now, pack_id],
        )
    conn.commit()
    conn.close()
    return get_pack(pack_id)


def increment_download(pack_id: str) -> dict[str, Any] | None:
    conn = _ensure_db()
    conn.execute(
        "UPDATE packs SET download_count = download_count + 1 WHERE id = ?",
        [pack_id],
    )
    conn.commit()
    conn.close()
    return get_pack(pack_id)


def delete_pack(pack_id: str) -> bool:
    conn = _ensure_db()
    cursor = conn.execute("DELETE FROM packs WHERE id = ?", [pack_id])
    deleted = cursor.rowcount > 0
    conn.execute("DELETE FROM ratings WHERE pack_id = ?", [pack_id])
    conn.commit()
    conn.close()
    if deleted:
        pack_dir = _PACKS_DIR / pack_id
        if pack_dir.exists():
            shutil.rmtree(pack_dir)
    return deleted


def save_pack_file(pack_id: str, content: bytes, filename: str) -> Path:
    """将配置包文件保存到磁盘。

    返回:
        保存后的文件路径。
    """
    pack_dir = _PACKS_DIR / pack_id
    pack_dir.mkdir(parents=True, exist_ok=True)
    file_path = pack_dir / filename
    file_path.write_bytes(content)
    return file_path


def get_pack_file_path(pack_id: str, filename: str) -> Path | None:
    file_path = _PACKS_DIR / pack_id / filename
    if file_path.exists():
        return file_path
    return None


def validate_calcpack_archive(content: bytes) -> tuple[bool, str, dict[str, Any]]:
    """校验 .calcpack 最小结构（meta + DAG + layout）。"""
    if not content:
        return False, "文件为空", {}
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = set(zf.namelist())
            required = ("meta.json", "dag/formula.dag.json", "ui/layout.json")
            missing = [name for name in required if name not in names]
            if missing:
                return False, f"缺少必需文件: {', '.join(missing)}", {}
            meta = json.loads(zf.read("meta.json").decode("utf-8"))
            if not isinstance(meta, dict):
                return False, "meta.json 格式无效", {}
            return True, "", meta
    except zipfile.BadZipFile:
        return False, "不是有效的 ZIP / .calcpack 文件", {}
    except json.JSONDecodeError:
        return False, "meta.json 不是合法 JSON", {}
    except Exception as exc:
        return False, str(exc), {}


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """将 SQLite Row 转为普通字典，自动反序列化 JSON 字段。"""
    d = dict(row)
    for key in ("tags", "screenshot_urls"):
        if isinstance(d.get(key), str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                d[key] = []
    return d
