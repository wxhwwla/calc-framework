# SPDX-License-Identifier: AGPL-3.0
"""
通用公式反推引擎 — SPI（Service Provider Interface）框架。

将反推逻辑从游戏专属适配器中提炼为框架级服务，
任何游戏只需注册 FormulaType 即可使用。

用法::

    from calc_framework.inverse.engine import InverseEngine
    from calc_framework.inverse.registry import registry

    engine = InverseEngine()
    result = engine.fit(data, "floor_linear", num_levels=90)
"""

from .advanced import ExponentialFormulaFitter, PiecewiseFormulaFitter, ThresholdFormulaFitter
from .base import FitResult, FloorFormulaFitter, FormulaFitter
from .engine import InverseEngine
from .registry import FormulaType, registry

__all__ = [
    "ExponentialFormulaFitter",
    "FitResult",
    "FloorFormulaFitter",
    "FormulaFitter",
    "FormulaType",
    "InverseEngine",
    "PiecewiseFormulaFitter",
    "ThresholdFormulaFitter",
    "registry",
]
