# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""增强工具弹窗共用的样式常量。"""

from __future__ import annotations

__all__ = ["_HINT_COLOR", "_PRIMARY_BTN_STYLE", "_SEC_BTN_STYLE", "_SMALL_LABEL"]

_SMALL_LABEL = "color: #CCCCCC;"

_HINT_COLOR = "color: #888888;"

_SEC_BTN_STYLE = """

    QPushButton {

        background-color: transparent; color: #D1D1D1;

        border: 1px solid #464646; border-radius: 6px; padding: 6px 16px;

    }

    QPushButton:hover { border-color: #2B6CB6; color: white; }

"""

_PRIMARY_BTN_STYLE = """

    QPushButton {

        background-color: #2B6CB6; color: white;

        border-radius: 6px; padding: 6px 16px; font-weight: bold;

    }

    QPushButton:hover { background-color: #3182CE; }

"""
