# -*- coding: utf-8 -*-
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
from .base import FitResult, FloorFormulaFitter, FormulaFitter, GrowthParams
from .curve import (
    CurveBlueprint,
    SegmentCurveEngine,
    SegmentSpec,
    expand_segment_linear,
    single_segment_blueprint,
)
from .engine import InverseEngine
from .materialize import (
    GROWTH_PARAM_KEY,
    blueprint_from_stored,
    has_segment_storage,
    materialize_entity_from_stored_segments,
    merge_blueprint_segments,
)
from .registry import FormulaType, registry
from .schema import GameInverseAdapter, InverseSchema
from .segment_adapter import SegmentCurveAdapter

__all__ = [
    "GROWTH_PARAM_KEY",
    "CurveBlueprint",
    "ExponentialFormulaFitter",
    "FitResult",
    "FloorFormulaFitter",
    "FormulaFitter",
    "FormulaType",
    "GameInverseAdapter",
    "GrowthParams",
    "InverseEngine",
    "InverseSchema",
    "PiecewiseFormulaFitter",
    "SegmentCurveAdapter",
    "SegmentCurveEngine",
    "SegmentSpec",
    "ThresholdFormulaFitter",
    "blueprint_from_stored",
    "expand_segment_linear",
    "has_segment_storage",
    "materialize_entity_from_stored_segments",
    "merge_blueprint_segments",
    "registry",
    "single_segment_blueprint",
]
