"""数据加载模块"""


class DataLoadingError(Exception):
    """游戏数据加载领域所有异常的基类。"""


from .game_data_facade import GameDataFacade
from .loader import (
    DataLoadError,
    check_and_save_characters,
    check_and_save_weapons,
    get_characters,
    get_weapons,
    preload_game_data,
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
