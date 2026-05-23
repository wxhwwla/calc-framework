#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pytest 全局夹具：缓存清理、测试分层标记说明。"""

from __future__ import annotations

import pytest

from calculation.result_cache import reset_global_result_cache


@pytest.fixture(autouse=True)
def _reset_global_calculation_cache() -> None:
    """每条用例前后清空全局结果缓存，避免跨测堆积大对象。"""
    reset_global_result_cache()
    yield
    reset_global_result_cache()
