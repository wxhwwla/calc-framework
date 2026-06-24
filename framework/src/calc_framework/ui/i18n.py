# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""桌面 GUI 国际化 (i18n) 模块。

提供简单、无外部依赖的翻译系统，用于 PySide6 桌面应用。
与 Web 端使用相同的键名结构（dot-notation），翻译数据从 JSON 文件加载。

用法::

    from calc_framework.ui.i18n import tr, set_locale

    set_locale("en")
    label.setText(tr("compute.title"))        # → "Damage Calculator"
    label.setText(tr("common.close"))          # → "Close"

设计原则:
    - 单例模式 — 全局共享翻译状态
    - JSON 数据文件 — 与 Qt .ts/.qm 解耦，无需 lrelease
    - 与 Web i18n 共享键名结构 — 渐进统一
    - 自动检测系统语言 — locale.getdefaultlocale()
    - 回退到 zh-CN — 中文作为源语言
"""

from __future__ import annotations

import json
import locale
import logging
from pathlib import Path
from threading import Lock
from typing import Any

_logger = logging.getLogger(__name__)

# ── 支持的 locale ──────────────────────────────────────────

SUPPORTED_LOCALES = ("zh-CN", "en")
_FALLBACK_LOCALE = "zh-CN"


def _detect_system_locale() -> str:
    """检测系统默认语言并映射到支持的 locale。

    返回 ``zh-CN`` 如果系统语言以 "zh" 开头，否则返回 ``en``。
    """
    try:
        sys_locale, _ = locale.getdefaultlocale()
    except (ValueError, locale.Error):
        sys_locale = None

    if sys_locale and sys_locale.lower().startswith("zh"):
        return "zh-CN"
    return "en"


def _data_dir() -> Path:
    """返回存放翻译 JSON 文件的目录路径。"""
    return Path(__file__).resolve().parent / "i18n_data"


def _load_json_file(path: Path) -> dict[str, Any]:
    """加载 JSON 翻译文件，出错时返回空字典。"""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        _logger.warning("i18n 文件未找到: %s", path)
    except json.JSONDecodeError as exc:
        _logger.warning("i18n 文件 JSON 解析失败: %s — %s", path, exc)
    return {}


def _flatten_dict(
    nested: dict[str, Any],
    prefix: str = "",
    sep: str = ".",
) -> dict[str, str]:
    """将嵌套字典扁平化为 ``"a.b.c": "值"`` 形式的字典。

    忽略非字符串叶子节点（如子字典），仅扁平化最终值为字符串的路径。
    """
    result: dict[str, str] = {}
    for key, value in nested.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
        if isinstance(value, str):
            result[full_key] = value
        elif isinstance(value, dict):
            result.update(_flatten_dict(value, full_key, sep))
        # 忽略其他类型（int、list 等）
    return result


# ── DesktopTranslator ──────────────────────────────────────


class DesktopTranslator:
    """桌面翻译管理器。

    单例 — 通过模块级 ``_instance`` 和 ``_get_translator()`` 访问。
    避免在用户代码中直接实例化，使用模块级 ``tr()`` 函数代替。
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._current_locale: str = _detect_system_locale()
        # _cache[locale_str] = {key: value}
        self._cache: dict[str, dict[str, str]] = {}

    # ── public API ─────────────────────────────────────────

    @property
    def current_locale(self) -> str:
        """当前激活的 locale，如 ``"zh-CN"`` 或 ``"en"``。"""
        return self._current_locale

    def set_locale(self, locale_str: str) -> None:
        """切换当前 locale。

        如果请求的 locale 不受支持，回退到 ``zh-CN``。
        """
        if locale_str not in SUPPORTED_LOCALES:
            _logger.warning("不支持的 locale '%s'，回退到 '%s'", locale_str, _FALLBACK_LOCALE)
            locale_str = _FALLBACK_LOCALE

        if locale_str != self._current_locale:
            self._current_locale = locale_str
            _logger.info("i18n locale 已切换为: %s", locale_str)

    def load_translations(self, locale_str: str) -> None:
        """预加载指定 locale 的翻译数据到缓存。

        通常在启动时调用一次即可；``tr()`` 也会在首次访问时按需加载。
        """
        if locale_str not in SUPPORTED_LOCALES:
            _logger.warning("跳过不支持的 locale: %s", locale_str)
            return
        self._ensure_loaded(locale_str)

    def reload(self) -> None:
        """清空缓存，强制下次 ``tr()`` 调用时重新从磁盘加载。"""
        with self._lock:
            self._cache.clear()

    def tr(self, key: str, /, **kwargs: Any) -> str:
        """翻译指定键。

        支持 ``**kwargs`` 用于插值，例如 ``tr("result.count", n=5)``。

        如果键在当前 locale 中不存在，回退到 ``zh-CN``。
        如果键在两种 locale 中都不存在，返回键本身作为占位符。
        """
        translation = self._lookup(key)
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError) as exc:
                _logger.debug("i18n 插值失败 key=%r: %s", key, exc)
                return translation
        return translation

    # ── internal ───────────────────────────────────────────

    def _ensure_loaded(self, locale_str: str) -> dict[str, str]:
        """确保指定 locale 的翻译已加载到缓存。返回扁平翻译字典。"""
        with self._lock:
            if locale_str in self._cache:
                return self._cache[locale_str]

        path = _data_dir() / f"{locale_str}.json"
        nested = _load_json_file(path)
        flat = _flatten_dict(nested)

        with self._lock:
            self._cache[locale_str] = flat
        _logger.debug("已加载 i18n locale: %s (%d 条)", locale_str, len(flat))
        return flat

    def _lookup(self, key: str) -> str:
        """按 key 查找翻译，带回退逻辑。"""
        # 1. 查找当前 locale
        current = self._ensure_loaded(self._current_locale)
        if key in current:
            return current[key]

        # 2. 回退到 zh-CN
        if self._current_locale != _FALLBACK_LOCALE:
            fallback = self._ensure_loaded(_FALLBACK_LOCALE)
            if key in fallback:
                return fallback[key]

        # 3. 未找到 — 返回键名本身作为占位符
        _logger.debug("i18n 键未找到: %s", key)
        return key


