# SPDX-License-Identifier: AGPL-3.0
"""
高级拟合策略 — re-export 入口（兼容性）。

各拟合器已拆分至独立模块：
  - :mod:`~calc_framework.inverse.exponential_fitter`
  - :mod:`~calc_framework.inverse.piecewise_fitter`
  - :mod:`~calc_framework.inverse.threshold_fitter`
"""

from __future__ import annotations

from .exponential_fitter import ExponentialFormulaFitter  # noqa: F401
from .piecewise_fitter import PiecewiseFormulaFitter  # noqa: F401
from .threshold_fitter import ThresholdFormulaFitter  # noqa: F401
