# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""插件管理 API — 列出/安装/卸载插件。"""

from __future__ import annotations

from typing import Annotated

from api.internal.auth import verify_admin_token
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


class PluginInfo(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "framework"
    type: str = "builtin"
    installed: bool = True
    tags: list[str] = Field(default_factory=list)


def _ensure_registry_loaded():
    """触发内置插件注册（首次调用时导入 builtin 模块）。"""
    try:
        import calc_framework.plugin.builtin  # noqa: F401 — 触发 register()  # type: ignore[unused-import]
    except ImportError:
        pass


def _list_from_registry() -> list[dict]:
    """从真实插件注册表获取已安装插件列表。"""
    _ensure_registry_loaded()
    try:
        from calc_framework.plugin.registry import get_registry

        reg = get_registry()
        plugins: list[dict] = []
        for name in reg.list():
            p = reg.get(name)
            if p:
                meta = p.meta
                plugins.append(
                    {
                        "name": meta.name,
                        "version": meta.version,
                        "description": meta.description,
                        "author": meta.author or "framework",
                        "type": "builtin",
                        "installed": True,
                        "tags": ["内置"],
                    }
                )
        return plugins
    except ImportError:
        return []


@router.get("", response_model=list[PluginInfo])
async def list_plugins():
    """列出所有已安装插件（从注册表）。"""
    return [PluginInfo(**p) for p in _list_from_registry()]


@router.post("/install")
async def install_plugin(plugin_name: str = ""):
    """安装插件（暂不支持在线安装，仅返回提示）。"""
    if not plugin_name:
        raise HTTPException(status_code=400, detail="需要提供 plugin_name 参数")
    return {
        "status": "not_implemented",
        "name": plugin_name,
        "message": ("在线安装暂未开放，请手动将 .calcplugin 文件放入 framework/adapters/"),
    }


@router.delete("/{plugin_name}")
async def uninstall_plugin(plugin_name: str, _admin: Annotated[None, Depends(verify_admin_token)] = None):
    """卸载插件（仅限非内置插件）。需要管理 Token。"""
    try:
        from calc_framework.plugin.registry import get_registry

        reg = get_registry()
        p = reg.get(plugin_name)
        if p is None:
            raise HTTPException(status_code=404, detail=f"插件 '{plugin_name}' 未安装")
        if p.meta.author == "framework":
            raise HTTPException(status_code=400, detail="内置插件不可卸载")
        reg.unregister(plugin_name)
        return {"status": "uninstalled", "name": plugin_name}
    except ImportError:
        raise HTTPException(status_code=503, detail="插件系统不可用")


__all__: list[str] = []
