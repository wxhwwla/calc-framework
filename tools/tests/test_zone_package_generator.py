# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""乘区包生成器唯一实现与发布入口委托测试。"""

from __future__ import annotations

from tools import generate_endfield_zone_package as core
from tools.publish import generate_endfield_zone_package as publish


def test_publish_entry_delegates_to_core() -> None:
    """发布入口必须复用唯一实现，而不是复制一份生成器。"""
    assert publish.build_package is core.build_package
    assert publish.ALL_ZONE_BUILDERS is core.ALL_ZONE_BUILDERS
    assert publish.OUTPUT_DIR == core.REPO_ROOT / "output"
