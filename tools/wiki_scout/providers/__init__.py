# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout 内置数据源。

导入本包会触发所有 provider 的注册（供 `list_providers()` 使用）。
"""

from .bwiki import BWIKIExtractor
from .warfarin import WarfarinProvider
from .wjdlglr import WjdlglrProvider

__all__ = [
    "BWIKIExtractor",
    "WarfarinProvider",
    "WjdlglrProvider",
]
