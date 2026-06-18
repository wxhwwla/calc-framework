# SPDX-License-Identifier: AGPL-3.0
# ruff: noqa: N999 — 模板文件使用 _template 前缀命名，是设计意图
"""TEMPLATE（{Game}）桌面 GUI — ComputeSheet 声明式面板示例。

用法::

    python -m games._template.gui._template_App

TODO:
  - 替换 _template_App.py 文件名为 your_game_App.py
  - 替换类名 TEMPLATEDamageApp 为 YourGameDamageApp
  - 根据实际 DAG 变量调整 user_context_overrides 映射
  - 可选：替换 QPushButton 占位为游戏特有的角色/武器选择面板
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..framework_bridge import AdapterPackage, ComputeSheet, load_layout_json

_ADAPTER_DIR = Path(__file__).resolve().parents[4] / "framework" / "adapters" / "_template"


class TEMPLATEDamageApp(QMainWindow):
    """{Game} 桌面伤害计算器 — ComputeSheet 声明式面板示例。

    此模板演示了正确的 ComputeSheet 集成模式：
      1. 通过 AdapterPackage 加载 DAG 服务和 layout.json
      2. 定义 user_context_overrides 将 user_input 变量映射到 DAG context
      3. 创建 ComputeSheet 并传入映射
      4. 处理 evaluate 事件展示结果
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("{Game} 伤害计算器")
        self.setMinimumSize(800, 600)
        self.resize(1024, 768)

        self._pkg = AdapterPackage(_ADAPTER_DIR)
        self._dag_service = self._pkg.dag_service
        self._setup_ui()

    def _setup_ui(self) -> None:
        """构建主界面布局。"""
        cw = QWidget()
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw)

        # 标题
        title = QLabel("{Game} 伤害计算器")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 12px;")
        root.addWidget(title)

        # ── ComputeSheet 区域 ──────────────────────────────
        sheet_widget = self._build_compute_sheet()
        if sheet_widget is not None:
            root.addWidget(sheet_widget, stretch=1)
        else:
            placeholder = QLabel("ComputeSheet 不可用（请先完成 layout.json 和 DAG 配置）")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            root.addWidget(placeholder, stretch=1)

        # ── 底部操作栏 ─────────────────────────────────────
        btn_row = QHBoxLayout()
        compute_btn = QPushButton("计算")
        compute_btn.clicked.connect(self._on_compute)
        btn_row.addStretch()
        btn_row.addWidget(compute_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        result_label = QLabel("结果将显示在此处")
        result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(result_label)

    # ───────────────────────────────────────────────────────
    #  ComputeSheet 集成（核心模式）
    # ───────────────────────────────────────────────────────

    def _build_compute_sheet(self) -> QWidget | None:
        """创建 ComputeSheet 控件。

        这是标准的 ComputeSheet 集成模式，与 games/arknights/gui/ArknightsApp.py
        和 games/endfield/gui/endfield_app.py 中的用法一致。
        """
        # 1. 从适配包加载 layout.json
        layout_path = _ADAPTER_DIR / "ui" / "layout.json"
        if not layout_path.is_file():
            return None

        layout = load_layout_json(str(layout_path))
        variables = dict(self._dag_service.dag.variables) if self._dag_service.dag.variables else {}

        # 2. 筛选出 user_input 源变量（与 layout.json 中的 inputs 对应）
        _user_vars = {k: v for k, v in variables.items() if isinstance(v, dict) and v.get("source") == "user_input"}
        # 或者直接逐一手动定义:
        # user_vars = {
        #     "user_input.技能倍率": {"type": "float", "default": 1.0, ...},
        # }

        # 3. 定义 user_context_overrides 映射
        #    格式: "user_input.<字段名>": ("<context路径>", ["override"|"add"])
        #    - "override": 替换 DAG context 中该变量的值
        #    - "add":      叠加到 DAG context 中该变量的值（适用于百分比加成）
        #
        #    左键是 layout.json 中声明的 user_input 变量路径。
        #    右键是 DAG context 中的变量路径（character.* / enemy.* / computed.*）。
        user_context_overrides: dict[str, tuple[str, list[str]]] = {
            # ── 敌方参数 ────────────────────────────────────
            "user_input.敌人防御": ("enemy.防御", ["override"]),
            "user_input.敌人抗性": ("enemy.法术抗性", ["override"]),
            # ── 角色参数 ────────────────────────────────────
            "user_input.技能等级": ("computed.技能等级", ["override"]),
            "user_input.攻击力加成": ("computed.攻击力百分比加成", ["add"]),
            "user_input.伤害加成": ("computed.伤害加成", ["add"]),
            # TODO: 根据实际 DAG 变量调整以上映射
        }

        # 4. 创建 ComputeSheet
        compute_sheet = ComputeSheet(
            self._dag_service,
            layout,
            variables,
            base_context={},
            user_context_overrides=user_context_overrides,
        )

        # 5. 设置基础 context 值（从游戏数据加载）
        # compute_sheet.set("character.攻击力", 490.0)

        # 6. 连接 evaluate 信号
        compute_sheet.evaluated.connect(self._on_sheet_evaluated)

        return compute_sheet.widget(parent=self)

    def _on_sheet_evaluated(self, outputs: dict[str, float]) -> None:
        """ComputeSheet 求值完成回调。"""
        # TODO: 更新 GUI 展示
        pass

    # ───────────────────────────────────────────────────────
    #  业务方法
    # ───────────────────────────────────────────────────────

    def _on_compute(self) -> None:
        """计算按钮回调。"""
        # TODO: 调用 compute_snapshot_with_dag() 并展示结果
        pass


def main() -> None:
    """应用入口。"""
    import sys

    # TODO: 配置 sys.path（参照 games/arknights/main.py 的 _path_setup 模式）
    app = QApplication(sys.argv)
    window = TEMPLATEDamageApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