# ── 模块级单例 ─────────────────────────────────────────────

_instance: DesktopTranslator | None = None
_lock_singleton = Lock()


def _get_translator() -> DesktopTranslator:
    """获取全局 DesktopTranslator 单例（线程安全）。"""
    global _instance
    if _instance is None:
        with _lock_singleton:
            if _instance is None:
                _instance = DesktopTranslator()
    return _instance


# ── 公开 API 函数 ──────────────────────────────────────────


def tr(key: str, /, **kwargs: Any) -> str:
    """翻译字符串键。

    用法::

        from calc_framework.ui.i18n import tr
        label.setText(tr("compute.title"))
        label.setText(tr("result.count", n=5))
    """
    return _get_translator().tr(key, **kwargs)


def set_locale(locale_str: str) -> None:
    """设置当前语言 locale。

    用法::

        from calc_framework.ui.i18n import set_locale
        set_locale("en")
    """
    _get_translator().set_locale(locale_str)


def current_locale() -> str:
    """获取当前激活的 locale。"""
    return _get_translator().current_locale


def reload_translations() -> None:
    """清空缓存，强制从磁盘重新加载所有翻译。"""
    _get_translator().reload()


def load_translations(locale_str: str) -> None:
    """预加载指定 locale 的翻译数据。"""
    _get_translator().load_translations(locale_str)


# ── 模块导入时自动预加载当前 locale ──────────────────────────

_load_translator = _get_translator()
import contextlib

with contextlib.suppress(Exception):
    _load_translator.load_translations(_load_translator.current_locale)
# 静默处理 — 翻译文件可能尚未创建，tr() 会优雅降级
