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
from calc_framework.config.entity_meta import (
    EntityMetaError,
    format_detail_value,
    normalize_entity_detail,
    normalize_entity_input_rules,
    rule_matches,
)
from calc_framework.config.manager import AdapterManager, discover_adapters, get_adapters_dir
from calc_framework.config.scaffold import (
    AdapterScaffoldConfig,
    ScaffoldResult,
    scaffold_adapter_directory,
)
from calc_framework.config.watcher import AdapterWatcher

__all__ = [
    "AdapterError",
    "AdapterManager",
    "AdapterNotFoundError",
    "AdapterPackage",
    "AdapterScaffoldConfig",
    "AdapterWatcher",
    "EntityMetaError",
    "InvalidMetaError",
    "ScaffoldResult",
    "discover_adapters",
    "format_detail_value",
    "get_adapters_dir",
    "normalize_entity_detail",
    "normalize_entity_input_rules",
    "rule_matches",
    "scaffold_adapter_directory",
]
