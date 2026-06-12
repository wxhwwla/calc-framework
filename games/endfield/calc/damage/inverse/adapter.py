# SPDX-License-Identifier: AGPL-3.0
"""
终末地逆推适配器 — ``GameInverseAdapter`` 的具体实现。

将终末地的领域知识（90 级属性、9/12 级技能倍率、94 级去重）
声明为 InverseSchema 配置，委托框架 InverseEngine 执行拟合。

旧 `api.py` / `attribute.py` / `skill.py` 的公开函数保留为向后兼容的薄封装，
内部委托给本模块的 ``EndfieldInverseAdapter``。
"""

from __future__ import annotations

from collections.abc import Sequence

from calc_framework.inverse.base import FitResult
from calc_framework.inverse.schema import GameInverseAdapter, InverseSchema

# ── 终末地数据去重工具 ──────────────────────────

_DUPLICATE_INDICES_94 = [20, 41, 62, 83]
"""94 级数据中的重复位置（等级 20/40/60/80 各重复一次）。"""


def remove_duplicates_94(data: Sequence[float]) -> list[float]:
    """从 94 个数据中移除 4 个重复点，得到标准 90 级数据。"""
    if len(data) != 94:
        raise ValueError(f"输入数据长度应为 94，实际为 {len(data)}")
    return [data[i] for i in range(94) if i not in _DUPLICATE_INDICES_94]


# ── 终末地逆推适配器 ────────────────────────────


class EndfieldInverseAdapter(GameInverseAdapter):
    """终末地逆推适配器。

    声明终末地的三种数据模式：
    - 90 级属性成长
    - 12 级技能倍率（10-12 级为特殊值）
    - 9 级技能倍率（潜能/附加属性）
    """

    @property
    def schemas(self) -> list[InverseSchema]:
        return [
            InverseSchema(
                length=90,
                label="属性成长 (1-90 级)",
                search_options={
                    "divisor_range": (1, 201),
                    "growth_range": (1, 301),
                    "offset_search_limit": 200,
                },
            ),
            InverseSchema(
                length=12,
                label="技能倍率 (1-12 级，10-12 特殊值)",
                special_indices=[9, 10, 11],
            ),
            InverseSchema(
                length=9,
                label="技能倍率 (1-9 级，无特殊值)",
            ),
        ]

    def default_formula(self) -> str:
        return "floor_linear"

    # ── 后处理钩子 ───────────────────────────────

    def fit_special_logic(
        self,
        schema: InverseSchema,
        base_data: Sequence[float],
        result: FitResult,
        original_data: Sequence[float],
    ) -> FitResult:
        """技能倍率的特殊值后处理。

        对于 12 级技能：前 9 级拟合，特殊值直接从原始数据提取。
        对于 9 级技能（无特殊值）：若 9 级精确拟合失败，自动将第 9 级降级为特殊值重试。
        """
        # 12 级技能：正常处理（特殊值已在 fit() 中注入 params）
        if schema.length == 12:
            return result

        # 9 级技能：尝试降级第 9 级为特殊值
        if schema.length == 9 and not result.is_exact and result.params:
            special_values = [original_data[8]]
            base_8 = original_data[:8]
            options = schema.search_options or {}

            retry_result = self._engine.fit(base_8, formula_id=schema.formula_id, **options)
            if retry_result.is_exact and retry_result.params:
                retry_result.params["special_values"] = special_values
                return retry_result

        return result

    # ── 94 级去重支持 ───────────────────────────

    def fit_from_94(self, data: Sequence[float]) -> FitResult:
        """从 94 级数据（含 4 个重复点）拟合 90 级属性公式。

        自动去重后调用标准 90 级拟合。
        """
        clean = remove_duplicates_94(data)
        return self.fit(clean)
