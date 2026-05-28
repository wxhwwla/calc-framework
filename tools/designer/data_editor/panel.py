#!/usr/bin/env python3
"""数据录入面板 — 四层标准 schema 编辑器。

当前为骨架，后续版本将提供：
- 实体列表（角色/武器/装备/坐骑）
- 属性筛选字段自由编辑
- 技能/段 树形编辑
- CSV / JSON 导入
- 实时校验
"""

from __future__ import annotations

import json
import os
import sys

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DataEditorPanel(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._entities: list[dict] = []
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        load_btn = QPushButton("加载 JSON")
        load_btn.clicked.connect(self._load_json)
        toolbar.addWidget(load_btn)

        validate_btn = QPushButton("校验")
        validate_btn.clicked.connect(self._validate)
        toolbar.addWidget(validate_btn)

        from tools.data_pipeline.transformers.from_legacy_endfield import (
            from_characters,
        )
        migrate_chars_btn = QPushButton("从 characters.json 迁移")
        migrate_chars_btn.clicked.connect(lambda: self._migrate_chars(from_characters))
        toolbar.addWidget(migrate_chars_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._entity_list = QListWidget()
        self._entity_list.currentRowChanged.connect(self._on_select)
        splitter.addWidget(self._entity_list)

        self._editor = QTextEdit()
        self._editor.setPlaceholderText("选中实体后在此编辑 JSON...")
        splitter.addWidget(self._editor)

        splitter.setSizes([200, 500])
        layout.addWidget(splitter, stretch=1)

        status = QLabel("未加载数据")
        layout.addWidget(status)

    def _load_json(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 JSON 数据文件", "", "JSON Files (*.json);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._entities = data
            elif isinstance(data, dict):
                self._entities = [data]
            else:
                QMessageBox.warning(self, "格式错误", "JSON 顶层应为对象或对象数组")
                return
            self._refresh_list()
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))

    def _refresh_list(self) -> None:
        self._entity_list.clear()
        for e in self._entities:
            name = e.get("名称", e.get("name", "(未命名)"))
            self._entity_list.addItem(name)

    def _on_select(self, row: int) -> None:
        if 0 <= row < len(self._entities):
            text = json.dumps(self._entities[row], ensure_ascii=False, indent=2)
            self._editor.setPlainText(text)
        else:
            self._editor.clear()

    def _validate(self) -> None:
        from tools.data_pipeline.validators.schema_check import validate_all

        errors = validate_all(self._entities)
        has_err = False
        lines = []
        for idx, errs in errors:
            if errs:
                name = self._entities[idx].get("名称", f"[{idx}]")
                lines.append(f"✗ {name}:")
                for e in errs:
                    lines.append(f"    - {e}")
                has_err = True
        if has_err:
            QMessageBox.warning(self, "校验结果", "\n".join(lines) if lines else "有错误")
        else:
            QMessageBox.information(self, "校验通过", f"{len(self._entities)} 条数据合法")

    def _migrate_chars(self, from_characters_func) -> None:
        path = os.path.join(
            _project_root,
            "endfield_damage_calculator",
            "character_weapon_equipment",
            "character_data",
            "characters.json",
        )
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._entities = from_characters_func(data)
            self._refresh_list()
            QMessageBox.information(self, "迁移完成", f"已加载 {len(self._entities)} 条")
        except Exception as e:
            QMessageBox.critical(self, "迁移失败", str(e))
