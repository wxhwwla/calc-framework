# SPDX-License-Identifier: AGPL-3.0
"""数据录入面板 — 按实体类型分 tab 展示，字段级查看/编辑。



数据源随「数据模板」切换：终末地 adapter/data；明日方舟 BWIKI 解析 operators.json。

"""



from __future__ import annotations



import json

import os

import sys

from pathlib import Path



_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

if _project_root not in sys.path:

    sys.path.insert(0, _project_root)



from PySide6.QtCore import Qt

from PySide6.QtWidgets import (

    QAbstractItemView,

    QComboBox,

    QFileDialog,

    QHBoxLayout,

    QLabel,

    QMessageBox,

    QPushButton,

    QSplitter,

    QTabWidget,

    QTableWidget,

    QTableWidgetItem,

    QTextEdit,

    QTreeWidget,

    QTreeWidgetItem,

    QVBoxLayout,

    QWidget,

)



from tools.designer.data_editor.profiles import (

    ADAPTER_NAME_TO_PROFILE,

    PROFILES,

    data_dir_for_profile,

)





class _EntityTab(QWidget):

    def __init__(

        self,

        entity_type: str,

        filename: str,

        columns: list[str],

        data_dir: Path,

        parent: QWidget | None = None,

    ):

        super().__init__(parent)

        self._entity_type = entity_type

        self._filename = filename

        self._columns = columns

        self._data_dir = data_dir

        self._entities: list[dict] = []

        self._build_ui()



    def _build_ui(self) -> None:

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)



        splitter = QSplitter(Qt.Orientation.Vertical)



        table_container = QWidget()

        table_layout = QVBoxLayout(table_container)

        table_layout.setContentsMargins(0, 0, 0, 0)



        self._table = QTableWidget()

        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self._table.setAlternatingRowColors(True)

        self._table.currentItemChanged.connect(self._on_select)

        table_layout.addWidget(self._table)



        self._count_label = QLabel("0 条")

        table_layout.addWidget(self._count_label)



        splitter.addWidget(table_container)



        detail_splitter = QSplitter(Qt.Orientation.Horizontal)



        self._detail_text = QTextEdit()

        self._detail_text.setPlaceholderText("选中实体后显示结构化详情…")

        self._detail_text.setReadOnly(True)

        detail_splitter.addWidget(self._detail_text)



        self._skill_tree = QTreeWidget()

        self._skill_tree.setHeaderLabels(["技能 / 段", "值"])

        self._skill_tree.setAlternatingRowColors(True)

        detail_splitter.addWidget(self._skill_tree)



        detail_splitter.setSizes([400, 400])

        splitter.addWidget(detail_splitter)

        splitter.setSizes([300, 400])



        layout.addWidget(splitter)



    def load_data(self, data: list[dict]) -> None:

        self._entities = data

        self._refresh_table()



    def load_from_file(self, path: str | Path) -> bool:

        try:

            with open(path, encoding="utf-8") as f:

                data = json.load(f)

            if isinstance(data, list):

                self._entities = data

                self._refresh_table()

                return True

        except Exception:

            pass

        return False



    def _refresh_table(self) -> None:

        self._table.setRowCount(0)

        self._table.setColumnCount(len(self._columns))

        self._table.setHorizontalHeaderLabels(self._columns)



        for row_idx, entity in enumerate(self._entities):

            self._table.insertRow(row_idx)

            for col_idx, col in enumerate(self._columns):

                val = entity.get(col, "")

                if isinstance(val, list):

                    val = f"[{len(val)} 项]"

                elif isinstance(val, float) or isinstance(val, int):

                    val = str(val)

                item = QTableWidgetItem(str(val))

                item.setData(Qt.ItemDataRole.UserRole, row_idx)

                self._table.setItem(row_idx, col_idx, item)



        self._table.horizontalHeader().setStretchLastSection(True)

        self._count_label.setText(f"{len(self._entities)} 条")



    def _on_select(self, current: QTableWidgetItem | None, _previous: QTableWidgetItem | None) -> None:

        if current is None:

            self._detail_text.clear()

            self._skill_tree.clear()

            return

        row = current.data(Qt.ItemDataRole.UserRole)

        if row is None or row < 0 or row >= len(self._entities):

            return

        entity = self._entities[row]

        self._show_detail(entity)



    def _show_detail(self, entity: dict) -> None:

        lines: list[str] = []

        for key, val in entity.items():

            if key == "技能":

                continue

            if isinstance(val, list):

                if all(isinstance(v, (int, float)) for v in val):

                    if len(val) <= 10:

                        lines.append(f"{key}: {val}")

                    else:

                        lines.append(f"{key}: [{len(val)} 级], 范围 {val[0]}~{val[-1]}")

                else:

                    lines.append(f"{key}: [{len(val)} 项]")

            elif isinstance(val, dict):

                lines.append(f"{key}: {{{len(val)} 字段}}")

            else:

                lines.append(f"{key}: {val}")

        self._detail_text.setPlainText("\n".join(lines))



        self._skill_tree.clear()

        skills = entity.get("技能", [])

        if not skills:

            root = QTreeWidgetItem(self._skill_tree, ["（无技能）", ""])

            return

        for sk in skills:

            sk_name = sk.get("名称", "?")

            sk_tag = sk.get("标签", "")

            sk_pct = sk.get("百分比", False)

            label = sk_name

            if sk_tag:

                label += f" ({sk_tag})"

            sk_item = QTreeWidgetItem(self._skill_tree, [label, f"百分比={sk_pct}"])

            segments = sk.get("段", [])

            for seg_idx, seg in enumerate(segments, start=1):

                rates = seg.get("倍率", [])

                dt = seg.get("伤害类型", "")

                seg_label = f"第{seg_idx}段"

                if dt:

                    seg_label += f" [{dt}]"

                if len(rates) <= 10:

                    seg_val = str(rates)

                else:

                    seg_val = f"[{len(rates)} 级] {rates[0]}~{rates[-1]}"

                seg_item = QTreeWidgetItem(sk_item, [seg_label, seg_val])



    @property

    def entities(self) -> list[dict]:

        return self._entities



    @property

    def selected_entity(self) -> dict | None:

        current = self._table.currentItem()

        if current is None:

            return None

        row = current.data(Qt.ItemDataRole.UserRole)

        if row is None or row < 0 or row >= len(self._entities):

            return None

        return self._entities[row]





