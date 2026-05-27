#!/usr/bin/env python3
"""
路径工具模块

提供统一的路径处理功能，支持两种运行模式：
1. 开发模式：从源码运行（获取项目根目录）
2. 打包模式：从发布文件夹内的 EXE 运行（读取 EXE **同级**目录下的 JSON；
   兼容 PyInstaller onedir 的 ``_internal/`` 回退，但正式发布包应将数据放在 exe 旁）

主要功能：
1. 获取资源文件的完整路径
2. 支持开发和打包两种环境

依赖模块：
- sys: 系统相关操作
- pathlib: 路径对象处理
"""

import sys
from pathlib import Path


def _find_project_root() -> Path:
    """
    查找项目根目录（开发模式下使用）

    返回：
        项目根目录路径对象
    """
    current_file = Path(__file__).resolve()
    return current_file.parent.parent


def get_application_dir() -> Path:
    """
    获取应用程序根目录（开发=源码包目录；打包=exe 所在目录）。

    全量搜索导出、续跑数据库等用户数据应写在此目录下，勿使用系统临时盘。
    """
    return _get_app_dir()


def _get_app_dir() -> Path:
    """
    获取应用程序根目录

    支持两种运行模式：
    1. 打包模式：通过 sys.frozen 判断，返回 EXE 所在目录
    2. 开发模式：返回项目源码根目录

    返回：
        应用程序根目录路径对象
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return _find_project_root()


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的完整路径

    参数：
        relative_path: 资源文件相对于项目根目录的路径

    返回：
        资源文件的完整路径对象

    示例：
        get_resource_path("data/config.json")
        -> Path("C:/project/data/config.json")
    """
    app_dir = _get_app_dir()

    primary_path = app_dir / relative_path
    if primary_path.exists():
        return primary_path

    internal_path = app_dir / "_internal" / relative_path
    return internal_path if internal_path.exists() else primary_path
