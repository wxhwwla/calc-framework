# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""出站 HTTP 安全封装 — SSRF 校验与固定路径重建。

防止 DNS 重绑定攻击：在验证阶段一次性解析域名并绑定 IP，
``httpx.AsyncClient`` 不再重复 DNS 解析，消除 TOCTOU 窗口。
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)

_LOCAL_HOSTNAMES = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0", "::"})

_ALLOWED_PATH_PREFIXES = frozenset({"", "/v1"})


@dataclass(frozen=True, slots=True)
class ValidatedOutboundHost:
    """已通过 SSRF 校验的出站主机（scheme + hostname + 已解析 IP + 固定路径前缀）。

    解析后的 IP 地址在验证阶段固定下来，后续请求直接连接该 IP，
    避免 HTTP 客户端重复 DNS 解析导致的 TOCTOU 风险。
    """

    scheme: str
    hostname: str
    resolved_ip: str
    path_prefix: str = ""

    def chat_completions_url(self) -> str:
        """重建 OpenAI 兼容 chat/completions URL。"""
        prefix = self.path_prefix.rstrip("/")
        return f"{self.scheme}://{self.hostname}{prefix}/chat/completions"


def _resolve_hostname(hostname: str) -> str:
    """解析域名到 IP 地址，拒绝内网/回环地址。

    Returns:
        第一个解析到的公网 IPv4 或 IPv6 地址

    Raises:
        HTTPException: 指向内网或无法解析
    """
    try:
        addrs = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HTTPException(
            status_code=400,
            detail=f"无法解析域名 {hostname}，请检查 API 地址是否正确",
        ) from exc

    first_public: str | None = None
    for addr in addrs:
        ip_str = cast(str, addr[4][0])
        ip = ipaddress.ip_address(ip_str)
        for net in _PRIVATE_NETWORKS:
            if ip in net:
                raise HTTPException(
                    status_code=400,
                    detail=f"域名 {hostname} 解析到内网地址 {ip_str}，已阻止",
                )
        if first_public is None:
            first_public = ip_str

    if first_public is None:
        raise HTTPException(status_code=400, detail=f"无法解析域名 {hostname}")

    return first_public


def validate_outbound_api_base(api_base: str) -> ValidatedOutboundHost:
    """校验用户配置的 API Base URL，返回脱敏后的出站主机描述。

    在校验阶段完成 DNS 解析并将 IP 地址固定到返回对象中，
    后续 ``post_chat_completions`` 直接使用该 IP 发起请求，
    避免两次 DNS 解析带来的 TOCTOU 风险。

    Raises:
        HTTPException: 协议非法、内网地址、DNS 指向私有网段。
    """
    parsed = urlparse(api_base.strip().rstrip("/"))
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的协议: {parsed.scheme}，仅允许 http/https",
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise HTTPException(status_code=400, detail="API 地址缺少主机名")

    path_prefix = parsed.path.rstrip("/") or ""
    if path_prefix not in _ALLOWED_PATH_PREFIXES:
        raise HTTPException(
            status_code=400,
            detail="API Base 路径仅支持空或 /v1（OpenAI 兼容）",
        )

    if hostname in _LOCAL_HOSTNAMES:
        raise HTTPException(status_code=400, detail=f"禁止访问内部地址: {hostname}")

    resolved_ip = _resolve_hostname(hostname)

    return ValidatedOutboundHost(
        scheme=parsed.scheme,
        hostname=hostname,
        resolved_ip=resolved_ip,
        path_prefix=path_prefix,
    )


async def post_chat_completions(
    api_base: str,
    *,
    json_body: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> httpx.Response:
    """向已校验主机发送 chat/completions 请求（SSRF 安全入口）。

    使用验证阶段固定的 IP 地址发起连接，并设置 ``Host`` 头
    以支持虚拟主机，避免 HTTP 客户端重复 DNS 解析。
    """
    host = validate_outbound_api_base(api_base)
    target_url = host.chat_completions_url()

    # 使用已解析的 IP 替换 URL 中的主机名，并添加 Host 头
    # 这样 httpx 不会再次 DNS 解析
    mapped_url = target_url.replace(f"://{host.hostname}", f"://{host.resolved_ip}", 1)
    extra_headers = dict(headers)
    extra_headers.setdefault("Host", host.hostname)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        return await client.post(mapped_url, json=json_body, headers=extra_headers)


__all__ = [
    "ValidatedOutboundHost",
    "post_chat_completions",
    "validate_outbound_api_base",
]
