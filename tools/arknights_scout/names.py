# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""名称规范化处理。"""

import re


_UNIFY_WHITESPACE = re.compile(r"\s+")


def normalize_name_for_match(name: str) -> str:
    """normalize_name_for_match 实现。

    Args:
        name: 参数描述。

    Returns:
        返回值描述。
    """
    return _UNIFY_WHITESPACE.sub(" ", name).strip()
