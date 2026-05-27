"""终末地 ComputeSheet 工厂 — 从 EndfieldContextLoader 构建声明式 UI 组件。

供 GUI 层调用：构造一个已配置好 DAG + layout + base_context 的 ComputeSheet，
调用方只需 `sheet.widget` 即可嵌入现有 GUI。

用法::

    from gui_design.shared.display_view.endfield_sheet import build_endfield_sheet
    sheet = build_endfield_sheet(char, weapon, char_level=80, weapon_level=80, trust_level=0)
    parent_layout.addWidget(sheet.widget)
    sheet.evaluate()  # 首次求值
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

_FRAMEWORK_DIR = Path(__file__).resolve().parents[4] / "framework"
_SRC_DIR = _FRAMEWORK_DIR / "src"
_ADAPTER_DIR = _FRAMEWORK_DIR / "adapters" / "endfield"

if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from calc_framework.config.adapter import AdapterPackage
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout_json

_LAYOUT_PATH = _ADAPTER_DIR / "ui" / "layout.json"


def build_endfield_sheet(
    char: dict[str, Any],
    weapon: dict[str, Any] | None,
    *,
    char_level: int = 80,
    weapon_level: int = 80,
    trust_level: int = 0,
    bonuses_kwargs: dict[str, Any] | None = None,
    parent: Any = None,
) -> ComputeSheet:
    from calculation.multiplicative_zones.dag.loader import EndfieldContextLoader

    loader = EndfieldContextLoader()
    context = loader.build_context(
        character=char,
        weapon=weapon,
        char_level=char_level,
        weapon_level=weapon_level,
        trust_level=trust_level,
        bonuses_kwargs=bonuses_kwargs or {},
    )

    pkg = _get_adapter_package()
    layout = load_layout_json(_LAYOUT_PATH.read_text(encoding="utf-8"))

    sheet = ComputeSheet(
        dag_service=pkg.dag_service,
        layout=layout,
        variables=pkg.dag_service.dag.variables,
        base_context=context,
        parent=parent,
    )
    return sheet


_ADAPTER_PACKAGE: AdapterPackage | None = None


def _get_adapter_package() -> AdapterPackage:
    global _ADAPTER_PACKAGE
    if _ADAPTER_PACKAGE is None:
        _ADAPTER_PACKAGE = AdapterPackage(_ADAPTER_DIR)
    return _ADAPTER_PACKAGE
