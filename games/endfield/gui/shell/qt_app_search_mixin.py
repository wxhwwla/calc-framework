# SPDX-License-Identifier: AGPL-3.0
"""全量搜索相关回调(SearchMixin,混合入 QtDamageApp)。"""



from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QFileDialog, QMessageBox
from utils.app_paths import allocate_search_run_directory, default_search_output_root

from games.endfield.gui.controls.search.qt_actions import QtSearchResultsDialog, SearchWorker
from games.endfield.gui.presentation.search_results_lines import build_search_results_report_lines


class SearchMixin:

    """全量搜索线程、进度、结果回调。"""



    def _build_search_job_inputs(self) -> Any:

        from games.endfield.gui.app.loadout_state import read_loadout_from_panels



        dock = self.control_dock

        loadout = read_loadout_from_panels(

            self.char_panel, self.weapon_panel,

            calculation_mode=self._current_calc_mode,

            weapon_scope_label=dock.single_skill_scope_combo.currentText(),

            equipment_scope_label=dock.equipment_scope_combo.currentText(),

            fixed_loadout=dock.read_fixed_loadout_selection(self._equipment_catalog),

            use_manual_multi_skill_counts=dock.use_manual_skill_counts_cb.isChecked(),

            manual_counts=dock.read_skill_counts(),

            physical_abnormal_counts=dock.read_physical_abnormal_counts(),

            spell_abnormal_counts=dock.read_spell_abnormal_counts(),

            damage_component_mode=dock.read_damage_component_mode(),

            use_expected_crit=dock.use_expected_crit_cb.isChecked(),

            include_conditional_equipment_crit=dock.include_conditional_crit_cb.isChecked(),

            extra_crit_rate=dock.read_extra_crit_rate(),

            extra_crit_damage=dock.read_extra_crit_damage(),

            enemy_defense=self._enemy_defense,

            enemy_resistance=self._enemy_resistance,

            ignore_resistance=self._ignore_resistance,

            imbalance_vulnerability_coeff=self._imbalance_vulnerability_coeff,

            is_unbalanced=self._is_unbalanced,

        )

        if loadout is None:

            return None

        return loadout.to_search_job_inputs(

            all_weapons=list(self.all_weapons),

            equipment_catalog=dict(self._equipment_catalog),

        )
        """build search job inputs。"""



    def _on_mvp_search(self) -> None:

        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.run.cancel import SearchCancelToken



        inputs = self._build_search_job_inputs()

        if inputs is None:

            QMessageBox.warning(self.app, "MVP 搜索", "请先选择有效的角色和武器。")

            return

        job, err = prepare_search_job(inputs)

        if err or job is None:

            QMessageBox.warning(self.app, "最优搜索", err or "无法准备搜索任务")

            return



        output_dir = QFileDialog.getExistingDirectory(

            self.app, "选择 MVP 搜索导出目录", str(default_search_output_root()),

        )

        export_root = allocate_search_run_directory(purpose="mvp_search") if not output_dir else Path(output_dir)



        cancel_token = SearchCancelToken()

        self._search_cancel_token = cancel_token

        worker = SearchWorker(

            job, mode_label="最优搜索并导出", export_root=export_root,

            top_n_choice=self.control_dock.read_top_n_choice(),

            workers_choice=self.control_dock.read_workers_choice(),

            status_prefix="最优搜索状态", cancel_token=cancel_token,

        )

        self._start_search_thread(worker, "最优搜索状态：计算中，请稍候...")
        """on mvp search。"""



    def _on_full_search(self) -> None:

        from utils.app_paths import allocate_search_run_directory

        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.run.cancel import SearchCancelToken
        from games.endfield.calc.search.run.single_skill import estimate_single_skill_search
        from games.endfield.gui.controls.search.search_settings import resolve_parallel_workers, resolve_top_n



        inputs = self._build_search_job_inputs()

        if inputs is None:

            QMessageBox.warning(self.app, "全量遍历", "请先选择有效的角色和武器。")

            return

        job, err = prepare_search_job(inputs)

        if err or job is None:

            QMessageBox.warning(self.app, "全量遍历", err or "无法准备搜索任务")

            return



        dock = self.control_dock

        estimate = estimate_single_skill_search(

            job, max_workers=resolve_parallel_workers(dock.read_workers_choice()),

            top_n=resolve_top_n(dock.read_top_n_choice()),

        )

        self._search_estimated_total_seconds = estimate.estimated_seconds

        if estimate.estimated_seconds >= 120:

            reply = QMessageBox.question(

                self.app, "确认全量遍历", f"{estimate.text}\n\n组合较多，是否仍要开始？",

                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,

                QMessageBox.StandardButton.No,

            )

            if reply != QMessageBox.StandardButton.Yes:

                return



        cancel_token = SearchCancelToken()

        self._search_cancel_token = cancel_token

        export_root = allocate_search_run_directory(purpose="full_search")

        mode_label = "多技能加权全量遍历" if job.multi_skill_eval is not None else "单技能全量遍历"

        worker = SearchWorker(

            job, mode_label=mode_label, export_root=export_root,

            top_n_choice=dock.read_top_n_choice(),

            workers_choice=dock.read_workers_choice(),

            status_prefix="全量遍历", cancel_token=cancel_token,

        )

        self._start_search_thread(worker, "全量遍历：计算中，请稍候。")
        """on full search。"""



    def _start_search_thread(self, worker: Any, status_running: str) -> None:

        self._search_thread = QThread()

        worker.moveToThread(self._search_thread)

        worker.progress.connect(self._on_search_progress)

        worker.finished.connect(self._on_search_finished)

        worker.error.connect(self._on_search_error)

        self._search_thread.started.connect(worker.run)

        self._search_thread.finished.connect(self._search_thread.deleteLater)

        self._search_thread.start()

        self._set_search_btns_enabled(False)

        self.control_dock.search_cancel_btn.setEnabled(True)

        self.control_dock.mvp_status_label.setVisible(True)

        self.control_dock.mvp_status_label.setText(status_running)
        """start search thread。"""



    def _on_search_progress(self, text: str) -> None:

        self.control_dock.mvp_status_label.setText(text)
        """on search progress。"""



    def _on_search_finished(self, mode_label: str, job: Any, outcome: Any, export_paths: dict) -> None:

        self._search_cancel_token = None

        self._search_thread.quit()

        self._search_thread.wait()

        damage_metric = "加权总伤" if job.multi_skill_eval is not None else "伤害"

        lines = build_search_results_report_lines(

            mode_label=mode_label, skill_label=str(job.skill_label),

            scope_labels=(str(job.weapon_scope), str(job.equipment_scope)),

            processed_combinations=int(outcome.processed_combinations),

            total_combinations=int(outcome.total_combinations),

            top_results=outcome.top_results, export_paths=export_paths,

            cancelled=bool(outcome.cancelled), damage_metric=damage_metric,

            segment_counts=(dict(job.multi_skill_eval.skill_counts) if job.multi_skill_eval else None),

            abnormal_counts=dict(job.physical_abnormal_counts or {}),

            spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),

        )

        suffix = "（已取消）" if outcome.cancelled else "：完成"

        mode = "全量遍历" if "全量" in mode_label else "MVP搜索状态"
        status = f"{mode}{suffix}（{outcome.processed_combinations}/{outcome.total_combinations}）"

        self.control_dock.mvp_status_label.setText(status)

        self._set_search_btns_enabled(True)

        dialog = QtSearchResultsDialog(

            self.app, title=mode_label, lines=lines,

            big_font=self.big_font, small_font=self.small_font,

            top_results=outcome.top_results,

            damage_metric=damage_metric,

            segment_counts=(dict(job.multi_skill_eval.skill_counts) if job.multi_skill_eval else None),

            abnormal_counts=dict(job.physical_abnormal_counts or {}),

            spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),

        )

        dialog.exec()
        """on search finished。"""



    def _on_search_error(self, error_msg: str) -> None:

        self._search_cancel_token = None

        if hasattr(self, "_search_thread") and self._search_thread:

            self._search_thread.quit()

            self._search_thread.wait()

        self.control_dock.mvp_status_label.setText(f"搜索失败：{error_msg}")

        self._set_search_btns_enabled(True)

        QMessageBox.critical(self.app, "搜索失败", error_msg)
        """on search error。"""



    def _on_cancel_search(self) -> None:

        if self._search_cancel_token is not None:

            self._search_cancel_token.cancel()

            self.control_dock.mvp_status_label.setText("搜索状态：正在取消。")
        """on cancel search。"""



    def _set_search_btns_enabled(self, enabled: bool) -> None:

        dock = self.control_dock

        dock.mvp_search_btn.setEnabled(enabled)

        dock.full_search_btn.setEnabled(enabled)

        dock.search_workers_combo.setEnabled(enabled)

        dock.search_top_n_combo.setEnabled(enabled)

        dock.search_cancel_btn.setEnabled(not enabled)
        """set search btns enabled。"""

