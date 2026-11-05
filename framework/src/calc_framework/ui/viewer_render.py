# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 渲染/重建逻辑 Mixin。"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..config.entity_meta import (
    EntityMetaError,
    format_detail_value,
    normalize_entity_detail,
)
from ..dag.schema import DAGVariable
from ..dag.serializer import dag_from_dict
from ..dag.service import DAGService
from ..logging import get_logger
from .compute_sheet import ComputeSheet
from .entity_cascade import option_displays, step_options
from .layout import load_layout
from .viewer_pack_utils import (
    _FALLBACK_DEFAULTS,
    _SOURCE_DISPLAY_NAMES,
    _SOURCE_TO_DATA_FILE,
    extract_assets_from_adapter_dir,
    extract_assets_from_calcpack,
    has_leveled_fields,
    load_calcpack,
    resolve_asset_paths_in_layout,
)
from .viewer_pack_utils import (
    load_adapter_dir as load_adapter_dir_data,
)

logger = get_logger(__name__)


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
    _cascade_combos: dict[str, list[Any]]
    _level_spin: Any
    _current_level: int
    _entity_data: dict[str, dict[str, Any]]
    _meta: dict[str, Any]
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
    _info_description: Any
    _status_label: Any
    _progress: Any
    _sheet_container: Any
    _left_layout: Any
    _scroll: Any
    _detail_group: Any
    _detail_value_labels: dict[str, Any]
    _detail_layout: Any

    def load_calcpack(self, path: str | Path) -> bool:
        """加载 .calcpack 文件并渲染 UI。"""
        try:
            data = load_calcpack(path)
        except Exception as e:
            self._report_load_error(str(e), show_errors=True)
            return False

        self._calcpack_path = str(path)

        self._reset_asset_temp_dir()

        temp_dir = tempfile.TemporaryDirectory(prefix="calcpack_assets_")
        self._asset_temp_dir = temp_dir
        asset_map = extract_assets_from_calcpack(path, temp_dir.name)

        return self._apply_loaded_data(
            data,
            asset_map=asset_map,
            source_path=path,
            title_suffix=" — 计算包查看器",
            source_label=".calcpack",
            show_errors=True,
        )

    def load_adapter_dir(self, adapter_dir: str | Path, *, show_errors: bool = True) -> bool:
        """直接加载适配器目录并渲染 UI（无需先打包 .calcpack）。

        Args:
            adapter_dir: 适配器包目录（含 ``meta.json``）。
            show_errors: 失败时是否弹出模态错误框；启动器同进程调用时关闭，
                以便失败后回退到子进程启动。

        Returns:
            加载并渲染成功返回 True。
        """
        try:
            data = load_adapter_dir_data(adapter_dir)
        except Exception as e:
            self._report_load_error(str(e), show_errors=show_errors)
            return False

        self._calcpack_path = ""

        self._reset_asset_temp_dir()

        temp_dir = tempfile.TemporaryDirectory(prefix="adapter_assets_")
        self._asset_temp_dir = temp_dir
        asset_map = extract_assets_from_adapter_dir(adapter_dir, temp_dir.name)

        return self._apply_loaded_data(
            data,
            asset_map=asset_map,
            source_path=adapter_dir,
            title_suffix="",
            source_label="适配器",
            show_errors=show_errors,
        )

    def _reset_asset_temp_dir(self) -> None:
        """清理上一次加载创建的临时资源目录。"""
        if self._asset_temp_dir:
            self._asset_temp_dir.cleanup()
            self._asset_temp_dir = None

    def _report_load_error(self, message: str, *, show_errors: bool) -> None:
        """显示或记录加载错误；无 GUI 场景可关闭模态框。"""
        if show_errors:
            QMessageBox.critical(cast(QWidget, self), "加载失败", message)
        else:
            logger.warning("加载失败: %s", message)

    def _apply_loaded_data(
        self,
        data: dict[str, Any],
        *,
        asset_map: dict[str, str],
        source_path: str | Path,
        title_suffix: str,
        source_label: str,
        show_errors: bool,
    ) -> bool:
        """把已解析的计算包/适配器数据渲染到窗口中。"""
        self._loaded_data = data
        self._dag_service = None
        self._layout = None

        meta = data.get("meta.json", {})
        self._meta = meta
        self._info_name.setText(meta.get("name", "—"))
        self._info_game.setText(meta.get("game", "—"))
        self._info_version.setText(meta.get("version", "—"))
        self._info_description.setText(meta.get("description", "—"))

        dag_data = data.get("dag/formula.dag.json")
        if not dag_data:
            self._report_load_error(f"{source_label} 缺少 dag/formula.dag.json", show_errors=show_errors)
            return False

        dag = dag_from_dict(dag_data)
        self._dag_service = DAGService(dag)
        self._variables = dag.variables

        layout_data = data.get("ui/layout.json")
        if not layout_data:
            self._report_load_error(f"{source_label} 缺少 ui/layout.json", show_errors=show_errors)
            return False

        if asset_map:
            layout_data = resolve_asset_paths_in_layout(layout_data, asset_map)

        self._layout = load_layout(layout_data)

        source_theme = data.get("ui/theme.json", {})
        if source_theme:
            self._theme_manager.register("calcpack", source_theme)
            self._theme_manager.switch("calcpack")
        elif self._theme_manager.current_name == "calcpack":
            self._theme_manager.switch("dark")

        self._data_files = {}
        for arcname, payload in data.items():
            if arcname.startswith("data/") and isinstance(payload, list):
                key = arcname.replace("data/", "").replace(".json", "")
                self._data_files[key] = payload

        self._info_vars.setText(str(len(self._variables)))
        self._info_outputs.setText(str(len(dag.outputs)))

        self._rebuild_entity_selectors()
        self._rebuild_detail_panel()
        self._rebuild_sheet()
        self._apply_entity_input_rules()
        self._apply_theme()

        source = Path(source_path)
        fallback = source.stem if source.is_file() else source.name
        name = meta.get("name", fallback)
        self.setWindowTitle(f"{name}{title_suffix}")
        self._status_label.setText(f"已加载 {name} ({len(self._variables)} 变量, {len(dag.outputs)} 输出)")
        return True

    def _rebuild_entity_selectors(self) -> None:
        """重建实体选择下拉菜单和等级输入框。

        支持两类选择器：

        - 普通实体源（``_SOURCE_TO_DATA_FILE``）：一个下拉列出全部实体。
        - ``meta.entity_selectors`` 声明的级联选择器：按步骤逐级过滤，
          最后一级选中记录的 ``名称`` 作为实体标识注入 DAG 命名空间。

        等级输入框只在实体数据含数值列表字段时显示；舰船/武器没有等级，
        显示等级只会造成误导。
        """
        while self._entity_form.count():
            item = self._entity_form.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self._entity_selectors.clear()
        self._cascade_combos.clear()
        self._entity_data.clear()

        self._level_spin = None
        if has_leveled_fields(self._data_files):
            level_box = QSpinBox()
            level_box.blockSignals(True)
            level_box.setRange(1, 100)
            level_box.setValue(90)
            level_box.blockSignals(False)
            level_box.valueChanged.connect(self._on_entity_changed)
            self._level_spin = level_box
            self._entity_form.addRow("等级:", level_box)

        cascaded_sources: set[str] = set()
        for config in self._meta.get("entity_selectors") or []:
            if not isinstance(config, dict):
                continue
            source = self._build_cascade_selector(config)
            if source:
                cascaded_sources.add(source)

        for source_prefix, data_key in _SOURCE_TO_DATA_FILE.items():
            if source_prefix in cascaded_sources:
                continue
            entities = self._data_files.get(data_key, [])
            if not entities:
                continue

            names = [e.get("名称", f"未命名 {i}") for i, e in enumerate(entities)]
            combo = self._make_entity_combo()
            combo.blockSignals(True)
            combo.addItems(names)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            combo.currentIndexChanged.connect(self._on_entity_changed)
            self._entity_selectors[source_prefix] = combo
            self._entity_data[source_prefix] = {n: e for n, e in zip(names, entities)}

            label = _SOURCE_DISPLAY_NAMES.get(source_prefix, source_prefix)
            self._entity_form.addRow(f"{label}:", combo)

    @staticmethod
    def _make_entity_combo() -> QComboBox:
        """创建宽度受限的实体下拉框。

        默认 sizeHint 按最长条目计算，数百条「舰船 · 武器」会把左侧面板
        撑到 800px 以上，挤压计算区。限制可见内容长度与最大宽度。
        """
        combo = QComboBox()
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(14)
        combo.setMaximumWidth(240)
        return combo

    def _build_cascade_selector(self, config: dict[str, Any]) -> str | None:
        """按 ``meta.entity_selectors`` 的一项构建级联下拉。

        Args:
            config: 含 ``source``、可选 ``data_file`` 和 ``steps`` 的配置。

        Returns:
            成功构建时返回实体源名（如 ``"weapon"``），配置无效时返回 None。
        """
        source = str(config.get("source") or "")
        steps = [step for step in config.get("steps") or [] if isinstance(step, dict) and step.get("field")]
        data_key = str(config.get("data_file") or _SOURCE_TO_DATA_FILE.get(source, ""))
        records = self._data_files.get(data_key, [])
        if not source or not steps or not records:
            return None

        self._entity_data[source] = {str(record.get("名称")): record for record in records}

        combos: list[QComboBox] = []
        selections: list[str | None] = [None] * len(steps)
        updating = False

        def populate(index: int) -> None:
            """按当前已选值重建第 index 级下拉。"""
            combo = combos[index]
            options = step_options(records, steps, selections, index)
            displays = option_displays(records, steps, selections, index)
            combo.blockSignals(True)
            combo.clear()
            for value in options:
                combo.addItem(displays.get(value, value), value)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
            selections[index] = combo.currentData() if combo.count() else None

        def on_changed(index: int) -> None:
            """上级变化时清空并重建全部下级下拉。"""
            nonlocal updating
            if updating:
                return
            updating = True
            try:
                selections[index] = combos[index].currentData()
                for downstream in range(index + 1, len(combos)):
                    selections[downstream] = None
                    populate(downstream)
            finally:
                updating = False
            self._on_entity_changed()

        for index, step in enumerate(steps):
            combo = self._make_entity_combo()
            combos.append(combo)
            label = str(step.get("label") or step.get("field"))
            self._entity_form.addRow(f"{label}:", combo)
            populate(index)
            combo.currentIndexChanged.connect(lambda _current, position=index: on_changed(position))

        self._entity_selectors[source] = combos[-1]
        self._cascade_combos[source] = combos
        return source

    def _selected_entity_names(self) -> dict[str, str]:
        """读取当前各级下拉的选中实体名。

        级联选择器最后一级显示的是 ``display_field``（如武器短名），
        实际记录名保存在 item data 中；普通下拉没有 item data，回退到文本。
        """
        selected: dict[str, str] = {}
        for source, combo in self._entity_selectors.items():
            if combo.currentIndex() < 0:
                continue
            data = combo.currentData()
            selected[source] = str(data) if data is not None else combo.currentText()
        return selected

    def _entity_source_records(self) -> dict[str, list[dict[str, Any]]]:
        """按实体源名（weapon/enemy/…）汇总数据记录，供配置校验使用。"""
        records: dict[str, list[dict[str, Any]]] = {}
        for source, data_key in _SOURCE_TO_DATA_FILE.items():
            data = self._data_files.get(data_key)
            if data:
                records[source] = data
        for config in self._meta.get("entity_selectors") or []:
            if not isinstance(config, dict):
                continue
            source = str(config.get("source") or "")
            data_key = str(config.get("data_file") or _SOURCE_TO_DATA_FILE.get(source, ""))
            data = self._data_files.get(data_key)
            if source and data:
                records[source] = data
        return records

    def _selected_entity_record(self, source: str) -> dict[str, Any] | None:
        """返回指定实体源当前选中的完整记录。"""
        name = self._selected_entity_names().get(source)
        if not name:
            return None
        return self._entity_data.get(source, {}).get(name)

    def _rebuild_detail_panel(self) -> None:
        """按 ``meta.entity_detail`` 重建左侧实体数据面板。"""
        if self._detail_layout is None:
            return
        while self._detail_layout.count():
            item = self._detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._detail_value_labels = {}
        self._detail_group = None

        raw = self._meta.get("entity_detail")
        if not raw:
            return
        try:
            detail = normalize_entity_detail(raw, self._entity_source_records())
        except EntityMetaError as exc:
            logger.warning("entity_detail 配置无效，已跳过详情面板: %s", exc)
            return
        if detail is None:
            return

        record = self._selected_entity_record(detail["source"]) or {}
        group = QGroupBox(detail["title"])
        group_layout = QVBoxLayout(group)
        for section in detail["sections"]:
            title = QLabel(section["title"])
            title.setStyleSheet("font-weight: bold;")
            group_layout.addWidget(title)
            grid = QGridLayout()
            columns = section["columns"]
            for index, field in enumerate(section["fields"]):
                row, column = divmod(index, columns)
                name_label = QLabel(field["label"])
                value_label = QLabel(format_detail_value(record.get(field["field"]), field.get("format", "")))
                value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                value_label.setWordWrap(True)
                grid.addWidget(name_label, row, column * 2)
                grid.addWidget(value_label, row, column * 2 + 1)
                self._detail_value_labels[field["field"]] = value_label
            group_layout.addLayout(grid)

        self._detail_group = group
        self._detail_layout.addWidget(group)

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
                    ui_control=getattr(var, "ui_control", {}),
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
        selected = self._selected_entity_names()
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
