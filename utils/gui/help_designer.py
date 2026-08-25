# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数据设计器内置说明书内容。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr

from utils.gui.help_dialog import HelpSection
from utils.gui.help_loader import load_multi_category


def build_designer_help() -> list[HelpSection]:
    result = [
        _overview(),
        _inverse_tab(),
        _data_editor_tab(),
        _data_browser_tab(),
        _tools(),
        _tips(),
    ]
    docs = load_multi_category(
        {
            tr("desktop.designer.helpCatManual"): [
                "GUI ②：终末地数据设计器",
            ],
        }
    )
    result.extend(docs)
    return result


def _overview() -> HelpSection:
    return HelpSection(
        category=tr("desktop.designer.helpCatIntro"),
        title=tr("desktop.designer.helpTitleOverview"),
        content=tr("desktop.designer.helpBodyOverview"),
    )


def _inverse_tab() -> HelpSection:
    return HelpSection(
        category=tr("desktop.designer.helpCatInverse"),
        title=tr("desktop.designer.helpTitleFeature"),
        content=tr("desktop.designer.helpBodyInverse"),
    )


def _data_editor_tab() -> HelpSection:
    return HelpSection(
        category=tr("desktop.designer.helpCatDataEdit"),
        title=tr("desktop.designer.helpTitleFeature"),
        content=tr("desktop.designer.helpBodyDataEdit"),
    )


def _data_browser_tab() -> HelpSection:
    return HelpSection(
        category=tr("desktop.designer.helpCatDataBrowse"),
        title=tr("desktop.designer.helpTitleFeature"),
        content=tr("desktop.designer.helpBodyDataBrowse"),
    )


def _tools() -> HelpSection:
    return HelpSection(
        category=tr("desktop.designer.helpCatTools"),
        title=tr("desktop.designer.helpTitleBottomTools"),
        content=tr("desktop.designer.helpBodyTools"),
    )


def _tips() -> HelpSection:
    return HelpSection(
        category=tr("desktop.designer.helpCatFaq"),
        title=tr("desktop.designer.helpTitleTips"),
        content=tr("desktop.designer.helpBodyTips"),
    )
