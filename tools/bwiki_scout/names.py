#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0

# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""名称规范化，用于 Wiki 页面标题与本地 JSON「名称」对齐。"""

import re


_FULLWIDTH_SPACE = "\u3000"


def normalize_name_for_match(name: str) -> str:
    """去除首尾空白，并将全角空格视为无分隔。"""

    text = (name or "").strip()

    text = text.replace(_FULLWIDTH_SPACE, "")

    text = re.sub(r"\s+", "", text)

    return text
