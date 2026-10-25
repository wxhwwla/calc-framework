# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ActionsSearchMixin — 终末地伤害计算搜索相关事件处理。

从 ActionsMixin 拆分出的搜索方法（全量遍历、MVP 搜索、搜索线程管理、
搜索结果/进度/错误处理、搜索历史、耗时估算等）。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from calc_framework.ui.i18n import tr
from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QWidget
from utils.app_paths import allocate_search_run_directory, default_search_output_root
from utils.frozen_runtime import frozen_use_qthread_search

from games.endfield.framework_bridge import get_logger
from games.endfield.gui.app.loadout_state import read_loadout_from_panels
from games.endfield.gui.controls.search.qt_actions import QtSearchResultsDialog, SearchWorker
from games.endfield.gui.controls.search.qt_search_browser import SearchHistoryDialog
from games.endfield.gui.presentation.search_results_lines import build_search_results_report_lines

_logger = get_logger("gui.endfield_search")


class ActionsSearchMixin:
    """搜索相关事件处理混合类。

    提供全量遍历、MVP 搜索、搜索线程生命周期管理、
    搜索结果展示、搜索历史、耗时估算更新等。
    由 EndfieldApp 通过多重继承使用。
    """

    # ── 搜索耗时估算 ─────────────────────────────

    def _refresh_search_estimate(self) -> None:
        dock = self.control_dock
        if dock.estimate_output_label is None:
            return
        from games.endfield.gui.app.search_controller import format_search_duration

        secs = getattr(self, "_search_estimated_total_seconds", 0)
        dock.estimate_output_label.setText(format_search_duration(secs))

    # ── 搜索任务构建 ─────────────────────────────

    def _build_search_job_inputs(self) -> Any:
        dock = self.control_dock
        loadout = read_loadout_from_panels(
            self.char_panel,
            self.weapon_panel,
            calculation_mode=self._current_calc_mode,
            weapon_scope_label=dock.current_weapon_scope_label(),
            equipment_scope_label=dock.current_equipment_scope_label(),
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

    # ── MVP 搜索 / 全量搜索 ─────────────────────

    def _on_mvp_search(self) -> None:
        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.run.cancel import SearchCancelToken

        inputs = self._build_search_job_inputs()
        if inputs is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.searchMvpTitle"),
                tr("desktop.endfield.searchMvpNeedCharWeapon"),
            )
            return
        job, err = prepare_search_job(inputs)
        if err or job is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.searchOptTitle"),
                err or tr("desktop.endfield.searchPrepareFailed"),
            )
            return

        output_dir = QFileDialog.getExistingDirectory(
            cast(QWidget, self),
            tr("desktop.endfield.searchMvpExportDir"),
            str(default_search_output_root()),
        )
        export_root = allocate_search_run_directory(purpose="mvp_search") if not output_dir else Path(output_dir)

        cancel_token = SearchCancelToken()
        self._search_cancel_token = cancel_token
        worker = SearchWorker(
            job,
            mode_label=tr("desktop.endfield.searchOptExportMode"),
            export_root=export_root,
            top_n_choice=self.control_dock.read_top_n_choice(),
            workers_choice=self.control_dock.read_workers_choice(),
            status_prefix=tr("desktop.endfield.searchOptStatusPrefix"),
            cancel_token=cancel_token,
        )
        self._start_search_thread(worker, tr("desktop.endfield.searchOptRunning"))

    def _on_full_search(self) -> None:
        from games.endfield.calc.search.plan.controller import prepare_search_job
        from games.endfield.calc.search.run.cancel import SearchCancelToken
        from games.endfield.calc.search.run.single_skill import estimate_single_skill_search
        from games.endfield.gui.controls.search.search_settings import resolve_parallel_workers, resolve_top_n

        inputs = self._build_search_job_inputs()
        if inputs is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.searchFullTitle"),
                tr("desktop.endfield.searchMvpNeedCharWeapon"),
            )
            return
        job, err = prepare_search_job(inputs)
        if err or job is None:
            QMessageBox.warning(
                cast(QWidget, self),
                tr("desktop.endfield.searchFullTitle"),
                err or tr("desktop.endfield.searchPrepareFailed"),
            )
            return

        dock = self.control_dock
        estimate = estimate_single_skill_search(
            job,
            max_workers=resolve_parallel_workers(dock.read_workers_choice()),
            top_n=resolve_top_n(dock.read_top_n_choice()),
        )
        self._search_estimated_total_seconds = estimate.estimated_seconds
        from games.endfield.gui.app.search_controller import should_warn_search_combinations

        if should_warn_search_combinations(estimate.estimated_seconds):
            reply = QMessageBox.question(
                cast(QWidget, self),
                tr("desktop.endfield.searchFullConfirmTitle"),
                tr("desktop.endfield.searchFullConfirmMsg", estimate=estimate.text),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        cancel_token = SearchCancelToken()
        self._search_cancel_token = cancel_token
        export_root = allocate_search_run_directory(purpose="full_search")
        mode_label = (
            tr("desktop.endfield.searchFullMultiMode")
            if job.multi_skill_eval is not None
            else tr("desktop.endfield.searchFullSingleMode")
        )
        worker = SearchWorker(
            job,
            mode_label=mode_label,
            export_root=export_root,
            top_n_choice=dock.read_top_n_choice(),
            workers_choice=dock.read_workers_choice(),
            status_prefix=tr("desktop.endfield.searchFullStatusPrefix"),
            cancel_token=cancel_token,
        )
        self._start_search_thread(worker, tr("desktop.endfield.searchFullRunning"))

    # ── 搜索线程管理 ─────────────────────────────

    def _start_search_thread(self, worker: Any, status_running: str) -> None:
        """启动搜索：打包 exe 在主线程同步跑（避免 QThread + native 崩溃）。"""
        if not frozen_use_qthread_search():
            self._run_search_on_main_thread(worker, status_running)
            return
        self._search_thread = QThread()
        self._search_worker = worker
        worker.moveToThread(self._search_thread)
        worker.progress.connect(self._on_search_progress, Qt.ConnectionType.QueuedConnection)
        worker.finished.connect(self._on_search_finished, Qt.ConnectionType.QueuedConnection)
        worker.error.connect(self._on_search_error, Qt.ConnectionType.QueuedConnection)
        self._search_thread.started.connect(worker.run)
        self._search_thread.finished.connect(worker.deleteLater)
        self._search_thread.finished.connect(self._search_thread.deleteLater)
        self._search_thread.start()
        self._set_search_btns_enabled(False)
        self.control_dock.search_cancel_btn.setEnabled(True)
        self.control_dock.mvp_status_label.setVisible(True)
        self.control_dock.mvp_status_label.setText(status_running)

    def _run_search_on_main_thread(self, worker: Any, status_running: str) -> None:
        """打包 exe：阻塞主线程执行搜索，进度时 pump 事件循环。"""
        self._search_thread = None
        self._set_search_btns_enabled(False)
        self.control_dock.search_cancel_btn.setEnabled(True)
        self.control_dock.mvp_status_label.setVisible(True)
        self.control_dock.mvp_status_label.setText(status_running)

        def _progress_pump(text: str) -> None:
            self._on_search_progress(text)
            app = QApplication.instance()
            if app is not None:
                app.processEvents()

        worker.progress.connect(_progress_pump, Qt.ConnectionType.DirectConnection)
        worker.finished.connect(self._on_search_finished, Qt.ConnectionType.DirectConnection)
        worker.error.connect(self._on_search_error, Qt.ConnectionType.DirectConnection)
        worker.run()

    def _on_search_progress(self, text: str) -> None:
        self.control_dock.mvp_status_label.setText(text)

    def _on_search_finished(self, mode_label: str, job: Any, outcome: Any, export_paths: dict) -> None:
        self._search_cancel_token = None
        thread = getattr(self, "_search_thread", None)
        if thread is not None:
            thread.quit()
            thread.wait()
        damage_metric = (
            tr("desktop.endfield.searchWeightedDamage")
            if job.multi_skill_eval is not None
            else tr("desktop.endfield.searchDamage")
        )
        lines = build_search_results_report_lines(
            mode_label=mode_label,
            skill_label=str(job.skill_label),
            scope_labels=(str(job.weapon_scope), str(job.equipment_scope)),
            processed_combinations=int(outcome.processed_combinations),
            total_combinations=int(outcome.total_combinations),
            top_results=outcome.top_results,
            export_paths=export_paths,
            cancelled=bool(outcome.cancelled),
            damage_metric=damage_metric,
            segment_counts=(dict(job.multi_skill_eval.skill_counts) if job.multi_skill_eval else None),
            abnormal_counts=dict(job.physical_abnormal_counts or {}),
            spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),
        )
        suffix = (
            tr("desktop.endfield.searchCancelledSuffix")
            if outcome.cancelled
            else tr("desktop.endfield.searchDoneSuffix")
        )
        full_modes = (
            tr("desktop.endfield.searchFullMultiMode"),
            tr("desktop.endfield.searchFullSingleMode"),
        )
        mode = (
            tr("desktop.endfield.searchFullStatusMode")
            if mode_label in full_modes
            else tr("desktop.endfield.searchMvpStatusMode")
        )
        status = tr(
            "desktop.endfield.searchStatusFmt",
            mode=mode,
            suffix=suffix,
            processed=outcome.processed_combinations,
            total=outcome.total_combinations,
        )
        self.control_dock.mvp_status_label.setText(status)
        self._set_search_btns_enabled(True)
        dialog = QtSearchResultsDialog(
            cast(QWidget, self),
            title=mode_label,
            lines=lines,
            big_font=self.big_font,
            small_font=self.small_font,
            top_results=outcome.top_results,
            damage_metric=damage_metric,
            segment_counts=(dict(job.multi_skill_eval.skill_counts) if job.multi_skill_eval else None),
            abnormal_counts=dict(job.physical_abnormal_counts or {}),
            spell_abnormal_counts=dict(job.spell_abnormal_counts or {}),
        )
        dialog.exec()

    def _on_search_error(self, error_msg: str) -> None:
        self._search_cancel_token = None
        thread = getattr(self, "_search_thread", None)
        if thread is not None:
            thread.quit()
            thread.wait()
        self.control_dock.mvp_status_label.setText(tr("desktop.endfield.searchFailedStatus", error=error_msg))
        self._set_search_btns_enabled(True)
        QMessageBox.critical(
            cast(QWidget, self),
            tr("desktop.endfield.searchFailedTitle"),
            error_msg,
        )

    def _on_cancel_search(self) -> None:
        if self._search_cancel_token is not None:
            self._search_cancel_token.cancel()
            self.control_dock.mvp_status_label.setText(tr("desktop.endfield.searchCancelling"))

    def _set_search_btns_enabled(self, enabled: bool) -> None:
        dock = self.control_dock
        dock.mvp_search_btn.setEnabled(enabled)
        dock.full_search_btn.setEnabled(enabled)
        dock.search_workers_combo.setEnabled(enabled)
        dock.search_top_n_combo.setEnabled(enabled)
        dock.search_cancel_btn.setEnabled(not enabled)

    # ── 搜索历史 ──────────────────────────────

    def _on_search_history(self) -> None:
        dialog = SearchHistoryDialog(cast(QWidget, self), big_font=self.big_font, small_font=self.small_font)
        dialog.exec()

    # ── 搜索估算信号连接 ─────────────────────────

    def _connect_search_estimate_triggers(self) -> None:
        dock = self.control_dock
        dock.single_skill_scope_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.equipment_scope_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.search_workers_combo.currentTextChanged.connect(self._refresh_search_estimate)
        dock.search_top_n_combo.currentTextChanged.connect(self._refresh_search_estimate)
