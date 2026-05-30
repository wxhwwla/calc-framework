"""CalcPackViewer — 通用用户展示层。

加载 .calcpack 文件并渲染完整的交互式计算界面。
支持实体选择（角色/武器/装备）、自定义输入、实时 DAG 求值。

用法::

    python -m calc_framework.ui.viewer path/to/game.calcpack
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from calc_framework.dag.schema import DAGVariable
from calc_framework.dag.serializer import dag_from_dict
from calc_framework.dag.service import DAGService
from calc_framework.ui.compute_sheet import ComputeSheet
from calc_framework.ui.layout import load_layout, Layout
from calc_framework.ui.theme import ThemeManager

_VARIABLE_FIELD_MAP: dict[str, str] = {
    "基础攻击力": "基础攻击",
}

_SOURCE_TO_DATA_FILE: dict[str, str] = {
    "character": "characters",
    "weapon": "weapons",
    "equipment": "equipments",
}

_DATA_FILE_TO_SOURCE: dict[str, str] = {
    "characters": "character",
    "weapons": "weapon",
    "equipments": "equipment",
}

_FALLBACK_DEFAULTS: dict[str, float] = {
    "技能倍率": 1.0,
    "伤害加成": 0.0,
    "伤害减免": 0.0,
    "增幅": 0.0,
    "虚弱": 0.0,
    "庇护": 0.0,
    "脆弱": 0.0,
    "易伤": 0.0,
    "失衡易伤": 0.0,
    "抗性": 0.0,
    "非主控减伤": 0.0,
    "连击增伤": 0.0,
    "特殊乘区": 1.0,
    "主能力平值加算": 0.0,
    "副能力平值加算": 0.0,
    "主能力百分比": 0.0,
    "副能力百分比": 0.0,
    "力量加成值": 0.0,
    "敏捷加成值": 0.0,
    "智识加成值": 0.0,
    "意志加成值": 0.0,
    "防御": 100.0,
    "暴击率": 0.05,
    "暴击伤害": 0.5,
}


def _load_calcpack(path: str | Path) -> dict[str, Any]:
    """加载 .calcpack 文件，返回内部文件映射 {arcname: raw_bytes}。"""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f".calcpack 文件未找到: {p}")
    result: dict[str, Any] = {}
    with zipfile.ZipFile(p, "r") as zf:
        for name in zf.namelist():
            raw = zf.read(name)
            if name.endswith(".json"):
                result[name] = json.loads(raw.decode("utf-8"))
            else:
                result[name] = raw
    return result


_ASSETS_DIR = "assets/"


def _extract_assets_from_calcpack(pack_path: str | Path, target_dir: str | Path) -> dict[str, str]:
    """从 .calcpack 中提取 assets/ 文件到目标目录。

    Returns:
        {ZIP 内路径: 解压后完整路径} 的映射。
    """
    result: dict[str, str] = {}
    target = Path(target_dir)
    with zipfile.ZipFile(str(pack_path), "r") as zf:
        for name in zf.namelist():
            if name.startswith(_ASSETS_DIR) and not name.endswith("/"):
                dest = target / name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                result[name] = str(dest)
    return result


def _resolve_asset_paths_in_layout(layout_data: dict[str, Any], asset_map: dict[str, str]) -> dict[str, Any]:
    """将 layout 中的 assets/ 路径替换为解压后的实际文件路径。"""
    patched = json.loads(json.dumps(layout_data))
    sections = patched.get("sections", [])
    for sec in sections:
        if sec.get("widget_type") == "donation":
            cfg = sec.get("widget_config", {})
            raw = cfg.get("image_path", "")
            if raw in asset_map:
                cfg["image_path"] = asset_map[raw]
            elif raw.startswith(_ASSETS_DIR) and raw in asset_map:
                cfg["image_path"] = asset_map[raw]
    return patched


def _resolve_field_name(field: str) -> str:
    """将实体数据字段名映射为 DAG context 字段名。

    例如 "基础攻击力" → "基础攻击"（Endfield 命名差异）。
    通用情况下直接返回原字段名。
    """
    return _VARIABLE_FIELD_MAP.get(field, field)


def _build_context_from_entity(
    entity: dict[str, Any],
    namespace: str,
    level: int = 90,
) -> dict[str, float]:
    """从实体数据构建 context 命名空间字典。

    level 为 1-indexed（1 = 最低等级）。
    """
    ctx: dict[str, float] = {}
    for key, val in entity.items():
        if key in ("名称", "技能", "_entity_type", "类型", "星级", "武器",
                   "主能力", "副能力", "装备种类", "部位", "稀有度",
                   "所属套组", "套装", "属性词条", "效果", "三件套效果", "_source",
                   "等级", "潜能", "信赖", "信赖加成"):
            continue
        if isinstance(val, list) and all(isinstance(v, (int, float)) for v in val):
            idx = min(level, len(val)) - 1
            resolved = _resolve_field_name(key)
            ctx[resolved] = float(val[idx])
        elif isinstance(val, (int, float)):
            resolved = _resolve_field_name(key)
            ctx[resolved] = float(val)
    return ctx


class CalcPackViewer(QMainWindow):
    """通用 .calcpack 查看器 — 加载计算包并渲染交互界面。"""

    def __init__(self, calcpack_path: str | None = None):
        super().__init__()
        self.setWindowTitle("计算包查看器")
        self.resize(1100, 750)

        self._loaded_data: dict[str, Any] = {}
        self._dag_service: DAGService | None = None
        self._layout: Layout | None = None
        self._variables: dict[str, DAGVariable] = {}
        self._theme_manager = ThemeManager()
        self._data_files: dict[str, list[dict[str, Any]]] = {}
        self._compute_sheet: ComputeSheet | None = None
        self._entity_selectors: dict[str, QComboBox] = {}
        self._level_spin: QSpinBox | None = None
        self._current_level: int = 90
        self._entity_data: dict[str, dict[str, Any]] = {}
        self._splitter: QSplitter | None = None
        self._entity_group: QGroupBox | None = None
        self._right_panel: QWidget | None = None
        self._asset_temp_dir: tempfile.TemporaryDirectory | None = None
        self._calcpack_path: str | None = calcpack_path

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self._build_menu()

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        self._left_layout = QVBoxLayout(left)
        self._left_layout.setContentsMargins(4, 4, 4, 4)
        self._entity_group = QGroupBox("选择实体")
        self._entity_form = QFormLayout(self._entity_group)
        self._left_layout.addWidget(self._entity_group)
        self._left_layout.addStretch()
        splitter.addWidget(left)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._sheet_container = QWidget()
        self._sheet_layout = QVBoxLayout(self._sheet_container)
        self._scroll.setWidget(self._sheet_container)
        splitter.addWidget(self._scroll)

        right = QWidget()
        self._right_layout = QVBoxLayout(right)
        self._right_layout.setContentsMargins(4, 4, 4, 4)
        self._info_group = QGroupBox("包信息")
        info_form = QFormLayout(self._info_group)
        self._info_name = QLabel("—")
        info_form.addRow("名称:", self._info_name)
        self._info_game = QLabel("—")
        info_form.addRow("游戏:", self._info_game)
        self._info_version = QLabel("—")
        info_form.addRow("版本:", self._info_version)
        self._info_vars = QLabel("—")
        info_form.addRow("变量:", self._info_vars)
        self._info_outputs = QLabel("—")
        info_form.addRow("输出:", self._info_outputs)
        self._right_layout.addWidget(self._info_group)
        self._right_layout.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([220, 580, 200])
        self._splitter = splitter
        main_layout.addWidget(splitter, stretch=1)

        bar = QStatusBar()
        self._status_label = QLabel("就绪 — 打开一个 .calcpack 文件开始使用")
        bar.addWidget(self._status_label)
        self._progress = QProgressBar()
        self._progress.setMaximumWidth(160)
        self._progress.setVisible(False)
        bar.addPermanentWidget(self._progress)
        self.setStatusBar(bar)

        if calcpack_path:
            path_copy = calcpack_path
            QTimer.singleShot(100, lambda p=path_copy: self.load_calcpack(p))

    def _build_menu(self) -> None:
        mb = self.menuBar()
        file_menu = mb.addMenu("文件")

        open_action = QAction("打开 .calcpack...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = mb.addMenu("工具")
        plugin_action = QAction("插件管理器...", self)
        plugin_action.triggered.connect(self._show_plugin_manager)
        tools_menu.addAction(plugin_action)

        theme_menu = mb.addMenu("主题")
        self._theme_actions: dict[str, QAction] = {}
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)
        theme_group.triggered.connect(self._on_theme_switched)
        for key in self._theme_manager.theme_names:
            display = self._theme_manager.get_theme(key).get("name", key)
            action = QAction(display, self, checkable=True)
            action.setData(key)
            if key == self._theme_manager.current_name:
                action.setChecked(True)
            theme_group.addAction(action)
            theme_menu.addAction(action)
            self._theme_actions[key] = action

        file_menu.addSeparator()
        layout_menu = mb.addMenu("布局")
        toggle_left_action = QAction("切换左侧面板", self)
        toggle_left_action.setShortcut("Ctrl+B")
        toggle_left_action.triggered.connect(self._toggle_left_panel)
        layout_menu.addAction(toggle_left_action)
        toggle_right_action = QAction("切换右侧面板", self)
        toggle_right_action.setShortcut("Ctrl+R")
        toggle_right_action.triggered.connect(self._toggle_right_panel)
        layout_menu.addAction(toggle_right_action)

        help_menu = mb.addMenu("帮助")
        help_action = QAction("使用说明", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)

    def _show_help(self) -> None:
        from utils.gui_help_dialog import HelpDialog, HelpSection
        dialog = HelpDialog(self._build_viewer_help, self, title="CalcPackViewer 使用说明")
        dialog.exec()

    @staticmethod
    def _build_viewer_help() -> list[HelpSection]:
        return [
            HelpSection(
                category="入门",
                title="概述",
                content="""\
