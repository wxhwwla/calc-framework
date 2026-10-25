# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""计算器内置说明书内容。"""

from __future__ import annotations

from calc_framework.ui.i18n import tr

from utils.gui.help_dialog import HelpSection
from utils.gui.help_loader import load_multi_category


def build_calculator_help() -> list[HelpSection]:
    result = [
        _overview(),
        _main_tab(),
        _advanced_tab(),
        _search(),
        _features(),
        _nga_mechanics(),
        _tips(),
    ]
    docs = load_multi_category(
        {
            tr("desktop.endfield.helpCatManual"): [
                "GUI ⑤：终末地伤害计算器",
                "数据结构与文件格式",
            ],
        }
    )
    result.extend(docs)
    return result


def _overview() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatIntro"),
        title=tr("desktop.endfield.helpTitleOverview"),
        content=tr("desktop.endfield.helpBodyOverview"),
    )


def _main_tab() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatMain"),
        title=tr("desktop.endfield.helpTitleMainLayout"),
        content=tr("desktop.endfield.helpBodyMainLayout"),
        sub_sections=[
            HelpSection(
                category=tr("desktop.endfield.helpCatMain"),
                title=tr("desktop.endfield.helpTitleMainOps"),
                content=tr("desktop.endfield.helpBodyMainOps"),
            ),
            HelpSection(
                category=tr("desktop.endfield.helpCatMain"),
                title=tr("desktop.endfield.helpTitleCharParams"),
                content=tr("desktop.endfield.helpBodyCharParams"),
            ),
            HelpSection(
                category=tr("desktop.endfield.helpCatMain"),
                title=tr("desktop.endfield.helpTitleWeaponParams"),
                content=tr("desktop.endfield.helpBodyWeaponParams"),
            ),
        ],
    )


def _advanced_tab() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatAdvanced"),
        title=tr("desktop.endfield.helpTitleAdvOverview"),
        content=tr("desktop.endfield.helpBodyAdvancedOverview"),
        sub_sections=[
            HelpSection(
                category=tr("desktop.endfield.helpCatAdvanced"),
                title=tr("desktop.endfield.helpTitleAdvSearch"),
                content=tr("desktop.endfield.helpBodyFullSearch"),
            ),
            HelpSection(
                category=tr("desktop.endfield.helpCatAdvanced"),
                title=tr("desktop.endfield.helpTitleAdvMulti"),
                content=tr("desktop.endfield.helpBodyMultiSkill"),
            ),
        ],
    )


def _search() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatSearch"),
        title=tr("desktop.endfield.helpTitleSearchModes"),
        content=tr("desktop.endfield.helpBodySearchModes"),
    )


def _features() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatFeatures"),
        title=tr("desktop.endfield.helpTitleFeatures"),
        content=tr("desktop.endfield.helpBodyFeatures"),
    )


def _nga_mechanics() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatMechanics"),
        title=tr("desktop.endfield.helpTitleNga"),
        content=tr("desktop.endfield.helpBodyNga"),
    )


def _tips() -> HelpSection:
    return HelpSection(
        category=tr("desktop.endfield.helpCatFaq"),
        title=tr("desktop.endfield.helpTitleTips"),
        content=tr("desktop.endfield.helpBodyTips"),
    )
