# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""帮助文档 — 菜单、操作、快捷键、文件、配置等说明。"""

from calc_framework.ui.i18n import tr

from .help_content import HelpSection


def _operations() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryOps"),
        title=tr("desktop.graphEditor.helpBasicOps"),
        content=tr("desktop.graphEditor.helpBodyOps"),
    )


def _file_ops() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryFile"),
        title=tr("desktop.graphEditor.helpFileOps"),
        content=tr("desktop.graphEditor.helpBodyFile"),
    )


def _preview() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryPreview"),
        title=tr("desktop.graphEditor.helpLivePreview"),
        content=tr("desktop.graphEditor.helpBodyPreview"),
    )


def _shortcuts() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryShortcuts"),
        title=tr("desktop.graphEditor.helpShortcuts"),
        content=tr("desktop.graphEditor.helpBodyShortcuts"),
    )


def _config() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryAdvanced"),
        title=tr("desktop.graphEditor.helpNodeConfig"),
        content=tr("desktop.graphEditor.helpBodyNodeConfig"),
    )


def _compilation() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryAdvanced"),
        title=tr("desktop.graphEditor.helpCompilation"),
        content=tr("desktop.graphEditor.helpBodyCompilation"),
    )


def _format() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryFormat"),
        title=tr("desktop.graphEditor.helpJsonFormat"),
        content=tr("desktop.graphEditor.helpBodyJsonFormat"),
    )
