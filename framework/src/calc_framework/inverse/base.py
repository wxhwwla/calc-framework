# SPDX-License-Identifier: AGPL-3.0
"""

公式拟合器 SPI 基类 + 内置 FloorFormulaFitter 实现。



**SPI 架构**：FormulaFitter 是抽象基类，定义一个公式类型的完整信息：

- ``describe()`` — 公式的元数据（名称、参数名等）

- ``fit()`` — 从等级数据反推公式参数

- ``compute()`` — 用参数正向计算各等级值

- ``validate()`` — 验证参数拟合质量

"""



from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass

class FitResult:

    """拟合结果。"""



    params: dict[str, Any] = field(default_factory=dict)

    computed: list[float] = field(default_factory=list)

    max_error: float = 0.0

    is_exact: bool = False



    def summary(self) -> str:

        """返回人类可读的拟合结果摘要。"""

        status = "✓ 精确匹配" if self.is_exact else f"≈ 最大误差 {self.max_error:.4f}"

        params_str = ", ".join(f"{k}={v}" for k, v in self.params.items())

        return f"[{status}] {params_str}"





class FormulaFitter(ABC):

    """公式拟合器 SPI。



    子类必须实现：

    - ``describe()`` — 公式元数据

    - ``fit()`` — 反推参数

    - ``compute()`` — 正向计算

    - ``validate()`` — 验证拟合质量

    """



    @abstractmethod

    def describe(self) -> dict[str, Any]:

        """返回公式元数据。



        Returns:

            dict 包含:

            - name: 公式名称

            - description: 简要描述

            - param_names: 参数名列表

            - param_descriptions: 参数字典 {名: 描述}

        """



    @abstractmethod

    def fit(

        self,

        data: Sequence[int | float],

        *,

        num_levels: int | None = None,

        **options: Any,

    ) -> FitResult:

        """从等级数据反推公式参数。



        Args:

            data: 各等级的观测值（索引 0 = 等级 1）

            num_levels: 数据等级数（若为 None 则自动从 data 长度推断）

            options: 各公式类型的可选参数



        Returns:

            FitResult 包含拟合参数和评估信息

        """



    @abstractmethod

    def compute(

        self,

        params: dict[str, Any],

        num_levels: int = 1,

    ) -> list[float]:

        """用给定参数正向计算各等级的值。



        Args:

            params: 与 fit() 返回的 params 一致

            num_levels: 要计算的等级数



        Returns:

            各等级的值列表（索引 0 = 等级 1）

        """



    @abstractmethod

    def validate(

        self,

        params: dict[str, Any],

        data: Sequence[int | float],

    ) -> FitResult:

        """验证参数与观测数据的一致性，返回 ``FitResult``。"""





