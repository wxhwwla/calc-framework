# SPDX-License-Identifier: AGPL-3.0
"""名称规范化处理。"""

import re


_UNIFY_WHITESPACE = re.compile(r"\s+")


def normalize_name_for_match(name: str) -> str:
    return _UNIFY_WHITESPACE.sub(" ", name).strip()
