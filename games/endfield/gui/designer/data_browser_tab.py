#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""数据浏览页签：查看角色/武器/装备 JSON 列表。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from calc_framework.ui.i18n import tr
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[4]
_JSON_PATHS = {
    "character": _ROOT / "adapters" / "endfield" / "data" / "character_data" / "characters.json",
    "weapon": _ROOT / "adapters" / "endfield" / "data" / "weapon_data" / "weapons.json",
    "equipment": _ROOT / "adapters" / "endfield" / "data" / "equipments.json",
}

_KIND_LABEL_KEYS = (
    ("character", "desktop.designer.kindCharacter"),
    ("weapon", "desktop.designer.kindWeapon"),
    ("equipment", "desktop.designer.kindEquipment"),
)

_STYLE = """

    QTextEdit { background-color: #1E1E1E; color: #D1D1D1;

                border: 1px solid #464646; border-radius: 4px;

                font-family: Consolas, monospace; font-size: 12px; }

"""


class DataBrowserTab(QWidget):
    def __init__(self, big_font: QFont, small_font: QFont) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        row = QHBoxLayout()

        label = QLabel(tr("desktop.designer.dataKindLabel"))

        label.setFont(small_font)

        label.setStyleSheet("color: #CCCCCC;")

        row.addWidget(label)

        self.kind_combo = QComboBox()

        for kind_id, label_key in _KIND_LABEL_KEYS:
            self.kind_combo.addItem(tr(label_key), kind_id)

        self.kind_combo.currentIndexChanged.connect(self._load)

        row.addWidget(self.kind_combo)

        row.addStretch()

        layout.addLayout(row)

        self.text_edit = QTextEdit()

        self.text_edit.setReadOnly(True)

        self.text_edit.setStyleSheet(_STYLE)

        layout.addWidget(self.text_edit)

        self._load()

    def _load(self) -> None:
        kind = self.kind_combo.currentData()

        try:
            json_path = _JSON_PATHS.get(str(kind or ""))

            if json_path and json_path.is_file():
                with json_path.open(encoding="utf-8") as f:
                    data = json.load(f)

                names = [item.get("名称", "?") for item in data]

                text = (
                    tr("desktop.designer.browserCountFmt", n=len(names)) + "\n" + "\n".join(f"  - {n}" for n in names)
                )

            else:
                text = tr("desktop.designer.browserFileMissing")

        except Exception as e:
            _logger.warning("JSON 数据加载失败: %s", e)
            text = tr("desktop.designer.browserLoadFailed", error=str(e))

        self.text_edit.setPlainText(text)
