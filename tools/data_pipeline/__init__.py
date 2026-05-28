#!/usr/bin/env python3
"""数据录入 ETL 工具链：将原始数据（CSV / 旧 JSON）转换为标准 schema。"""

from . import readers, transformers, validators
from .schema import (
    EntitySchema,
    SkillSchema,
    SegmentSchema,
    EntityType,
    STANDARD_ENTITY_TYPES,
)

__all__ = [
    "EntitySchema",
    "SkillSchema",
    "SegmentSchema",
    "EntityType",
    "STANDARD_ENTITY_TYPES",
    "readers",
    "transformers",
    "validators",
]
