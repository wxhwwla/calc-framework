# SPDX-License-Identifier: AGPL-3.0
"""开发者工具主窗口 — 三页签：数据录入 / 布局编辑 / 主题与导出。



三页签数据共享：

- 数据录入 → 主题与导出：标准格式数据自动传递

- 布局编辑 → 主题与导出：DAG + layout 自动传递

- 切换到导出页签时自动同步

"""



from __future__ import annotations



import sys

import os



_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

if _project_root not in sys.path:

    sys.path.insert(0, _project_root)




from PySide6.QtGui import QAction, QKeySequence

from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,



)

from utils.gui.help_dialog import HelpDialog, HelpSection

from utils.gui.help_loader import load_multi_category



from utils.gui.donation import open_donation_dialog



from calc_framework.config.manager import AdapterManager



from tools.designer.data_editor.panel import DataEditorPanel

from tools.designer.layout_editor.canvas import LayoutCanvasPanel

from tools.designer.theme_editor.panel import ThemePanel





class DesignerWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("配置包设计器")

        self.resize(1200, 800)



        self._adapter_mgr = AdapterManager()



        self._tabs = QTabWidget()

        self.setCentralWidget(self._tabs)



        self._data_panel = DataEditorPanel()

        self._layout_panel = LayoutCanvasPanel()

        self._theme_panel = ThemePanel()

        self._theme_panel.export_requested.connect(self._on_export)



        self._tabs.addTab(self._data_panel, "数据录入")

        self._tabs.addTab(self._layout_panel, "布局编辑")

        self._tabs.addTab(self._theme_panel, "主题与导出")



        self._status = QStatusBar()

        self._status_label = QLabel("就绪")

        self._status.addWidget(self._status_label)

        self.setStatusBar(self._status)



        self._setup_menu()



        self._tabs.currentChanged.connect(self._on_tab_changed)



        self._layout_panel.layout_changed.connect(self._on_layout_changed)



        self._update_status()



    def _setup_menu(self) -> None:

        menubar = self.menuBar()

        help_menu = menubar.addMenu("帮助(&H)")

        help_action = QAction("使用说明(&U)", self)

        help_action.setShortcut(QKeySequence("F1"))

        help_action.triggered.connect(self._show_help)

        help_menu.addAction(help_action)

        help_menu.addSeparator()

        donation_action = QAction("自愿捐赠(&D)", self)

        donation_action.triggered.connect(lambda: open_donation_dialog(self))

        help_menu.addAction(donation_action)



    def _show_help(self) -> None:


        dialog = HelpDialog(self._build_designer_help, self, title="配置包设计器 使用说明")

        dialog.exec()



    @staticmethod

    def _build_designer_help() -> list[HelpSection]:
        docs = load_multi_category(
            {
                "完整说明书": [
                    "GUI ③：配置包设计器",
                    "数据结构与文件格式",
                ],
            }
        )
        static_help = [
            HelpSection(
                category="入门",
                title="概述",
                content="""\
<h2>配置包设计器</h2>
<p>配置包设计器用于创建和编辑 .calcpack 配置文件，包含数据、布局和主题的完整设计流程。<br>
生成的 .calcpack 文件可以通过 CalcPackViewer 加载使用。</p>
<p>详见 <code>docs/制造游戏计算器完整流程.md</code>。</p>""",
            ),
        ]
        static_help += [
            HelpSection(
                category="数据录入",
                title="数据录入页签",
                content="""\
<h2>数据录入</h2>
<p>提供标准化的数据录入界面，支持角色、武器、装备等实体的数据管理：</p>
<ul>
<li><b>角色数据</b> — 名称、类型、星级、能力值、基础属性、技能 JSON 等</li>
<li><b>武器数据</b> — 名称、类型、星级、基础攻击力、附加属性、特殊能力等</li>
<li><b>装备数据</b> — 装备属性、套装效果等</li>
</ul>
<h3>操作说明</h3>
<ul>
<li>填写表单后点击「保存」</li>
<li>已保存的数据会传递到「主题与导出」页签，用于打包</li>
<li>支持导入已有 JSON 数据进行编辑</li>
</ul>""",
            ),
        ]
        static_help += [
            HelpSection(
                category="布局编辑",
                title="布局编辑页签",
                content="""\
<h2>布局编辑</h2>
<p>可视化编排 DAG 节点和布局，设计计算器的界面结构：</p>
<ul>
<li>从适配器列表选择目标游戏适配器</li>
<li>加载 DAG 数据和布局模板</li>
<li>拖拽编排节点位置</li>
<li>网格吸附 + 碰撞检测辅助对齐</li>
</ul>
<h3>操作说明</h3>
<ul>
<li>选择适配器后自动加载数据</li>
<li>编排完成后布局数据自动同步到导出页签</li>
<li>支持实时预览编排效果</li>
</ul>""",
            ),
        ]
        static_help += [
            HelpSection(
                category="主题与导出",
                title="主题与导出页签",
                content="""\
<h2>主题与导出</h2>
<h3>主题编辑</h3>
<ul>
<li><b>字体</b> — 选择界面字体和字号</li>
<li><b>色板</b> — 编辑界面配色方案</li>
<li>修改实时生效，可随时预览效果</li>
</ul>
<h3>导出 .calcpack</h3>
<ol>
<li>确认数据、布局、主题都已配置完成</li>
<li>检查各页签数据是否已同步</li>
<li>点击「导出」按钮</li>
<li>选择导出路径，系统会打包为 .calcpack 文件</li>
</ol>
<p>.calcpack 文件生成后，可以用 CalcPackViewer 或启动器直接打开使用。</p>""",
            ),
        ]
        static_help += [
            HelpSection(
                category="常见问题",
                title="常见问题",
                content="""\
<h2>使用技巧与常见问题</h2>
<h3>数据同步</h3>
<p>切换到「主题与导出」页签时，系统会自动同步其他页签的数据。<br>
如果需要手动同步，可以切换页签触发。</p>
<h3>常见问题</h3>
<p><b>Q: 生成的 .calcpack 怎么用？</b><br>
A: 用启动器或 CalcPackViewer 打开。</p>
<p><b>Q: 数据格式有要求吗？</b><br>
A: 系统使用标准四层 schema，数据录入界面会自动引导填写正确格式。</p>""",
            ),
        ]
        return static_help + docs



    def _on_tab_changed(self, index: int) -> None:

        if index == 1:

            self._layout_panel.populate_adapters(self._adapter_mgr.names)

        elif index == 2:

            self._auto_sync_to_theme()

        self._update_status()



    def _on_layout_changed(self, layout_data: dict | None) -> None:

        if layout_data:

            self._status_label.setText("布局已更新 — 导出页签可同步最新数据")



    def _auto_sync_to_theme(self) -> None:

        """切到导出页签时自动同步其他面板的数据。"""

        data_files = self._data_panel.get_data_files()



        layout_data = self._layout_panel.get_layout_data()

        dag_service = self._layout_panel.get_dag_service()



        dag_dict = None

        if dag_service:

            try:


                from calc_framework.dag.serializer import dag_to_dict

                dag_dict = dag_to_dict(dag_service.dag)

            except Exception:

                dag_dict = {"name": self._layout_panel.get_adapter_name(), "from_adapter": True}



        if any(data_files.values()):

            count_parts = [f"{k}={len(v)}" for k, v in data_files.items()]

            self._status_label.setText(

                f"已同步数据({', '.join(count_parts)}) + "

                f"{'布局' if layout_data else '无布局'} + "

                f"{'DAG' if dag_dict else '无DAG'}"

            )



        self._theme_panel.set_shared_data(

            data_files=data_files,

            dag_data=dag_dict,

            layout_data=layout_data,

        )

        self._theme_panel._sync_from_shared()



    def _update_status(self) -> None:

        tab_name = self._tabs.tabText(self._tabs.currentIndex())

        self._status_label.setText(f"当前页签: {tab_name}")



    def _on_export(self, path: str) -> None:

        self._status_label.setText(f"已导出 → {path}")





def main() -> None:

    app = QApplication(sys.argv)

    app.setApplicationName("配置包设计器")

    win = DesignerWindow()

    win.showMaximized()

    sys.exit(app.exec())





if __name__ == "__main__":

    main()

