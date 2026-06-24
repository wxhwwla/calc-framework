#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""数据加载器抽象基类 — 适配器需实现的接口。"""

from abc import ABC, abstractmethod
from typing import Any


class DataContextLoader(ABC):
    """数据上下文加载器抽象基类。



    各游戏适配器需继承此类，实现 ``build_context`` 方法。

    框架通过此接口获取 ``evaluate_graph`` 所需的数据上下文，

    不关心内部逻辑如何组装。



    用法::



        class EndfieldLoader(DataContextLoader):

            def build_context(self, **kwargs):

                char = kwargs["character"]

                weapon = kwargs.get("weapon")

                return make_context(

                    character=_build_char_context(char),

                    weapon=_build_weapon_context(weapon),

                    computed=_build_computed(char, weapon),

                )

    """

    @abstractmethod
    def build_context(self, **kwargs: Any) -> dict[str, Any]:
        """从原始数据构建 DAG 求值所需的 DataContext。



        Args:

            **kwargs: 适配器自定义参数（如 character/weapon/level 等）



        Returns:

            求值上下文字典，至少包含 ``character``/``weapon``/``computed`` 等顶层 key。

        """

        ...
