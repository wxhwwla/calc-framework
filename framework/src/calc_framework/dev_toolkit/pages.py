# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""开发者工具箱 — 各工具页面适配器注册。

具体页面实现按领域拆到 ``pages_config`` / ``pages_graph_editor`` /
``pages_tools``；本模块只负责聚合注册。``from . import pages`` 的
副作用（向 ``_PAGE_REGISTRY`` 注册全部页面）与拆分前保持一致。
"""

from __future__ import annotations

from .main_window import _register_page
from .pages_config import (
    _DataEditorPage,
    _ExportPage,
    _LayoutEditorPage,
    _NewAdapterPage,
)
from .pages_graph_editor import _GraphEditorPage
from .pages_tools import (
    _DebuggerPage,
    _GeneratorPage,
    _OcrPage,
    _ViewerPage,
)

_register_page("new_adapter", _NewAdapterPage)
_register_page("data_editor", _DataEditorPage)
_register_page("layout_editor", _LayoutEditorPage)
_register_page("export_pack", _ExportPage)
_register_page("graph_editor", _GraphEditorPage)
_register_page("dag_debugger", _DebuggerPage)
_register_page("calcpack_viewer", _ViewerPage)
_register_page("ai_generator", _GeneratorPage)
_register_page("ocr_label", _OcrPage)
