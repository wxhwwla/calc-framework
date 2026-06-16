# SPDX-License-Identifier: AGPL-3.0
"""SaaS 管理 API — API Key 管理 + 速率限制 + 用量统计。"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ── 持久化路径 ────────────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent / ".admin_data"
_KEYS_FILE = _DATA_DIR / "api_keys.json"
_USAGE_FILE = _DATA_DIR / "usage.json"


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict:
    _ensure_data_dir()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save_json(path: Path, data: dict) -> None:
    _ensure_data_dir()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── API Key 管理 ──────────────────────────────────────


class ApiKeyInfo(BaseModel):
    """API Key 信息（不包含完整 key）。"""

    key_prefix: str
    """Key 前缀（前 8 位）。"""
    name: str = ""
    tier: str = "free"
    rate_limit: int = Field(default=60, description="每分钟请求数")
    created_at: str = ""
    last_used: str = ""
    enabled: bool = True


class CreateKeyRequest(BaseModel):
    """创建 API Key 请求。"""

    name: str = Field(default="", description="密钥备注名")
    tier: str = Field(default="free", description="套餐: free/pro/enterprise")


class CreateKeyResponse(BaseModel):
    """创建 API Key 响应（仅创建时返回完整 key）。"""

    api_key: str
    key_prefix: str
    name: str
    tier: str


_TIER_RATE_LIMITS = {"free": 30, "pro": 300, "enterprise": 3000}


def _hash_key(api_key: str) -> str:
    """对 API Key 做加盐哈希（防止彩虹表），salt 从 key 自身派生。"""
    salt = hashlib.sha3_256(api_key[:16].encode()).digest()
    return hashlib.sha3_256(salt + api_key.encode()).hexdigest()


@router.post("/keys", response_model=CreateKeyResponse)
async def create_api_key(req: CreateKeyRequest):
    """创建新的 API Key（仅创建时返回完整 key，请妥善保存）。"""
    api_key = "cf_" + secrets.token_urlsafe(32)
    key_hash = _hash_key(api_key)

    keys = _load_json(_KEYS_FILE)
    keys[key_hash] = {
        "key_prefix": api_key[:12],
        "name": req.name or f"Key-{len(keys) + 1}",
        "tier": req.tier if req.tier in _TIER_RATE_LIMITS else "free",
        "rate_limit": _TIER_RATE_LIMITS.get(req.tier, 30),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": "",
        "enabled": True,
    }
    _save_json(_KEYS_FILE, keys)

    return CreateKeyResponse(
        api_key=api_key,
        key_prefix=api_key[:12],
        name=keys[key_hash]["name"],
        tier=keys[key_hash]["tier"],
    )


@router.get("/keys", response_model=list[ApiKeyInfo])
async def list_api_keys():
    """列出所有 API Keys（不返回完整 key）。"""
    keys = _load_json(_KEYS_FILE)
    return [ApiKeyInfo(**v) for v in keys.values()]


@router.delete("/keys/{key_prefix}")
async def revoke_api_key(key_prefix: str):
    """吊销指定 API Key。"""
    keys = _load_json(_KEYS_FILE)
    to_delete = [h for h, v in keys.items() if v.get("key_prefix") == key_prefix]
    for h in to_delete:
        del keys[h]
    _save_json(_KEYS_FILE, keys)
    return {"status": "revoked", "count": len(to_delete)}


# ── 用量统计 ──────────────────────────────────────────


class UsageStats(BaseModel):
    total_requests: int = 0
    active_keys: int = 0
    by_tier: dict[str, int] = Field(default_factory=dict)
    by_endpoint: dict[str, int] = Field(default_factory=dict)
    recent_rpm: float = 0.0  # 最近一分钟请求数


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats():
    """获取用量统计概览。"""
    keys = _load_json(_KEYS_FILE)
    usage = _load_json(_USAGE_FILE)

    active = sum(1 for v in keys.values() if v.get("enabled", True))
    by_tier: dict[str, int] = defaultdict(int)
    for v in keys.values():
        by_tier[v.get("tier", "free")] += 1

    # 最近一分钟请求
    now = time.time()
    recent_requests = [ts for ts in usage.get("request_timestamps", []) if now - ts < 60]

    return UsageStats(
        total_requests=len(usage.get("request_timestamps", [])),
        active_keys=active,
        by_tier=dict(by_tier),
        by_endpoint=usage.get("by_endpoint", {}),
        recent_rpm=len(recent_requests),
    )


# ── 速率限制中间件 ────────────────────────────────────


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的内存速率限制中间件。

    读取 ``X-API-Key`` header：
    - 有效 key：按 tier 限速
    - 无效或无 key：默认 20 req/min（宽松，方便开发）

    注意：当前使用同步文件 I/O 存储 usage/key 数据。
    适用于单 worker 部署；多 worker 场景建议替换为 Redis 等外部存储。

    测试时可通过 ``RateLimitMiddleware.enabled = False`` 全局禁用。
    """

    enabled: bool = True
    _window: dict[str, list[float]] = defaultdict(list)
    _window_size = 60  # 秒

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if not self.enabled:
            return await call_next(request)
        # 跳过管理端点自身和静态文件
        path = request.url.path
        if path.startswith("/api/admin") or path.startswith("/api/docs") or path.startswith("/api/redoc"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        client_id = "anonymous"

        rate_limit = 20  # 默认

        if api_key:
            key_hash = _hash_key(api_key)
            keys = _load_json(_KEYS_FILE)
            key_data = keys.get(key_hash)
            if key_data and key_data.get("enabled", True):
                client_id = f"key:{key_data['key_prefix']}"
                rate_limit = key_data.get("rate_limit", 30)
                # 更新 last_used
                key_data["last_used"] = datetime.now(timezone.utc).isoformat()
                _save_json(_KEYS_FILE, keys)

        # 滑动窗口检查
        now = time.time()
        window = self._window[client_id]
        window[:] = [t for t in window if now - t < self._window_size]

        if len(window) >= rate_limit:
            return JSONResponse(
                status_code=429,
                content={"detail": f"请求过于频繁，当前限制 {rate_limit} 次/分钟"},
                headers={"Retry-After": str(self._window_size)},
            )

        window.append(now)

        # 记录用量
        self._record_usage(path)

        return await call_next(request)

    @staticmethod
    def _record_usage(path: str) -> None:
        usage = _load_json(_USAGE_FILE)
        timestamps = usage.get("request_timestamps", [])
        timestamps.append(time.time())
        # 只保留最近 1 小时
        now = time.time()
        usage["request_timestamps"] = [t for t in timestamps if now - t < 3600]

        by_endpoint = usage.get("by_endpoint", {})
        endpoint = path.split("?")[0]
        by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1
        usage["by_endpoint"] = by_endpoint

        _save_json(_USAGE_FILE, usage)


__all__: list[str] = []
