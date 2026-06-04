# SPDX-License-Identifier: AGPL-3.0
"""计算器生成器 — AI 驱动的适配器包生成工具。

用法:
    from tools.generator import GeneratorEngine

    engine = GeneratorEngine()
    templates = engine.list_templates()
    files = engine.generate("simple", game_name="我的游戏", ...)
"""

from .engine import GeneratorEngine
from .templates import list_templates, CATEGORY_TEMPLATES
from .validators import validate_adapter

__all__ = [
    "CATEGORY_TEMPLATES",
    "GeneratorEngine",
    "list_templates",
    "validate_adapter",
]
