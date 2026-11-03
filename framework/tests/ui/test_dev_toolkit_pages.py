# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""P2-07：``dev_toolkit.pages`` 拆分后的结构与行为门禁。

页面按符号边界拆到独立模块后，聚合模块只负责注册；行数门禁
防止 1000+ 行的 ``pages.py`` 回流。
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

_PAGE_MODULES = (
    "calc_framework.dev_toolkit.pages",
    "calc_framework.dev_toolkit.pages_common",
    "calc_framework.dev_toolkit.pages_config",
    "calc_framework.dev_toolkit.pages_graph_editor",
    "calc_framework.dev_toolkit.pages_graph_preview",
    "calc_framework.dev_toolkit.pages_tools",
)

_NON_GRAPH_MODULES = (
    "calc_framework.dev_toolkit.pages",
    "calc_framework.dev_toolkit.pages_common",
    "calc_framework.dev_toolkit.pages_config",
    "calc_framework.dev_toolkit.pages_graph_preview",
    "calc_framework.dev_toolkit.pages_tools",
)

_EXPECTED_PAGE_IDS = {
    "new_adapter",
    "data_editor",
    "layout_editor",
    "export_pack",
    "graph_editor",
    "dag_debugger",
    "calcpack_viewer",
    "ai_generator",
    "ocr_label",
}


def _line_count(module_name: str) -> int:
    module = importlib.import_module(module_name)
    module_file = module.__file__
    assert module_file is not None
    return len(Path(module_file).read_text(encoding="utf-8").splitlines())


@pytest.mark.parametrize("module_name", _PAGE_MODULES)
def test_page_module_stays_within_hard_cap(module_name: str) -> None:
    assert _line_count(module_name) <= 500


@pytest.mark.parametrize("module_name", _NON_GRAPH_MODULES)
def test_non_graph_modules_stay_within_target(module_name: str) -> None:
    assert _line_count(module_name) <= 400


def test_aggregator_module_stays_small() -> None:
    assert _line_count("calc_framework.dev_toolkit.pages") <= 120


def test_page_registry_contains_all_page_ids() -> None:
    importlib.import_module("calc_framework.dev_toolkit.pages")
    from calc_framework.dev_toolkit.main_window import _PAGE_REGISTRY

    assert set(_PAGE_REGISTRY) >= _EXPECTED_PAGE_IDS


def test_page_classes_are_owned_by_split_modules() -> None:
    from calc_framework.dev_toolkit import pages, pages_config, pages_graph_editor, pages_tools

    assert pages._NewAdapterPage is pages_config._NewAdapterPage
    assert pages._DataEditorPage is pages_config._DataEditorPage
    assert pages._LayoutEditorPage is pages_config._LayoutEditorPage
    assert pages._ExportPage is pages_config._ExportPage
    assert pages._GraphEditorPage is pages_graph_editor._GraphEditorPage
    assert pages._DebuggerPage is pages_tools._DebuggerPage
    assert pages._ViewerPage is pages_tools._ViewerPage
    assert pages._GeneratorPage is pages_tools._GeneratorPage
    assert pages._OcrPage is pages_tools._OcrPage


def _node_item(
    node_type: str,
    *,
    path: str = "",
    default: object = None,
    value: object = None,
    label: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        node_id="n1",
        to_graph_node=lambda: SimpleNamespace(
            type=node_type,
            label=label,
            config=SimpleNamespace(path=path, default=default, value=value),
        ),
    )


def test_preview_text_for_reference_node() -> None:
    from calc_framework.dev_toolkit.pages_graph_preview import preview_text_for_node

    assert preview_text_for_node(MagicMock(), _node_item("var", path="a.b")) == "引用: a.b"


def test_preview_text_for_reference_node_without_path() -> None:
    from calc_framework.dev_toolkit.pages_graph_preview import preview_text_for_node

    assert preview_text_for_node(MagicMock(), _node_item("var")) == "(未设置路径)"


def test_preview_text_for_user_input_node() -> None:
    from calc_framework.dev_toolkit.pages_graph_preview import preview_text_for_node

    assert preview_text_for_node(MagicMock(), _node_item("user_input", default=1.5)) == "默认值: 1.5"


def test_preview_text_for_const_node() -> None:
    from calc_framework.dev_toolkit.pages_graph_preview import preview_text_for_node

    assert preview_text_for_node(MagicMock(), _node_item("const", value=42)) == "42"
