# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""启动器内置说明书内容。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr

from utils.gui.help_dialog import HelpSection


def build_launcher_help() -> list[HelpSection]:
    return [
        _overview(),
        _tools(),
        _calcpack(),
        _tips(),
    ]


def _overview() -> HelpSection:
    return HelpSection(
        category=tr("desktop.launcher.helpCatIntro"),
        title=tr("desktop.launcher.helpTitleOverview"),
        content=tr("desktop.launcher.helpBodyOverview"),
    )


def _tools() -> HelpSection:
    return HelpSection(
        category=tr("desktop.launcher.helpCatTools"),
        title=tr("desktop.launcher.helpTitleTools"),
        content=tr("desktop.launcher.helpBodyTools"),
    )


def _calcpack() -> HelpSection:
    return HelpSection(
        category=tr("desktop.launcher.helpCatCalcpack"),
        title=tr("desktop.launcher.helpTitleCalcpack"),
        content=tr("desktop.launcher.helpBodyCalcpack"),
    )


def _tips() -> HelpSection:
    return HelpSection(
        category=tr("desktop.launcher.helpCatFaq"),
        title=tr("desktop.launcher.helpTitleTips"),
        content=tr("desktop.launcher.helpBodyTips"),
    )