class FloorFormulaFitter(FormulaFitter):

    """通用 floor 线性公式拟合器。



    公式：value = base + floor((growth * (lv - 1) + offset) / divisor)



    支持整数和小数两条路线：

    - 整数数据：直接 floor，参数为 int

    - 小数数据：×10 → int floor → ÷10 还原，参数为 float



    内置自动 gcd 约分 + 多等价参数优选（按 growth → divisor → |offset| 字典序）。

    """



    def describe(self) -> dict[str, Any]:

        return {

            "name": "floor_linear",

            "description": "value = base + floor((growth * (lv - 1) + offset) / divisor)",

            "param_names": ["base", "growth", "divisor", "offset"],

            "param_descriptions": {

                "base": "1 级基础值",

                "growth": "成长系数",

                "divisor": "除数",

                "offset": "偏移量",

            },

            "required_options": [],

            "optional_options": {

                "divisor_range": "除数搜索范围 (默认 1..500)",

                "growth_range": "成长值搜索范围 (默认 1..1000)",

                "offset_search_limit": "offset 搜索限制 (默认 500)",

            },

        }



    def fit(

        self,

        data: Sequence[int | float],

        *,

        num_levels: int | None = None,

        **options: Any,

    ) -> FitResult:

        if num_levels is None:

            num_levels = len(data)

        if num_levels < 2:

            return FitResult(max_error=0)



        divisor_range = options.get("divisor_range", (1, 501))

        growth_range = options.get("growth_range", (1, 1001))

        offset_search_limit = options.get("offset_search_limit", 500)



        # 1. 探测并缩放

        scale_factor = self._detect_scale(data)

        scaled_data = [round(x * scale_factor) for x in data]

        scaled_base = scaled_data[0]



        # 2. 核心搜索

        result = self._search(scaled_data, scaled_base, scale_factor, num_levels,

                              divisor_range, growth_range, offset_search_limit)

        if result is None:

            return FitResult(max_error=999999.0)

        return result



    def compute(

        self,

        params: dict[str, Any],

        num_levels: int = 1,

    ) -> list[float]:

        base = params["base"]

        growth = params["growth"]

        divisor = params["divisor"]

        offset = params.get("offset", 0)

        is_decimal = params.get("is_decimal", False)



        if is_decimal:

            return [

                round(base + math.floor((growth * (lv - 1) + offset) / divisor), 1)

                for lv in range(1, num_levels + 1)

            ]

        return [

            round(base + math.floor((growth * (lv - 1) + offset) / divisor), 1)

            for lv in range(1, num_levels + 1)

        ]



    def validate(

        self,

        params: dict[str, Any],

        data: Sequence[int | float],

    ) -> FitResult:

        num_levels = len(data)

        computed = self.compute(params, num_levels)

        errors = [abs(computed[i] - data[i]) for i in range(num_levels)]

        max_error = max(errors) if errors else 0.0

        return FitResult(

            params=params,

            computed=computed,

            max_error=max_error,

            is_exact=max_error < 0.001,

        )



    # ── 内部 ─────────────────────────────────



    @staticmethod

    def _detect_scale(data: Sequence[int | float]) -> int:

        """探测缩放因子。含真小数 → 10，纯整数 → 1。"""

        for x in data:

            if isinstance(x, float) and x != int(x):

                return 10

        return 1



    @staticmethod

    def _restore_param(value: float | int, scale_factor: int) -> int | float:

        """将反推参数还原为录入格式。"""

        if scale_factor != 1:

            return value

        rounded = round(float(value))

        if abs(float(value) - rounded) < 1e-9:

            return int(rounded)

        return value



    @staticmethod

    def _params_sort_key(growth: int, divisor: int, offset: int) -> tuple[int, int, int]:

        """按 growth → divisor → |offset| 字典序排序。"""

        return (growth, divisor, abs(offset))



    @staticmethod

    def _gcd_normalize(growth: int, divisor: int, offset: int,

                       scaled_data: list[int], scaled_base: int) -> tuple[int, int, int]:

        """GCD 约分简化参数。"""

        factor = math.gcd(growth, divisor)

        while factor > 1:

            ng, nd = growth // factor, divisor // factor

            if all(

                scaled_base + math.floor((ng * (lv - 1) + offset) / nd) == scaled_data[lv - 1]

                for lv in range(1, len(scaled_data) + 1)

            ):

                growth, divisor = ng, nd

                factor = math.gcd(growth, divisor)

            else:

                break

        return growth, divisor, offset



    def _offset_bounds(self, scaled_data: list[int], scaled_base: int,

                       growth: int, divisor: int, num_levels: int) -> tuple[bool, int, int]:

        """计算 floor 公式在各等级成立的 offset 区间。"""

        offset_lower = -(10 ** 18)

        offset_upper = 10 ** 18

        for lv in range(1, num_levels + 1):

            target = scaled_data[lv - 1] - scaled_base

            lower = target * divisor - growth * (lv - 1)

            upper = (target + 1) * divisor - growth * (lv - 1) - 1

            offset_lower = max(offset_lower, math.ceil(lower))

            offset_upper = min(offset_upper, math.floor(upper))

            if offset_lower > offset_upper:

                return False, 0, 0

        return True, int(offset_lower), int(offset_upper)



    def _search(

        self,

        scaled_data: list[int],

        scaled_base: int,

        scale_factor: int,

        num_levels: int,

        divisor_range: tuple[int, int],

        growth_range: tuple[int, int],

        offset_search_limit: int,

    ) -> FitResult | None:

        """核心搜索：先找精确解，再找近似最优解。"""

        best_params: tuple[int, int, int] | None = None

        best_key: tuple[int, int, int] | None = None

        best_error = float("inf")



        def _consider(growth: int, divisor: int, offset: int, error: float) -> None:

            """_consider。"""
            nonlocal best_params, best_key, best_error

            key = self._params_sort_key(growth, divisor, offset)

            if best_error < 0.001:

                if error < 0.001 and (best_key is None or key < best_key):

                    best_key = key

                    best_params = (growth, divisor, offset)

                return

            if error < best_error or (error == best_error and (best_key is None or key < best_key)):

                best_error = error

                best_key = key

                best_params = (growth, divisor, offset)



        # 精确解

        for growth in range(*growth_range):

            for divisor in range(*divisor_range):

                valid, offset_lower, offset_upper = self._offset_bounds(

                    scaled_data, scaled_base, growth, divisor, num_levels)

                if not valid:

                    continue

                for offset in range(offset_lower, offset_upper + 1):

                    error = sum(

                        abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_data[lv - 1])

                        for lv in range(1, num_levels + 1)

                    )

                    if error < 0.001:

                        growth, divisor, offset = self._gcd_normalize(

                            growth, divisor, offset, scaled_data, scaled_base)

                        return FitResult(

                            params={

                                "base": self._restore_param(scaled_base / scale_factor, scale_factor),

                                "growth": self._restore_param(growth / scale_factor, scale_factor),

                                "divisor": divisor,

                                "offset": self._restore_param(offset / scale_factor, scale_factor),

                                "is_decimal": scale_factor > 1,

                            },

                            max_error=0.0,

                            is_exact=True,

                        )



        # 近似解

        for growth in range(*growth_range):

            for divisor in range(*divisor_range):

                total_offset = sum(

                    (scaled_data[lv - 1] - scaled_base) * divisor - growth * (lv - 1)

                    for lv in range(1, num_levels + 1))

                offset = round(total_offset / num_levels)

                error = sum(

                    abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_data[lv - 1])

                    for lv in range(1, num_levels + 1))

                _consider(growth, divisor, int(offset), float(error))



                valid, offset_lower, offset_upper = self._offset_bounds(

                    scaled_data, scaled_base, growth, divisor, num_levels)

                if not valid:

                    continue

                offset_end = min(offset_upper + 1, offset_lower + offset_search_limit)

                for offset in range(offset_lower, offset_end):

                    error = sum(

                        abs(scaled_base + math.floor((growth * (lv - 1) + offset) / divisor) - scaled_data[lv - 1])

                        for lv in range(1, num_levels + 1))

                    _consider(growth, divisor, int(offset), float(error))



        if best_params is None or best_error >= num_levels * 0.1:

            return None



        growth, divisor, offset = best_params

        if best_error < 0.001:

            growth, divisor, offset = self._gcd_normalize(

                growth, divisor, offset, scaled_data, scaled_base)



        return FitResult(

            params={

                "base": self._restore_param(scaled_base / scale_factor, scale_factor),

                "growth": self._restore_param(growth / scale_factor, scale_factor),

                "divisor": divisor,

                "offset": self._restore_param(offset / scale_factor, scale_factor),

                "is_decimal": scale_factor > 1,

            },

            max_error=best_error / num_levels,

            is_exact=best_error < 0.001,

        )

