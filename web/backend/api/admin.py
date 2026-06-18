# SPDX-License-Identifier: AGPL-3.0
"""SaaS 管理 API — API Key 管理 + 速率限制 + 用量统计。"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.internal.auth import verify_admin_token
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(verify_admin_token)],
)

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


async def _load_json_async(path: Path) -> dict:
    return await asyncio.to_thread(_load_json, path)


async def _save_json_async(path: Path, data: dict) -> None:
    await asyncio.to_thread(_save_json, path, data)


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

# 生产环境**必须**设置 CALC_API_KEY_PEPPER（≥32 字符随机串）
_API_KEY_PEPPER_ENV = "CALC_API_KEY_PEPPER"
# 不再提供硬编码回退 — 缺少环境变量时启动即失败


def _api_key_pepper() -> bytes:
    """读取 API Key 哈希用 pepper。

    Raises:
        RuntimeError: ``CALC_API_KEY_PEPPER`` 环境变量未设置。
    """
    raw = os.environ.get(_API_KEY_PEPPER_ENV, "").strip()
    if not raw:
        raise RuntimeError(
            f"安全配置缺失：环境变量 {_API_KEY_PEPPER_ENV} 未设置。\n"
            f"请设置一个 ≥32 字符的随机字符串作为 API Key 哈希盐值。\n"
            f"示例（PowerShell）：\n"
            f"  $env:{_API_KEY_PEPPER_ENV} = '$(openssl rand -base64 32)'\n"
            f"  或使用任意 ≥32 字符的随机字符串。"
        )
    return raw.encode("utf-8")


def _hash_key(api_key: str) -> str:
    """使用 scrypt 哈希 API Key（敏感凭据，非快速摘要算法）。"""
    return hashlib.scrypt(
        api_key.encode("utf-8"),
        salt=_api_key_pepper(),
        n=2**14,
        r=8,
        p=1,
        maxmem=0,
        dklen=64,
    ).hex()


@router.post("/keys", response_model=CreateKeyResponse)
async def create_api_key(req: CreateKeyRequest):
    """创建新的 API Key（仅创建时返回完整 key，请妥善保存）。"""
    api_key = "cf_" + secrets.token_urlsafe(32)
    key_hash = _hash_key(api_key)

    keys = await _load_json_async(_KEYS_FILE)
    keys[key_hash] = {
        "key_prefix": api_key[:12],
        "name": req.name or f"Key-{len(keys) + 1}",
        "tier": req.tier if req.tier in _TIER_RATE_LIMITS else "free",
        "rate_limit": _TIER_RATE_LIMITS.get(req.tier, 30),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": "",
        "enabled": True,
    }
    await _save_json_async(_KEYS_FILE, keys)

    return CreateKeyResponse(
        api_key=api_key,
        key_prefix=api_key[:12],
        name=keys[key_hash]["name"],
        tier=keys[key_hash]["tier"],
    )


@router.get("/keys", response_model=list[ApiKeyInfo])
async def list_api_keys():
    """列出所有 API Keys（不返回完整 key）。"""
    keys = await _load_json_async(_KEYS_FILE)
    return [ApiKeyInfo(**v) for v in keys.values()]


@router.delete("/keys/{key_prefix}")
async def revoke_api_key(key_prefix: str):
    """吊销指定 API Key。"""
    keys = await _load_json_async(_KEYS_FILE)
    to_delete = [h for h, v in keys.items() if v.get("key_prefix") == key_prefix]
    for h in to_delete:
        del keys[h]
    await _save_json_async(_KEYS_FILE, keys)
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
    keys = await _load_json_async(_KEYS_FILE)
    usage = await _load_json_async(_USAGE_FILE)

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

    注意：usage/key 持久化通过 ``asyncio.to_thread`` 执行同步 I/O；
    滑动窗口在进程内存中，**仅对当前 worker 有效**。

    部署说明：``docs/Web后端限速与多Worker.md``
    - 单 worker（推荐）：默认行为
    - 多 worker：设置 ``CALC_DISABLE_RATE_LIMIT=1`` 并在 nginx 等层限速

    测试时可通过 ``RateLimitMiddleware.enabled = False`` 全局禁用。
    """

    enabled: bool = True
    _window: dict[str, list[float]] = defaultdict(list)
    _window_size = 60  # 秒

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        if not self.enabled:
            return await call_next(request)
        # 跳过文档端点；/api/admin 已受 Token 保护且纳入限速统计
        path = request.url.path
        if path.startswith("/api/docs") or path.startswith("/api/redoc"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key", "")
        client_id = "anonymous"

        rate_limit = 20  # 默认

        if api_key:
            key_hash = _hash_key(api_key)
            keys = await _load_json_async(_KEYS_FILE)
            key_data = keys.get(key_hash)
            if key_data and key_data.get("enabled", True):
                client_id = f"key:{key_data['key_prefix']}"
                rate_limit = key_data.get("rate_limit", 30)
                # 更新 last_used
                key_data["last_used"] = datetime.now(timezone.utc).isoformat()
                await _save_json_async(_KEYS_FILE, keys)

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
        await self._record_usage_async(path)

        return await call_next(request)

    @staticmethod
    async def _record_usage_async(path: str) -> None:
        usage = await _load_json_async(_USAGE_FILE)
        timestamps = usage.get("request_timestamps", [])
        timestamps.append(time.time())
        # 只保留最近 1 小时
        now = time.time()
        usage["request_timestamps"] = [t for t in timestamps if now - t < 3600]

        by_endpoint = usage.get("by_endpoint", {})
        endpoint = path.split("?")[0]
        by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1
        usage["by_endpoint"] = by_endpoint

        await _save_json_async(_USAGE_FILE, usage)


__all__: list[str] = []
