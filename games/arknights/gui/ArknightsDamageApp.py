# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""明日方舟 Desktop GUI 伤害计算器。

基于 PySide6，直接调用本地 DAG 引擎 + skill_parser。
界面构建见 ``ArknightsAppUIMixin``，事件处理见 ``ArknightsAppEventsMixin``
（P2-07 结构债清理）。
"""

from __future__ import annotations

import sys
from typing import Any

# 深色主题 QSS — 框架 ThemeManager 基础 + Arknights 特定覆盖
from calc_framework.ui.theme import ThemeManager as _ThemeManager
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidgetItem

from games.arknights.calc.dag_adapter.adapter import compute_snapshot_with_dag, get_parsed_skill_info
from games.arknights.gui.arknights_app_events import ArknightsAppEventsMixin
from games.arknights.gui.arknights_app_ui import ArknightsAppUIMixin
from games.arknights.gui.arknights_compute_sheet import read_compute_params_from_sheet
from games.arknights.gui.arknights_sheet_config import merge_atk_percent_bonus
from games.arknights.operator_catalog import build_operator_index, load_operators_map

_BASE_DARK = _ThemeManager().stylesheet("dark")
DARK_QSS = (
    _BASE_DARK
    + """
QGroupBox {
    border: 1px solid #464646; border-radius: 8px; margin-top: 12px;
    padding-top: 16px; font-size: 13px; font-weight: bold; color: #E0E0E0;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QPushButton {
    background-color: #2B6CB6; color: white; border: none; border-radius: 6px;
    padding: 8px 24px; font-size: 14px; font-weight: bold; min-height: 20px;
}
QPushButton:hover { background-color: #3182CE; }
QPushButton:pressed { background-color: #1A4A8A; }
QPushButton:disabled { background-color: #4A4A4A; color: #888888; }
QSlider::groove:horizontal { height: 6px; background: #3C3C3C; border-radius: 3px; }
QSlider::handle:horizontal {
    background-color: #2B6CB6; width: 16px; height: 16px;
    margin: -5px 0; border-radius: 8px;
}
QSlider::sub-page:horizontal { background-color: #2B6CB6; border-radius: 3px; }
QTableWidget { border-radius: 4px; gridline-color: #333333; }
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section { border: 1px solid #464646; padding: 4px; }
"""
)


class ArknightsDamageApp(QMainWindow, ArknightsAppUIMixin, ArknightsAppEventsMixin):
    """明日方舟桌面伤害计算器 — 完整版（与 Web 页面对齐）。"""

    def __init__(self, *, embedded: bool = False) -> None:
        self._embedded = embedded
        existing = QApplication.instance()
        if existing is None:
            self._qapp: QApplication = QApplication(sys.argv)  # type: ignore[name-defined]
            self._owns_qapp = True
        else:
            self._qapp = existing
            self._owns_qapp = False
        if self._owns_qapp:
            self._qapp.setStyle("Fusion")
            self._qapp.setStyleSheet(DARK_QSS)
            from calc_framework.ui.app_icon import apply_application_identity

            apply_application_identity(self._qapp, "CalcFramework.Arknights")

        super().__init__()
        self.setWindowTitle("明日方舟 伤害计算器")
        self.setMinimumSize(1200, 720)
        self.resize(1366, 768)

        self._operators_map = load_operators_map()
        self._operator_index = build_operator_index(self._operators_map)
        self._current_operator: dict[str, Any] | None = None
        self._skill_count: int = 0

        self._setup_ui()

    # ═══════════════════════════════════════════
    #  计算
    # ═══════════════════════════════════════════

    def _on_compute(self) -> None:
        """执行伤害计算并更新所有结果展示面板。"""
        if not self._current_operator:
            self._result_label.setText("请先选择一个干员")
            self._set_confirm_ui_failed("请先选择一个干员")
            return

        self._set_confirm_ui_computing()
        try:
            level = self._lvl_slider.value()
            si = self._skill_combo.currentIndex() - 1
            skill_info = get_parsed_skill_info(self._current_operator, level, si)

            # 技能倍率：手动输入优先
            try:
                skill_mult = float(self._mult_input.text() or "1.0")
            except ValueError:
                skill_mult = skill_info.effective_multiplier

            # 条件触发
            if self._cond_check.isChecked() and skill_info.has_conditional:
                skill_mult = skill_info.conditional_mult

            hit_count = self._hit_spin.value()

            sheet_params = read_compute_params_from_sheet(self._param_sheet)
            enemy_def = sheet_params["enemy_def"]
            enemy_res = sheet_params["enemy_res"]
            def_pen = sheet_params["def_penetration"]
            res_pen = sheet_params["res_penetration"]
            atk_bonus = merge_atk_percent_bonus(
                sheet_params["atk_percent_bonus"],
                skill_info.atk_buff_hint,
            )
            dmg_bonus = sheet_params["dmg_bonus"]

            result = compute_snapshot_with_dag(
                operator=self._current_operator,
                skill_level=level,
                skill_multiplier=skill_mult,
                enemy_def=enemy_def,
                enemy_res=enemy_res,
                atk_percent_bonus=atk_bonus,
                dmg_bonus=dmg_bonus,
                def_penetration=def_pen,
                res_penetration=res_pen,
                trust_atk_override=sheet_params["trust_atk"],
                pot_atk_override=sheet_params["pot_atk"],
            )

            outputs = result.outputs
            final_atk = outputs.get("最终攻击力", 0)
            phys = outputs.get("物理伤害", 0)
            magic = outputs.get("法术伤害", 0)
            true_dmg = outputs.get("真伤伤害", 0)

            # 更新结果卡片
            self._result_cards["atk"].setText(f"{final_atk:.1f}")
            self._result_cards["phys"].setText(f"{phys:.1f}")
            self._result_cards["phys"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #DAA520; border: none;"
            )
            self._result_cards["magic"].setText(f"{magic:.1f}")
            self._result_cards["magic"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #2B6CB6; border: none;"
            )
            self._result_cards["true"].setText(f"{true_dmg:.1f}")
            self._result_cards["true"].setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #68D391; border: none;"
            )

            # 乘区明细表
            op = self._current_operator
            base_atk = float(op.get("基础属性", {}).get("攻击", 0))
            trust_atk = sheet_params["trust_atk"]
            pot_atk = sheet_params["pot_atk"]
            zone_rows = [
                ("基础攻击力", f"{base_atk:.1f}"),
                ("信赖加成", f"+{trust_atk:.1f}" if trust_atk > 0 else "0"),
                ("潜能攻击", f"+{pot_atk:.1f}" if pot_atk > 0 else "0"),
                (f"ATK%加成（{atk_bonus:.0f}%）", f"+{base_atk * atk_bonus / 100:.1f}"),
                ("最终攻击力", f"{final_atk:.1f}"),
                ("技能倍率", f"x{skill_mult:.2f}"),
                ("连发数", f"x{hit_count}"),
                ("总伤害倍率", f"x{skill_mult * hit_count:.2f}"),
                ("", ""),
                ("防御力", f"{enemy_def:.0f}"),
                ("法术抗性", f"{enemy_res:.0f}%"),
                ("", ""),
                (
                    "物理伤害（单发）",
                    f"{phys:.1f}" if hit_count <= 1 else f"{(phys / hit_count if hit_count else 0):.1f}",
                ),
                # "法术伤害（单发）" 类似
            ]
            if hit_count > 1:
                zone_rows.append(("物理伤害（合计）", f"{phys * hit_count:.1f}"))
                zone_rows.append(("法术伤害（合计）", f"{magic * hit_count:.1f}"))
                zone_rows.append(("真伤伤害（合计）", f"{true_dmg * hit_count:.1f}"))

            self._result_table.setRowCount(len(zone_rows))
            for i, (k, v) in enumerate(zone_rows):
                self._result_table.setItem(i, 0, QTableWidgetItem(k))
                self._result_table.setItem(i, 1, QTableWidgetItem(v))
            self._result_table.resizeColumnsToContents()

            self._update_detail()
            self._fill_bonus_table(
                skill_mult=skill_mult,
                hit_count=hit_count,
                skill_info=skill_info,
                level=level,
            )

            op_name = op.get("名称", "")
            label = f"计算结果 — {op_name}"
            label += f"（{skill_info.name}，总伤害倍率 {skill_mult * hit_count:.2f}x）"
            if skill_info.is_healing:
                label += " ⚕ 治疗技能"
            self._result_label.setText(label)
            self._result_label.setStyleSheet("color: #68D391; font-size: 14px; font-weight: bold; padding: 8px;")
            self._set_confirm_ui_confirmed()

        except Exception as e:
            self._result_label.setText(f"计算错误: {e}")
            self._result_label.setStyleSheet("color: #FC8181; font-size: 12px; padding: 8px;")
            self._set_confirm_ui_failed("计算失败")
            import traceback

            traceback.print_exc()

    def _fill_bonus_table(
        self,
        *,
        skill_mult: float,
        hit_count: int,
        skill_info: Any,
        level: int,
    ) -> None:
        """确认后填充右下角「技能加成数据」表。"""
        level_text = f"Lv.{level}" if level <= 7 else f"专精{level - 7}"
        rows = [
            ("技能等级", level_text),
            ("技能倍率", f"x{skill_mult:.2f}"),
            ("连发数", f"x{hit_count}"),
            ("总伤害倍率", f"x{skill_mult * hit_count:.2f}"),
            ("技能攻击力加成", f"+{skill_info.atk_buff_hint * 100:.0f}%"),
        ]
        if skill_info.has_conditional:
            active = "已激活" if self._cond_check.isChecked() else "未激活"
            rows.append(("条件倍率", f"x{skill_info.conditional_mult:.2f}（{active}）"))
        if skill_info.is_healing:
            rows.append(("技能类型", "治疗"))
        self._bonus_table.setRowCount(len(rows))
        for i, (key, value) in enumerate(rows):
            self._bonus_table.setItem(i, 0, QTableWidgetItem(key))
            self._bonus_table.setItem(i, 1, QTableWidgetItem(value))
        self._bonus_table.resizeColumnsToContents()

    @property
    def confirm_btn(self):
        """底部工具条中的确认按钮。"""
        return self._shell.confirm_button

    def run(self) -> None:
        """显示主窗口；独立启动时进入事件循环。"""
        self.showMaximized()
        if self._owns_qapp:
            sys.exit(self._qapp.exec())

    def show_embedded(self) -> None:
        """由 launcher 同进程拉起时仅显示窗口。"""
        self.showMaximized()


def main() -> None:
    """启动明日方舟桌面伤害计算器（独立入口）。"""
    from pathlib import Path as _Path

    _REPO_ROOT = _Path(__file__).resolve().parents[2].parent
    _FW_SRC = _REPO_ROOT / "framework" / "src"
    if str(_FW_SRC) not in sys.path:
        sys.path.insert(0, str(_FW_SRC))
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))

    window = ArknightsDamageApp()
    window.run()


if __name__ == "__main__":
    main()
