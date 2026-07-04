# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 渲染/重建逻辑 Mixin。"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, cast

from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QMessageBox,
    QSpinBox,
    QWidget,
)

from ..dag.schema import DAGVariable
from ..dag.serializer import dag_from_dict
from ..dag.service import DAGService
from .compute_sheet import ComputeSheet
from .layout import load_layout
from .viewer_pack_utils import (
    _FALLBACK_DEFAULTS,
    _SOURCE_TO_DATA_FILE,
    extract_assets_from_calcpack,
    load_calcpack,
    resolve_asset_paths_in_layout,
)


class CalcPackViewerRenderMixin:
    """CalcPackViewer 渲染与数据重建 Mixin。"""

    # Mixin 属性占位 — 由 CalcPackViewer 提供（Pylance 类型识别）
    _loaded_data: dict[str, Any]
    _dag_service: Any
    _layout: Any
    _variables: dict[str, Any]
    _theme_manager: Any
    _data_files: dict[str, list[Any]]
    _compute_sheet: Any
    _entity_selectors: dict[str, Any]
    _level_spin: Any
    _current_level: int
    _entity_data: dict[str, dict[str, Any]]
    _splitter: Any
    _entity_group: Any
    _right_panel: Any
    _asset_temp_dir: Any
    _calcpack_path: str | None
    _entity_form: Any
    _sheet_layout: Any
    _info_name: Any
    _info_game: Any
    _info_version: Any
    _info_vars: Any
    _info_outputs: Any
    _status_label: Any
    _progress: Any
    _sheet_container: Any
    _left_layout: Any
    _scroll: Any

    def load_calcpack(self, path: str | Path) -> None:
        """加载 .calcpack 文件并渲染 UI。"""
        try:
            self._loaded_data = load_calcpack(path)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))  # type: ignore[arg-type]
            return

        self._calcpack_path = str(path)

        asset_map: dict[str, str] = {}

        if self._asset_temp_dir:
            self._asset_temp_dir.cleanup()
            self._asset_temp_dir = None

        temp_dir = tempfile.TemporaryDirectory(prefix="calcpack_assets_")
        self._asset_temp_dir = temp_dir
        asset_map = extract_assets_from_calcpack(path, temp_dir.name)

        meta = self._loaded_data.get("meta.json", {})
        self._info_name.setText(meta.get("name", "—"))
        self._info_game.setText(meta.get("game", "—"))
        self._info_version.setText(meta.get("version", "—"))

        dag_data = self._loaded_data.get("dag/formula.dag.json")
        if not dag_data:
            QMessageBox.critical(self, "加载失败", ".calcpack 缺少 dag/formula.dag.json")  # type: ignore[arg-type]
            return

        dag = dag_from_dict(dag_data)
        self._dag_service = DAGService(dag)
        self._variables = dag.variables

        layout_data = self._loaded_data.get("ui/layout.json")
        if not layout_data:
            QMessageBox.critical(self, "加载失败", ".calcpack 缺少 ui/layout.json")  # type: ignore[arg-type]
            return

        if asset_map:
            layout_data = resolve_asset_paths_in_layout(layout_data, asset_map)

        self._layout = load_layout(layout_data)

        calcpack_theme = self._loaded_data.get("ui/theme.json", {})
        if calcpack_theme:
            self._theme_manager.register("calcpack", calcpack_theme)
            self._theme_manager.switch("calcpack")

        self._data_files = {}
        for arcname, data in self._loaded_data.items():
            if arcname.startswith("data/") and isinstance(data, list):
                key = arcname.replace("data/", "").replace(".json", "")
                self._data_files[key] = data

        self._info_vars.setText(str(len(self._variables)))
        self._info_outputs.setText(str(len(dag.outputs)))

        self._rebuild_entity_selectors()
        self._rebuild_sheet()
        self._apply_theme()

        name = meta.get("name", Path(path).stem)
        self.setWindowTitle(f"{name} — 计算包查看器")
        self._status_label.setText(f"已加载 {name} ({len(self._variables)} 变量, {len(dag.outputs)} 输出)")

    def _rebuild_entity_selectors(self) -> None:
        """重建实体选择下拉菜单和等级输入框。"""
        while self._entity_form.count():
            item = self._entity_form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._entity_selectors.clear()
        self._entity_data.clear()

        level_box = QSpinBox()
        level_box.blockSignals(True)
        level_box.setRange(1, 100)
        level_box.setValue(90)
        level_box.blockSignals(False)
        level_box.valueChanged.connect(self._on_entity_changed)
        self._level_spin = level_box
        self._entity_form.addRow("等级:", level_box)

        for source_prefix, data_key in _SOURCE_TO_DATA_FILE.items():
            entities = self._data_files.get(data_key, [])
            if not entities:
                continue

            names = [e.get("名称", f"未命名 {i}") for i, e in enumerate(entities)]
            combo = QComboBox()
            combo.blockSignals(True)
            combo.addItems(names)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            combo.currentIndexChanged.connect(self._on_entity_changed)
            self._entity_selectors[source_prefix] = combo
            self._entity_data[source_prefix] = {n: e for n, e in zip(names, entities)}

            label = {"character": "角色", "weapon": "武器", "equipment": "装备"}.get(source_prefix, source_prefix)
            self._entity_form.addRow(f"{label}:", combo)

    def _rebuild_sheet(self) -> None:
        """重建 ComputeSheet 控件（加载新 .calcpack 后调用）。"""
        while self._sheet_layout.count():
            item = self._sheet_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._dag_service or not self._layout:
            self._sheet_layout.addWidget(QLabel("请先打开一个 .calcpack 文件"))
            return

        base_context: dict[str, Any] = self._build_current_context()

        patched_vars: dict[str, DAGVariable] = {}
        for path, var in self._variables.items():
            source = var.source if hasattr(var, "source") else ""
            if source == "computed" and self._is_var_in_input_sections(path):
                parts = path.split(".", 1)
                field_name = parts[1] if len(parts) == 2 else ""
                fallback = _FALLBACK_DEFAULTS.get(field_name, 0.0)
                patched_vars[path] = DAGVariable(
                    type=var.type,
                    source="user_input",
                    description=var.description,
                    default=var.default if var.default is not None else fallback,
                    min=var.min,
                    max=var.max,
                )
            else:
                patched_vars[path] = var

        self._compute_sheet = ComputeSheet(
            dag_service=self._dag_service,
            layout=self._layout,
            variables=patched_vars,
            base_context=base_context,
            parent=self._sheet_container,
        )
        self._sheet_layout.addWidget(self._compute_sheet.widget)
        self._sheet_layout.addStretch()
        self._compute_sheet.evaluate()

    def _is_var_in_input_sections(self, path: str) -> bool:
        """检查 DAG 变量路径是否属于 layout.json 的 inputs 区域。"""
        if not self._layout:
            return False
        return any(sec.type == "inputs" and path in sec.variables for sec in self._layout.sections)

    def _build_current_context(self) -> dict[str, Any]:
        """根据当前选中的实体和等级构建 DAG context，缺失变量使用 0.0。"""
        from .viewer_evaluator import build_viewer_context

        level = self._level_spin.value() if self._level_spin else 90
        # 从 Qt combo 提取当前选中名称 → {source_prefix: name}
        selected: dict[str, str] = {}
        for source_prefix, combo in self._entity_selectors.items():
            if combo.currentIndex() >= 0:
                selected[source_prefix] = combo.currentText()
        return build_viewer_context(
            entity_selectors=selected,
            entity_data=self._entity_data,
            variables=self._variables,
            level=level,
        )

    def _apply_theme(self) -> None:
        """应用当前选中的主题样式。"""
        try:
            stylesheet = self._theme_manager.stylesheet()
            self.setStyleSheet(stylesheet)
            theme = self._theme_manager.get_theme(self._theme_manager.current_name)
            if theme:
                from ._qt_backend import apply_font

                apply_font(theme, cast(QWidget, self))
        except Exception:
            pass
