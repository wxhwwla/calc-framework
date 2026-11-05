# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ArknightsAppEventsMixin — 明日方舟主窗口的筛选与选择事件处理。

从 ``ArknightsDamageApp.py`` 按符号边界拆出（P2-07 结构债清理）。
"""

from __future__ import annotations

from PySide6.QtWidgets import QTableWidgetItem

from games.arknights.calc.dag_adapter.adapter import get_parsed_skill_info
from games.arknights.calc.dag_adapter.loader import _parse_potential_atk
from games.arknights.calc.skill_parser import ParsedSkillInfo
from games.arknights.gui.arknights_compute_sheet import populate_operator_context
from games.arknights.gui.operator_combo import configure_operator_combobox
from games.arknights.operator_catalog import filter_operator_index, list_branches


class ArknightsAppEventsMixin:
    """筛选、干员/技能选择、详情与参数同步事件。"""

    def _update_total_mult_label(self) -> None:
        """更新总伤害倍率展示（与 Web 一致：技能倍率 × 连发数）。"""
        try:
            mult = float(self._mult_input.text() or "1.0")
        except ValueError:
            mult = 1.0
        hits = self._hit_spin.value()
        self._total_mult_label.setText(f"总伤害倍率: {mult * hits:.3f}x")

    def _set_skill_level(self, level: int) -> None:
        """技能等级快捷按钮 → 滑块。"""
        self._lvl_slider.setValue(level)

    def _sync_skill_level_chips(self, level: int) -> None:
        """同步技能等级快捷按钮选中态。"""
        for idx, chip in enumerate(self._lvl_chip_btns, start=1):
            chip.blockSignals(True)
            chip.setChecked(idx == level)
            chip.blockSignals(False)

    def _sync_param_sheet(self) -> None:
        """干员/技能变化时同步 ComputeSheet 信赖与潜能。"""
        if not self._current_operator:
            return
        level = self._lvl_slider.value()
        si = self._skill_combo.currentIndex() - 1
        info = get_parsed_skill_info(self._current_operator, level, si)
        populate_operator_context(
            self._param_sheet,
            self._current_operator,
            skill_multiplier=info.effective_multiplier,
            skill_level=level,
        )

    def _active_stars(self) -> set[int]:
        """获取当前勾选的所有星级。"""
        return {s for s, cb in self._star_checks.items() if cb.isChecked()}

    def _refresh_branch_combo(self) -> None:
        """根据当前职业刷新分支下拉选项。"""
        profession = self._prof_combo.currentData() or ""
        self._branch_combo.blockSignals(True)
        current = self._branch_combo.currentData() or ""
        self._branch_combo.clear()
        self._branch_combo.addItem("全部", "")
        for b in list_branches(self._operator_index, profession):
            self._branch_combo.addItem(b, b)
        idx = self._branch_combo.findData(current)
        if idx >= 0:
            self._branch_combo.setCurrentIndex(idx)
        self._branch_combo.blockSignals(False)

    def _refresh_operator_combo(self) -> None:
        """根据当前筛选条件刷新干员下拉列表。"""
        filtered = filter_operator_index(
            self._operator_index,
            active_stars=self._active_stars(),
            profession=self._prof_combo.currentData() or "",
            branch=self._branch_combo.currentData() or "",
        )
        names = [op["名称"] for op in filtered]
        current = self._op_combo.currentText()
        configure_operator_combobox(self._op_combo, names, preserve=current)
        total = len(self._operator_index)
        self._op_count_label.setText(f"显示 {len(names)} / {total} 个干员")

    def _on_profession_changed(self) -> None:
        """职业选择变化时刷新分支和干员列表。"""
        self._refresh_branch_combo()
        self._on_filter_changed()

    def _on_filter_changed(self) -> None:
        """筛选条件变化时刷新干员列表。"""
        self._refresh_operator_combo()

    def _on_op_selected(self, name: str) -> None:
        """选中干员时更新详情和技能信息。"""
        if not name or name not in self._operators_map:
            return
        self._current_operator = self._operators_map[name]
        self._skill_count = len(self._current_operator.get("技能", []))
        # 更新技能下拉
        self._skill_combo.blockSignals(True)
        self._skill_combo.clear()
        self._skill_combo.addItem("普攻")
        for i in range(min(self._skill_count, 3)):
            self._skill_combo.addItem(f"技能{i + 1}")
        for i in range(self._skill_count, 3):
            self._skill_combo.addItem(f"技能{i + 1}（无数据）")
        self._skill_combo.blockSignals(False)
        self._update_detail_header()
        self._on_skill_changed(1)  # default to skill 1
        self._mark_pending()

    def _on_skill_changed(self, idx: int) -> None:
        """技能选择变化时更新技能信息。"""
        if not self._current_operator:
            return
        si = idx - 1  # 0=普攻(-1), 1=技能1(0), 2=技能2(1), 3=技能3(2)
        level = self._lvl_slider.value()
        info = get_parsed_skill_info(self._current_operator, level, si)
        self._apply_skill_info(info)
        self._mark_pending()

    def _on_level_changed(self, value: int) -> None:
        """技能等级滑块变化时更新标签和技能信息。"""
        label = f"Lv.{value}" if value <= 7 else f"专精{value - 7}"
        self._lvl_label.setText(label)
        self._sync_skill_level_chips(value)
        self._on_skill_changed(self._skill_combo.currentIndex())

    def _apply_skill_info(self, info: ParsedSkillInfo) -> None:
        """将技能解析信息应用到 UI 控件。"""
        # 技能信息
        self._skill_info_box.show()
        self._skill_name_label.setText(info.name)
        self._skill_meta_label.setText(f"SP={info.sp_cost}  初始={info.init_sp}  持续={info.duration}秒")
        self._skill_desc_label.setText(info.description[:200] if info.description else "无描述")

        self._cond_check.setChecked(False)

        # 治疗标记
        if info.is_healing:
            self._skill_heal_label.setText("⚕ 治疗技能 — 结果数值为治疗量")
            self._cond_check.setVisible(False)
        else:
            self._skill_heal_label.setText("")
            self._cond_check.setVisible(info.has_conditional)
            if info.has_conditional:
                self._cond_check.setText(f"仅攻击到一人时（倍率 {info.conditional_mult:.2f}x）")

        # 自动倍率
        eff_mult = info.effective_multiplier
        auto_text = f"自动检测: {eff_mult:.2f}x"
        if info.atk_buff_hint > 0:
            auto_text += f"（含 ATK+{info.atk_buff_hint * 100:.0f}% 加成）"
        self._mult_auto_label.setText(auto_text)
        self._mult_input.setText(f"{eff_mult:.2f}")

        # 连发数
        self._hit_spin.setValue(info.hit_count)
        self._update_total_mult_label()
        self._sync_param_sheet()

    def _update_detail_header(self) -> None:
        """更新左上角基本信息（名称/职业/特性）。"""
        op = self._current_operator
        if not op:
            self._det_name.setText("")
            self._det_info.setText("")
            self._det_trait.setText("")
            return
        name = op.get("名称", "?")
        star = op.get("星级", 0)
        self._det_name.setText(f"{name}  {'★' * star}")
        self._det_info.setText(f"{op.get('职业', '')} · {op.get('分支', '')}")
        self._det_trait.setText(op.get("特性", ""))

    def _update_detail(self) -> None:
        """更新左下角干员基础数据（属性/信赖/潜能/天赋）。"""
        op = self._current_operator
        if not op:
            return
        self._update_detail_header()

        base = op.get("基础属性", {})
        labels = {
            "生命": "生命上限",
            "攻击": "攻击力",
            "防御": "防御力",
            "法术抗性": "法术抗性",
            "部署费用": "部署费用",
            "再部署": "再部署时间",
            "阻挡数": "阻挡数",
            "攻击间隔": "攻击间隔",
        }
        self._det_stat_tbl.setRowCount(len(base))
        for i, (k, v) in enumerate(base.items()):
            self._det_stat_tbl.setItem(i, 0, QTableWidgetItem(labels.get(k, k)))  # type: ignore[arg-type]
            self._det_stat_tbl.setItem(i, 1, QTableWidgetItem(f"{v:.1f}" if isinstance(v, float) else str(v)))
        self._det_stat_tbl.resizeColumnsToContents()

        trust = op.get("信赖加成", {})
        if trust and any(v != 0 for v in trust.values()):
            parts = "  ".join(f"{labels.get(k, k)} {'+' if v >= 0 else ''}{v}" for k, v in trust.items() if v != 0)
            self._det_trust.setText(f"信赖加成（200%）：{parts}")
            self._det_trust.show()
        else:
            self._det_trust.hide()

        potentials = op.get("潜能", [])
        pot_atk = _parse_potential_atk(potentials) if isinstance(potentials, list) else 0.0
        if pot_atk > 0:
            self._det_potential.setText(f"潜能攻击（满潜合计）：+{pot_atk:.0f}")
            self._det_potential.show()
        else:
            self._det_potential.hide()

        talents = op.get("天赋", [])
        if talents:
            lines = [f"{t.get('name', '')}（{t.get('unlock', '')}）：{t.get('description', '')}" for t in talents]
            self._det_talent.setText("天赋：\n" + "\n".join(lines))
            self._det_talent.show()
        else:
            self._det_talent.hide()