<h2>CalcPackViewer — 配置包查看器</h2>

<p>CalcPackViewer 是通用计算展示层，用于加载 .calcpack 文件并呈现交互式计算界面。<br>
支持实体选择、自定义输入和实时 DAG 求值。</p>

<h3>启动方式</h3>
<pre>python -m calc_framework.ui path/to/game.calcpack</pre>
<p>也可以从启动器拖拽 .calcpack 文件到窗口打开。</p>

<h3>主要功能</h3>
<ul>
<li>加载并渲染 .calcpack 配置包</li>
<li>实体选择（角色/武器/装备）</li>
<li>自定义用户输入（滑块/数字框/下拉框）</li>
<li>实时 DAG 求值与结果展示</li>
<li>插件管理（导入/打包/查看插件）</li>
<li>多主题切换</li>
</ul>
""",
            ),
            HelpSection(
                category="界面",
                title="界面布局",
                content="""\
<h2>界面布局</h2>

<h3>菜单栏</h3>
<ul>
<li><b>文件</b> — 打开 .calcpack、退出</li>
<li><b>工具</b> — 插件管理器（导入/打包/刷新插件）</li>
<li><b>主题</b> — 切换界面主题（多个预设主题可选）</li>
<li><b>布局</b> — 切换左侧/右侧面板显示</li>
<li><b>帮助</b> — 使用说明</li>
</ul>

