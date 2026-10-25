# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""工具模块

提供通用的工具函数，支持应用程序路径处理等功能。

导出的函数：
- get_resource_path: 获取资源文件的完整路径
"""

from .path_utils import get_application_dir, get_resource_path

__all__ = ["get_resource_path"]
