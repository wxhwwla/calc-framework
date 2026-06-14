# SPDX-License-Identifier: AGPL-3.0
"""
高级公式拟合器 — 兼容 re-export 层。

所有拟合策略实现已移至 :mod:`~calc_framework.inverse.strategies`。
"""

from __future__ import annotations

from .strategies import (  # noqa: F401  # re-export for backward compat
    ExponentialFormulaFitter,  # type: ignore[unused-import]
    PiecewiseFormulaFitter,  # type: ignore[unused-import]
    ThresholdFormulaFitter,  # type: ignore[unused-import]
)