<h3>主内容区</h3>
<p>加载 .calcpack 后，根据包定义显示：</p>
<ul>
<li><b>左侧面板</b> — 实体选择（下拉框选择角色/武器等）</li>
<li><b>中间面板</b> — DAG 求值结果与用户输入控件</li>
<li><b>右侧面板</b> — 详细数据/属性展示</li>
</ul>

<h3>状态栏</h3>
<p>底部显示当前加载的配置包路径和状态信息。</p>
""",
            ),
            HelpSection(
                category="操作",
                title="操作说明",
                content="""\
<h2>操作说明</h2>

<h3>打开配置包</h3>
<ul>
<li>菜单「文件 → 打开 .calcpack」选择文件</li>
<li>拖拽 .calcpack 文件到窗口</li>
<li>启动时命令行参数指定路径</li>
</ul>

<h3>使用计算器</h3>
<ol>
<li>在左侧面板选择实体（如选择角色）</li>
<li>中间面板会显示可调参数（滑块拖拽或数字输入）</li>
<li>结果面板实时更新 DAG 求值结果</li>
</ol>

<h3>插件管理</h3>
<ol>
<li>菜单「工具 → 插件管理器」打开插件管理对话框</li>
<li>可导入 .calcplugin 插件文件</li>
<li>可打包插件目录为 .calcplugin</li>
<li>插件加载后自动生效</li>
</ol>

