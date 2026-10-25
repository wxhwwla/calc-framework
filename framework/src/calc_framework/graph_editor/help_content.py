# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""帮助文档内容 — 集中管理所有使用说明文本。"""

from __future__ import annotations

from dataclasses import dataclass, field

from calc_framework.ui.i18n import tr


@dataclass
class HelpSection:
    """帮助文档中的一个分类。"""

    category: str
    title: str
    content: str
    sub_sections: list[HelpSection] = field(default_factory=list)


# 在定义 HelpSection 之后再导入 help_menu，避免循环导入
from .help_menu import (
    _compilation,
    _config,
    _file_ops,
    _format,
    _operations,
    _preview,
    _shortcuts,
)
from .help_nodes import _node_types


def build_help_tree() -> list[HelpSection]:
    """构建完整的帮助文档树。"""
    return [
        _overview(),
        _interface(),
        _node_types(),
        _operations(),
        _file_ops(),
        _preview(),
        _shortcuts(),
        _config(),
        _compilation(),
        _format(),
    ]


def _overview() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCatIntro"),
        title=tr("desktop.graphEditor.helpTitleOverview"),
        content=tr("desktop.graphEditor.helpBodyOverview"),
    )


def _interface() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCatIntro"),
        title=tr("desktop.graphEditor.helpTitleInterface"),
        content=tr("desktop.graphEditor.helpBodyInterface"),
    )
