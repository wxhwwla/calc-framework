#!/usr/bin/env python3
"""
路径工具模块

提供统一的路径处理功能，支持两种运行模式：
1. 开发模式：从源码运行（获取项目根目录）
2. 打包模式：从发布文件夹内的 EXE 运行（读取 EXE **同级**目录下的 JSON；
   兼容 PyInstaller onedir 的 ``_internal/`` 回退，但正式发布包应将数据放在 exe 旁）
"""

import sys
from pathlib import Path


def _find_project_root() -> Path:
    current_file = Path(__file__).resolve()
    repo_root = current_file.parent.parent
    game_root = repo_root / "games" / "endfield"
    if game_root.is_dir():
        return game_root
    return repo_root


def get_application_dir() -> Path:
    return _get_app_dir()


def _get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    else:
        return _find_project_root()


def get_resource_path(relative_path: str) -> Path:
    app_dir = _get_app_dir()
    primary_path = app_dir / relative_path
    if primary_path.exists():
        return primary_path
    internal_path = app_dir / "_internal" / relative_path
    return internal_path if internal_path.exists() else primary_path


def get_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
