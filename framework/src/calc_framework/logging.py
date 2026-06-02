# SPDX-License-Identifier: AGPL-3.0
"""统一日志模块 — 集中配置格式、级别、输出目标。



用法::



    # 在应用入口调用一次

    from calc_framework.logging import setup_logging

    setup_logging(level="INFO", log_file="calc_framework.log")



    # 在各模块顶部获取 logger

    from calc_framework.logging import get_logger

    logger = get_logger(__name__)

    logger.info("DAG 求值完成，%d 个节点", node_count)

"""



from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_LOG_FORMAT = "[%(asctime)s.%(msecs)03d] [%(levelname)-7s] [%(name)s] %(message)s"

_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOG_ENCODING = "utf-8"



_LEVELS: dict[str, int] = {

    "DEBUG": logging.DEBUG,

    "INFO": logging.INFO,

    "WARNING": logging.WARNING,

    "ERROR": logging.ERROR,

    "CRITICAL": logging.CRITICAL,

}



_DEFAULT_LEVEL: str = "WARNING"

_ROOT_LOGGER_NAME: str = "calc_framework"



_initialized: bool = False





def setup_logging(

    level: str | int | None = None,

    log_file: str | None = None,

    console: bool = True,

    max_bytes: int = 5 * 1024 * 1024,

    backup_count: int = 3,

) -> None:

    """全局初始化框架日志系统。



    可在应用入口调用一次（通常是 ``main.py``）。后续重复调用无副作用。



    参数:

        level: 日志级别（``"DEBUG"`` / ``"INFO"`` / ``"WARNING"`` 或 ``logging.DEBUG``）。

               默认读取环境变量 ``CALC_FRAMEWORK_LOG_LEVEL``，仍为空则 ``WARNING``。

        log_file: 日志文件路径。默认读取 ``CALC_FRAMEWORK_LOG_FILE``，

                  仍为空则不输出文件。

        console: 是否输出到控制台（stdout），默认 ``True``。

        max_bytes: 日志文件轮转大小，默认 5 MB。

        backup_count: 保留的旧日志文件数，默认 3。

    """

    global _initialized

    if _initialized:

        return

    _initialized = True



    resolved_level = _resolve_level(level)

    resolved_file = log_file or os.environ.get("CALC_FRAMEWORK_LOG_FILE", "").strip() or None



    root = logging.getLogger(_ROOT_LOGGER_NAME)

    root.setLevel(resolved_level)

    root.handlers.clear()



    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)



    if console:

        handler = logging.StreamHandler(sys.stdout)

        handler.setLevel(resolved_level)

        handler.setFormatter(formatter)

        root.addHandler(handler)



    if resolved_file:

        os.makedirs(os.path.dirname(resolved_file) or ".", exist_ok=True)

        handler = RotatingFileHandler(

            resolved_file,

            maxBytes=max_bytes,

            backupCount=backup_count,

            encoding=_LOG_ENCODING,

        )

        handler.setLevel(resolved_level)

        handler.setFormatter(formatter)

        root.addHandler(handler)



    root.info("日志系统初始化完成 (level=%s, file=%s)", resolved_level, resolved_file or "(console only)")





def get_logger(name: str) -> logging.Logger:

    """获取框架命名空间下的 logger。



    所有框架日志统一挂在 ``calc_framework`` 根 logger 下，

    便于通过 ``calc_framework`` 统一控制级别。



    参数:

        name: 模块名，通常传入 ``__name__``。



    返回:

        配置好的 Logger 实例。

    """

    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")





def set_level(level: str | int) -> None:

    """运行时动态修改日志级别。"""

    resolved = _LEVELS.get(level.upper(), level) if isinstance(level, str) else level

    logging.getLogger(_ROOT_LOGGER_NAME).setLevel(resolved)





def _resolve_level(level: str | int | None) -> int:

    """_resolve_level。"""
    if level is not None:

        if isinstance(level, int):

            return level

        resolved = _LEVELS.get(level.upper())

        if resolved is not None:

            return resolved

    env = os.environ.get("CALC_FRAMEWORK_LOG_LEVEL", "").strip().upper()

    if env in _LEVELS:

        return _LEVELS[env]

    return _LEVELS[_DEFAULT_LEVEL]

