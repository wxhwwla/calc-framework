# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数据加载模块"""

from calc_framework.errors import CalcFrameworkError


class DataLoadingError(CalcFrameworkError):
    """游戏数据加载领域所有异常的基类（继承框架 CalcFrameworkError）。"""


from .game_data_facade import GameDataFacade
from .loader import (
    DataLoadError,
    get_characters,
    get_weapons,
    preload_game_data,
)
from .loader_crud import (
    check_and_save_characters,
    check_and_save_weapons,
    save_characters,
    save_weapons,
)

__all__ = [
    "DataLoadError",
    "GameDataFacade",
    "check_and_save_characters",
    "check_and_save_weapons",
    "get_characters",
    "get_weapons",
    "preload_game_data",
    "save_characters",
    "save_weapons",
]
