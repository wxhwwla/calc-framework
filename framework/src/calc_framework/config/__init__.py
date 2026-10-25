#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""配置子包 — 适配包加载器。

用法::

    from calc_framework.config import (
        AdapterPackage, AdapterManager, discover_adapters,
        AdapterWatcher,
    )
"""

from calc_framework.config.adapter import (
    AdapterError,
    AdapterNotFoundError,
    AdapterPackage,
    InvalidMetaError,
)
from calc_framework.config.manager import AdapterManager, discover_adapters
from calc_framework.config.watcher import AdapterWatcher

__all__ = [
    "AdapterError",
    "AdapterManager",
    "AdapterNotFoundError",
    "AdapterPackage",
    "AdapterWatcher",
    "InvalidMetaError",
    "discover_adapters",
]
