# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""帮助文档 — 节点类型相关说明。"""

from calc_framework.ui.i18n import tr

from .help_content import HelpSection


def _node_types() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCatNodes"),
        title=tr("desktop.graphEditor.helpTitleNodes"),
        content=tr("desktop.graphEditor.helpBodyNodes"),
        sub_sections=[
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeConst"),
                content=tr("desktop.graphEditor.helpBodyNodeConst"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeVar"),
                content=tr("desktop.graphEditor.helpBodyNodeVar"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeUserInput"),
                content=tr("desktop.graphEditor.helpBodyNodeUserInput"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeUnary"),
                content=tr("desktop.graphEditor.helpBodyNodeUnary"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeBinary"),
                content=tr("desktop.graphEditor.helpBodyNodeBinary"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeCondition"),
                content=tr("desktop.graphEditor.helpBodyNodeCondition"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeOutput"),
                content=tr("desktop.graphEditor.helpBodyNodeOutput"),
            ),
            HelpSection(
                category=tr("desktop.graphEditor.helpCatNodes"),
                title=tr("desktop.graphEditor.helpTitleNodeComposite"),
                content=tr("desktop.graphEditor.helpBodyNodeComposite"),
            ),
        ],
    )