<h3>切换主题</h3>
<p>菜单「主题」下选择不同预设主题，界面配色和样式会实时切换。</p>
""",
            ),
            HelpSection(
                category="常见问题",
                title="常见问题",
                content="""\
<h2>使用技巧与常见问题</h2>

<h3>快捷键</h3>
<ul>
<li><b>Ctrl+O</b> — 打开 .calcpack</li>
<li><b>Ctrl+Q</b> — 退出</li>
<li><b>Ctrl+B</b> — 切换左侧面板</li>
<li><b>Ctrl+R</b> — 切换右侧面板</li>
<li><b>F1</b> — 打开此使用说明</li>
</ul>

<h3>常见问题</h3>

<p><b>Q: .calcpack 文件在哪里？</b><br>
A: .calcpack 是由配置包设计器（<code>python -m tools.designer</code>）创建的压缩包文件。</p>

<p><b>Q: 支持的插件格式？</b><br>
A: 支持 .calcplugin 插件文件，包含扩展数据和计算逻辑。</p>

<p><b>Q: 如何自定义主题？</b><br>
A: 当前版本通过主题菜单切换预设主题。自定义主题需编辑配置文件。</p>
""",
            ),
        ]

    def _on_theme_switched(self, action: QAction) -> None:
        key = action.data()
        if key:
            stylesheet = self._theme_manager.switch(key)
            self.setStyleSheet(stylesheet)
            theme = self._theme_manager.get_theme(key)
            if theme:
                self._theme_manager.apply_font(theme, self)
            self._status_label.setText(f"主题切换为: {theme.get('name', key)}")

    def _toggle_left_panel(self) -> None:
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if sizes[0] > 0:
            self._splitter.setSizes([0, sizes[0] + sizes[1] + sizes[2], 0])
        else:
            self._splitter.setSizes([220, max(400, sizes[1] - 220), max(100, sizes[2])])

    def _toggle_right_panel(self) -> None:
        if self._splitter is None:
            return
        sizes = self._splitter.sizes()
        if sizes[2] > 0:
            self._splitter.setSizes([sizes[0], sizes[0] + sizes[1] + sizes[2], 0])
        else:
            self._splitter.setSizes([max(100, sizes[0]), max(400, sizes[1] - 200), 200])

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "打开 .calcpack", "",
            "CalcPack (*.calcpack);;ZIP (*.zip);;All Files (*)",
        )
        if path:
            self.load_calcpack(path)

    def load_calcpack(self, path: str | Path) -> None:
        """加载 .calcpack 文件并渲染 UI。"""
        try:
            self._loaded_data = _load_calcpack(path)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))
            return

        self._calcpack_path = str(path)

        asset_map: dict[str, str] = {}
        if self._asset_temp_dir:
            self._asset_temp_dir.cleanup()
            self._asset_temp_dir = None
        temp_dir = tempfile.TemporaryDirectory(prefix="calcpack_assets_")
        self._asset_temp_dir = temp_dir
        asset_map = _extract_assets_from_calcpack(path, temp_dir.name)

        meta = self._loaded_data.get("meta.json", {})
        self._info_name.setText(meta.get("name", "—"))
        self._info_game.setText(meta.get("game", "—"))
        self._info_version.setText(meta.get("version", "—"))

        dag_data = self._loaded_data.get("dag/formula.dag.json")
        if not dag_data:
            QMessageBox.critical(self, "加载失败", ".calcpack 缺少 dag/formula.dag.json")
            return
        dag = dag_from_dict(dag_data)
        self._dag_service = DAGService(dag)
        self._variables = dag.variables

        layout_data = self._loaded_data.get("ui/layout.json")
        if not layout_data:
            QMessageBox.critical(self, "加载失败", ".calcpack 缺少 ui/layout.json")
            return
        if asset_map:
            layout_data = _resolve_asset_paths_in_layout(layout_data, asset_map)
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
            self._entity_data[source_prefix] = {
                n: e for n, e in zip(names, entities)
            }
            label = {"character": "角色", "weapon": "武器", "equipment": "装备"}.get(
                source_prefix, source_prefix
            )
            self._entity_form.addRow(f"{label}:", combo)

    def _rebuild_sheet(self) -> None:
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
        if not self._layout:
            return False
        for sec in self._layout.sections:
            if sec.type == "inputs" and path in sec.variables:
                return True
        return False

    def _build_current_context(self) -> dict[str, Any]:
        """根据当前选中的实体和等级构建 DAG context，缺失变量使用 0.0。"""
        ctx: dict[str, Any] = {}
        level = self._level_spin.value() if self._level_spin else 90
        for source_prefix, combo in self._entity_selectors.items():
            idx = combo.currentIndex()
            if idx < 0:
                continue
            name = combo.currentText()
            entity = self._entity_data.get(source_prefix, {}).get(name)
            if entity:
                ns = source_prefix
                ns_ctx = _build_context_from_entity(entity, ns, level)
                ctx[ns] = ns_ctx

        for path, var in self._variables.items():
            source = var.source if hasattr(var, "source") else ""
            parts = path.split(".", 1)
            if len(parts) != 2:
                continue
            ns, key = parts
            if ns not in ctx:
                ctx[ns] = {}
            if isinstance(ctx.get(ns), dict) and key not in ctx[ns]:
                default = var.default if var.default is not None else _FALLBACK_DEFAULTS.get(key, 0.0)
                ctx[ns][key] = default
        return ctx

    def _on_entity_changed(self) -> None:
        """当用户切换实体或更改等级时重新求值。"""
        if self._compute_sheet is None:
            return
        context = self._build_current_context()
        self._compute_sheet._base_context = context
        self._compute_sheet.evaluate()

        selected = []
        for src, combo in self._entity_selectors.items():
            if combo.currentIndex() >= 0:
                selected.append(f"{src}={combo.currentText()}")
        lv = self._level_spin.value() if self._level_spin else 90
        self._status_label.setText(
            f"已求值 — {', '.join(selected) if selected else '自定义输入'} Lv.{lv}"
        )

    def _apply_theme(self) -> None:
        try:
            stylesheet = self._theme_manager.stylesheet()
            self.setStyleSheet(stylesheet)
            theme = self._theme_manager.get_theme(self._theme_manager.current_name)
            if theme:
                self._theme_manager.apply_font(theme, self)
        except Exception:
            pass

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._splitter is None:
            return
        width = event.size().width()
        if width < 800:
            self._splitter.setSizes([0, width, 0])
        elif width < 1100:
            sizes = self._splitter.sizes()
            if sizes[0] > 180:
                self._splitter.setSizes([180, width - 360, 180])
        elif self._splitter.sizes()[0] == 0 and self._splitter.sizes()[2] == 0:
            self._splitter.setSizes([220, width - 420, 200])

    def _show_plugin_manager(self) -> None:
        """显示插件管理器对话框（含导入/打包按钮）。"""
        try:
            from calc_framework.plugin.registry import PluginMeta, get_registry, list_plugins
        except ImportError:
            QMessageBox.information(self, "插件", "框架未安装 calc_framework.plugin 模块")
            return

        plugins = list_plugins()
        reg = get_registry()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"插件管理器 ({len(plugins)} 已注册)")
        dialog.resize(560, 460)
        layout = QVBoxLayout(dialog)

        # 工具栏
        toolbar = QHBoxLayout()
        import_btn = QPushButton("导入 .calcplugin...")
        import_btn.setStyleSheet("""
            QPushButton { background-color: #2B6CB6; color: white;
                          border: none; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #3182CE; }
        """)
        import_btn.clicked.connect(lambda: self._import_plugin(dialog))
        toolbar.addWidget(import_btn)

        build_btn = QPushButton("打包插件目录...")
        build_btn.setStyleSheet("""
            QPushButton { background-color: #2B6CB6; color: white;
                          border: none; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { background-color: #3182CE; }
        """)
        build_btn.clicked.connect(lambda: self._build_plugin(dialog))
        toolbar.addWidget(build_btn)

        refresh_btn = QPushButton("刷新")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #D1D1D1;
                          border: 1px solid #464646; border-radius: 4px; padding: 6px 14px; }
            QPushButton:hover { border-color: #2B6CB6; }
        """)
        refresh_btn.clicked.connect(lambda: (dialog.accept(), self._show_plugin_manager()))
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        if not plugins:
            layout.addWidget(QLabel("暂无已注册的插件。\n点击「导入 .calcplugin」安装一个插件，或「打包插件目录」将源码目录打包为 .calcplugin。"))
        else:
            for name in plugins:
                plugin = reg.get(name)
                if plugin is None:
                    continue
                meta = plugin.meta
                group = QGroupBox(f"{meta.name}  v{meta.version}")
                fl = QFormLayout(group)
                fl.addRow("描述:", QLabel(meta.description))
                fl.addRow("作者:", QLabel(meta.author or "—"))
                if meta.dependencies:
                    fl.addRow("依赖:", QLabel(", ".join(meta.dependencies)))
                layout.addWidget(group)

        layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def _import_plugin(self, parent: QWidget) -> None:
        """导入 .calcplugin 文件。"""
        path, _ = QFileDialog.getOpenFileName(
            parent, "导入插件", "",
            "CalcPlugin (*.calcplugin);;ZIP (*.zip);;All Files (*)",
        )
        if not path:
            return
        try:
            from tools.plugin_pack import install_plugin
            repo = Path(__file__).resolve().parents[3]
            target = repo / "web" / "hub" / "plugins"
            installed = install_plugin(path, target)
            self._status_label.setText(f"插件已安装: {installed.name}")
            QMessageBox.information(parent, "导入成功",
                                    f"插件已安装到:\n{installed}\n\n点击「刷新」查看已注册的插件。")
        except Exception as e:
            QMessageBox.critical(parent, "导入失败", f"导入插件时出错:\n{e}")

    def _build_plugin(self, parent: QWidget) -> None:
        """从目录打包 .calcplugin。"""
        dir_path = QFileDialog.getExistingDirectory(parent, "选择插件源码目录")
        if not dir_path:
            return
        try:
            from tools.plugin_pack import build_plugin
            output, _ = QFileDialog.getSaveFileName(
                parent, "保存为 .calcplugin", "",
                "CalcPlugin (*.calcplugin)",
            )
            if not output:
                return
            result = build_plugin(dir_path, output)
            self._status_label.setText(f"插件已打包: {result.name}")
            QMessageBox.information(parent, "打包成功", f"插件已打包:\n{result}")
        except Exception as e:
            QMessageBox.critical(parent, "打包失败", f"打包插件时出错:\n{e}")

    def closeEvent(self, event: Any) -> None:
        if self._asset_temp_dir:
            self._asset_temp_dir.cleanup()
            self._asset_temp_dir = None
        super().closeEvent(event)


def open_calcpack(path: str | Path) -> None:
    """便捷函数：加载并显示 .calcpack 文件。"""
    app = QApplication.instance() or QApplication([])
    viewer = CalcPackViewer()
    viewer.load_calcpack(path)
    viewer.show()


def main() -> None:
    """CLI 入口。

    用法::

        python -m calc_framework.ui.viewer [path/游戏名.calcpack]
    """
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("计算包查看器")

    path = sys.argv[1] if len(sys.argv) > 1 else None
    viewer = CalcPackViewer(path)

    if path:
        viewer.load_calcpack(path)

    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
