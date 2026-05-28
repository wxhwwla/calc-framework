#!/usr/bin/env python3
"""数据浏览页签：查看角色/武器/装备 JSON 列表。"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

_JSON_PATHS = {
    "角色": Path(__file__).resolve().parents[3] / "character_weapon_equipment" / "character_data" / "characters.json",
    "武器": Path(__file__).resolve().parents[3] / "character_weapon_equipment" / "weapon_data" / "weapons.json",
    "装备": Path(__file__).resolve().parents[3] / "character_weapon_equipment" / "equipments.json",
}

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
        label = QLabel("数据类型：")
        label.setFont(small_font)
        label.setStyleSheet("color: #CCCCCC;")
        row.addWidget(label)

        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["角色", "武器", "装备"])
        self.kind_combo.currentTextChanged.connect(self._load)
        row.addWidget(self.kind_combo)
        row.addStretch()
        layout.addLayout(row)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(_STYLE)
        layout.addWidget(self.text_edit)

        self._load()

    def _load(self) -> None:
        kind = self.kind_combo.currentText()
        try:
            json_path = _JSON_PATHS.get(kind)
            if json_path and json_path.is_file():
                with json_path.open(encoding="utf-8") as f:
                    data = json.load(f)
                names = [item.get("名称", "?") for item in data]
                text = f"共 {len(names)} 条\n" + "\n".join(f"  - {n}" for n in names)
            else:
                text = "数据文件未找到"
        except Exception as e:
            text = f"加载失败: {e}"
        self.text_edit.setPlainText(text)
