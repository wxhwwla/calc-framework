"""
公式类型注册表 — FormulaType 注册与发现。
"""

from __future__ import annotations

from typing import Any

from .base import FormulaFitter


class FormulaType:
    """公式类型描述符。

    ``FormulaType`` 将公式元信息与 FormulaFitter 实例绑定，
    注册到全局 ``registry`` 后可被 ``InverseEngine`` 按名称查找。

    用法::

        from calc_framework.inverse.base import FloorFormulaFitter
        from calc_framework.inverse.registry import FormulaType, registry

        ft = FormulaType(id="floor_linear", name="Floor 线性公式",
                         fitter=FloorFormulaFitter())
        registry.register(ft)
    """

    def __init__(
        self,
        id: str,
        name: str = "",
        description: str = "",
        fitter: FormulaFitter | None = None,
    ):
        self.id = id
        self.name = name or id
        self.description = description
        self._fitter = fitter

    @property
    def fitter(self) -> FormulaFitter:
        if self._fitter is None:
            raise ValueError(f"FormulaType {self.id} 未绑定 fitter")
        return self._fitter

    def to_dict(self) -> dict[str, Any]:
        meta = self.fitter.describe()
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or meta.get("description", ""),
            "param_names": meta.get("param_names", []),
            "param_descriptions": meta.get("param_descriptions", {}),
        }


class Registry:
    """全局公式类型注册表。"""

    def __init__(self):
        self._types: dict[str, FormulaType] = {}

    def register(self, ft: FormulaType) -> None:
        self._types[ft.id] = ft

    def get(self, formula_id: str) -> FormulaType:
        if formula_id not in self._types:
            raise KeyError(f"未知公式类型: {formula_id!r}，可用: {list(self._types.keys())}")
        return self._types[formula_id]

    def list_types(self) -> list[FormulaType]:
        return list(self._types.values())

    def list_ids(self) -> list[str]:
        return list(self._types.keys())


# 全局注册表
registry = Registry()

# ── 注册内置公式类型 ──────────────────────────
registry.register(FormulaType(
    id="floor_linear",
    name="Floor 线性公式",
    description="value = base + floor((growth * (lv - 1) + offset) / divisor)",
))

try:
    from calc_framework.inverse.base import FloorFormulaFitter
    registry.get("floor_linear")._fitter = FloorFormulaFitter()
except ImportError:
    pass