class DataEditorPanel(QWidget):

    def __init__(self, parent: QWidget | None = None):

        super().__init__(parent)

        self._tabs: dict[str, _EntityTab] = {}

        self._dag_pkg: object | None = None

        self._profile_id = "endfield"

        self._build_ui()

        self._rebuild_tabs()

        self._init_dag()



    def _build_ui(self) -> None:

        layout = QVBoxLayout(self)



        toolbar = QHBoxLayout()



        toolbar.addWidget(QLabel("数据模板:"))

        self._profile_combo = QComboBox()

        for pid, prof in PROFILES.items():

            self._profile_combo.addItem(prof.label, pid)

        self._profile_combo.currentIndexChanged.connect(self._on_profile_combo_changed)

        toolbar.addWidget(self._profile_combo)



        refresh_btn = QPushButton("重新加载")

        refresh_btn.clicked.connect(self._reload_all)

        toolbar.addWidget(refresh_btn)



        save_btn = QPushButton("保存修改")

        save_btn.clicked.connect(self._save_current)

        toolbar.addWidget(save_btn)



        validate_btn = QPushButton("校验")

        validate_btn.clicked.connect(self._validate_current)

        toolbar.addWidget(validate_btn)



        import_btn = QPushButton("导入 JSON")

        import_btn.clicked.connect(self._import_json)

        toolbar.addWidget(import_btn)



        self._dag_verify_btn = QPushButton("DAG 验证")

        self._dag_verify_btn.clicked.connect(self._dag_verify)

        self._dag_verify_btn.setEnabled(False)

        toolbar.addWidget(self._dag_verify_btn)



        toolbar.addStretch()

        layout.addLayout(toolbar)



        self._tab_widget = QTabWidget()

        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self._tab_widget, stretch=1)



    def _on_profile_combo_changed(self, index: int) -> None:

        pid = self._profile_combo.itemData(index)

        if pid:

            self.set_profile(str(pid))



    def set_profile(self, profile_id: str) -> None:

        if profile_id not in PROFILES:

            profile_id = "endfield"

        if profile_id == self._profile_id and self._tabs:

            return

        self._profile_id = profile_id

        keys = list(PROFILES.keys())

        combo_idx = keys.index(profile_id)

        if self._profile_combo.currentIndex() != combo_idx:

            self._profile_combo.blockSignals(True)

            self._profile_combo.setCurrentIndex(combo_idx)

            self._profile_combo.blockSignals(False)

        self._rebuild_tabs()

        self._init_dag()



    def sync_profile_from_adapter(self, adapter_name: str) -> None:

        pid = ADAPTER_NAME_TO_PROFILE.get(adapter_name)

        if pid:

            self.set_profile(pid)



    def get_profile_id(self) -> str:

        return self._profile_id



    def _rebuild_tabs(self) -> None:

        profile = PROFILES[self._profile_id]

        data_dir = data_dir_for_profile(profile)

        self._tab_widget.clear()

        self._tabs.clear()

        for tab_name, filename, columns in profile.entity_tabs:

            tab = _EntityTab(tab_name, filename, columns, data_dir)

            self._tabs[tab_name] = tab

            self._tab_widget.addTab(tab, tab_name)

        self._auto_load()

        self._update_status()

        if self._tab_widget.count() > 0:

            self._on_tab_changed(0)



    def _data_dir(self) -> Path:

        return data_dir_for_profile(PROFILES[self._profile_id])



    def _on_tab_changed(self, index: int) -> None:

        tab_name = self._tab_widget.tabText(index) if index >= 0 else ""

        self._dag_verify_btn.setEnabled(

            tab_name == "角色" and self._profile_id == "endfield",

        )



    def _init_dag(self) -> None:

        try:

            from calc_framework.config.adapter import AdapterPackage

            adapter_path = PROFILES[self._profile_id].adapter_dir

            if adapter_path.is_dir():

                self._dag_pkg = AdapterPackage(str(adapter_path))

        except Exception:

            self._dag_pkg = None



    def _dag_verify(self) -> None:

        if self._dag_pkg is None:

            QMessageBox.warning(self, "DAG 未加载", "终末地适配器未加载，请检查 framework/games/endfield/")

            return

        idx = self._tab_widget.currentIndex()

        if idx < 0:

            return

        tab = self._tabs.get("角色")

        if not tab:

            return

        entity = tab.selected_entity

        if entity is None:

            QMessageBox.information(self, "提示", "请先在角色列表中选择一个角色")

            return



        level = 90

        char_attrs = {}

        for attr in ("基础攻击力", "力量", "敏捷", "智识", "意志"):

            arr = entity.get(attr, [])

            if isinstance(arr, list) and len(arr) >= level:

                char_attrs[attr] = float(arr[level - 1])



        context = {

            "character": {

                "基础攻击": char_attrs.get("基础攻击力", 0),

                "力量": char_attrs.get("力量", 0),

                "敏捷": char_attrs.get("敏捷", 0),

                "智识": char_attrs.get("智识", 0),

                "意志": char_attrs.get("意志", 0),

                "暴击率": 0.05,

                "暴击伤害": 1.5,

            },

            "weapon": {

                "基础攻击": 0,

                "攻击力+": 0,

                "附加攻击力+": 0,

            },

            "equipment": {

                "攻击力平值": 0,

            },

            "enemy": {

                "防御": 100,

            },

            "computed": {

                "主能力平值加算": 0,

                "副能力平值加算": 0,

                "主能力百分比": 0,

                "副能力百分比": 0,

                "技能倍率": 1.0,

                "伤害加成": 0,

                "伤害减免": 0,

                "增幅": 0,

                "虚弱": 0,

                "庇护": 0,

                "脆弱": 0,

                "易伤": 0,

                "失衡易伤": 0,

                "抗性": 0,

                "非主控减伤": 0,

                "连击增伤": 0,

                "特殊乘区": 0,

                "力量加成值": 0,

                "敏捷加成值": 0,

                "智识加成值": 0,

                "意志加成值": 0,

            },

        }



        try:

            result = self._dag_pkg.dag_service.evaluate(context)

            lines = [f"=== DAG 验证结果: {entity.get('名称', '?')} Lv.{level} ===", ""]

            for out_name, out_val in result.outputs.items():

                lines.append(f"  {out_name}: {out_val:.4f}" if isinstance(out_val, float) else f"  {out_name}: {out_val}")

            lines.append("")

            lines.append("--- 全部节点值 ---")

            node_items = sorted(result.node_values.items(), key=lambda x: x[0])

            for node_id, val in node_items:

                lines.append(f"  {node_id}: {val:.4f}" if isinstance(val, float) else f"  {node_id}: {val}")

            QMessageBox.information(self, "DAG 验证", "\n".join(lines))

        except Exception as e:

            QMessageBox.critical(self, "DAG 求值失败", str(e))



    def _auto_load(self) -> None:

        for tab_name, tab in self._tabs.items():

            filepath = self._data_dir() / tab._filename

            if filepath.exists():

                tab.load_from_file(filepath)

        self._update_status()



    def _reload_all(self) -> None:

        self._auto_load()

        QMessageBox.information(self, "重载完成", "已重新加载所有数据")



    def _save_current(self) -> None:

        idx = self._tab_widget.currentIndex()

        if idx < 0:

            return

        tab_name = self._tab_widget.tabText(idx)

        tab = self._tabs.get(tab_name)

        if not tab:

            return

        filepath = self._data_dir() / tab._filename

        try:

            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w", encoding="utf-8") as f:

                json.dump(tab.entities, f, ensure_ascii=False, indent=2)

            QMessageBox.information(self, "保存成功", f"已保存到 {filepath}")

        except Exception as e:

            QMessageBox.critical(self, "保存失败", str(e))



    def _validate_current(self) -> None:

        from tools.data_pipeline.validators.schema_check import validate_all



        idx = self._tab_widget.currentIndex()

        if idx < 0:

            return

        tab_name = self._tab_widget.tabText(idx)

        tab = self._tabs.get(tab_name)

        if not tab:

            return

        entities = tab.entities

        errors = validate_all(entities)

        has_err = False

        lines: list[str] = []

        for idx_e, errs in errors:

            if errs:

                name = entities[idx_e].get("名称", f"[{idx_e}]")

                lines.append(f"✗ {name}:")

                for e in errs:

                    lines.append(f"    - {e}")

                has_err = True

        if has_err:

            QMessageBox.warning(self, "校验结果", "\n".join(lines) if lines else "有错误")

        else:

            QMessageBox.information(self, "校验通过", f"{len(entities)} 条数据合法")



    def _import_json(self) -> None:

        path, _ = QFileDialog.getOpenFileName(

            self, "导入 JSON", "", "JSON Files (*.json);;All Files (*)"

        )

        if not path:

            return

        idx = self._tab_widget.currentIndex()

        if idx < 0:

            return

        tab_name = self._tab_widget.tabText(idx)

        tab = self._tabs.get(tab_name)

        if not tab:

            return

        if tab.load_from_file(path):

            QMessageBox.information(self, "导入成功", f"已导入 {len(tab.entities)} 条到「{tab_name}」")

        else:

            QMessageBox.warning(self, "导入失败", "文件格式错误或为空")



    def _update_status(self) -> None:

        counts = []

        for tab_name, tab in self._tabs.items():

            counts.append(f"{tab_name}: {len(tab.entities)}")

        self.setWindowTitle("数据编辑器 — " + " | ".join(counts))



    def get_data_files(self) -> dict[str, list]:

        result: dict[str, list] = {}

        for tab_name, tab in self._tabs.items():

            stem = Path(tab._filename).stem

            key = stem.removesuffix("_standard") if stem.endswith("_standard") else stem

            result[key] = tab.entities

        return result

