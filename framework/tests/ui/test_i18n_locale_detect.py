# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""系统语言检测：环境变量、Windows 显示名与 locale 异常回退。"""

from __future__ import annotations

import locale

import pytest

from calc_framework.ui.i18n import _detect_system_locale

_ENV_KEYS = ("LC_ALL", "LC_MESSAGES", "LANG")


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.mark.parametrize("raw", ["zh_CN.UTF-8", "zh_TW.UTF-8", "zh"])
def test_env_zh_variants_return_zh_cn(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("LANG", raw)

    assert _detect_system_locale() == "zh-CN"


@pytest.mark.parametrize("raw", ["en_US.UTF-8", "C.UTF-8", "ja_JP.UTF-8"])
def test_env_non_zh_returns_en(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("LANG", raw)

    assert _detect_system_locale() == "en"


def test_windows_chinese_display_name_returns_zh_cn(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setattr(locale, "getlocale", lambda: ("Chinese (Simplified)_China", "936"))

    assert _detect_system_locale() == "zh-CN"


def test_windows_english_display_name_returns_en(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setattr(locale, "getlocale", lambda: ("English_United States", "1252"))

    assert _detect_system_locale() == "en"


def test_locale_error_falls_back_to_en(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)

    def _raise() -> tuple[str | None, str | None]:
        raise locale.Error("unknown locale")

    monkeypatch.setattr(locale, "getlocale", _raise)

    assert _detect_system_locale() == "en"
