#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""PySide6 搜索线程与结果弹窗。"""



from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from games.endfield.calc.loadout.optimizer import LoadoutScore
from games.endfield.calc.manual_buff.physical import (
    format_abnormal_breakdown_lines,
    split_damage_breakdown,
)
from games.endfield.calc.manual_buff.spell import (
    format_spell_abnormal_breakdown_lines,
    is_spell_abnormal_key,
)
from games.endfield.calc.search.plan.controller import (
    optimizer_config_for_search_job,
)
from games.endfield.calc.search.plan.job import SingleSkillSearchJob
from games.endfield.calc.search.run.cancel import SearchCancelToken
from games.endfield.calc.search.run.single_skill import (
    run_exported_single_skill_search,
)
from games.endfield.calc.skills.segments import (
    aggregate_weighted_damage,
    format_segment_breakdown_lines,
)
from gui.controls.search.search_settings import (
    format_search_progress_text,
    resolve_parallel_workers,
    resolve_top_n,
)
from gui.presentation.search_results_lines import (
    export_paths_to_strings,
)

# ═══════════════════════════════════════════════════════

#  搜索线程 Worker

# ═══════════════════════════════════════════════════════





class SearchWorker(QObject):

    """在 QThread 中执行全量遍历搜索。"""



    progress = Signal(str)

    finished = Signal(object, object, object, object)  # mode_label, job, outcome, export_paths

    error = Signal(str)



    def __init__(

        self,

        job: SingleSkillSearchJob,

        *,

        mode_label: str,

        export_root: Path,

        top_n_choice: str,

        workers_choice: str,

        status_prefix: str,

        cancel_token: SearchCancelToken,

    ) -> None:

        super().__init__()

        self._job = job

        self._mode_label = mode_label

        self._export_root = export_root

        self._top_n = resolve_top_n(top_n_choice)

        self._max_workers = resolve_parallel_workers(workers_choice)

        self._status_prefix = status_prefix

        self._cancel_token = cancel_token



    def run(self) -> None:

        """在 QThread 中执行全量遍历搜索，发射 progress/finished/error 信号。"""

        config = optimizer_config_for_search_job(self._job, top_n=self._top_n)



        def _progress(info: dict) -> None:
            processed = int(info.get("processed", 0))
            total = int(info.get("total", 0))
            speed = float(info.get("speed_per_sec", 0))
            eta_seconds = float(info.get("eta_seconds", 0.0))
            estimated_total = (total / speed) if speed > 0 and total > 0 else 0
            text = format_search_progress_text(
                prefix=self._status_prefix,
                processed=processed,
                total=total,
                eta_seconds=eta_seconds,
                estimated_total_seconds=estimated_total,
            )
            self.progress.emit(text)



        try:

            outcome = run_exported_single_skill_search(

                self._job,

                export_root=self._export_root,

                config=config,

                max_workers=self._max_workers,

                cancel_token=self._cancel_token,

                progress_callback=_progress,

            )

        except Exception as exc:

            self.error.emit(str(exc))

            return



        export_paths = export_paths_to_strings(outcome.exports or {})

        export_paths["数据库"] = str(outcome.db_path)

        export_paths["导出目录"] = str(outcome.export_dir)



        self.finished.emit(self._mode_label, self._job, outcome, export_paths)





# ═══════════════════════════════════════════════════════

#  搜索弹窗

# ═══════════════════════════════════════════════════════



_DARK_BG = "#1E1E1E"

_DARK_FG = "#D1D1D1"

_ACCENT = "#2B6CB6"

_HEADER_BG = "#2A2A2A"

_SEG_FG = QColor("#9BB9E0")

_ABNORMAL_FG = QColor("#C9A96E")





def _build_tree_items(

    lines: list[str],

    top_results: Sequence[LoadoutScore] | None,

    *,

    damage_metric: str,

    segment_counts: dict[str, int] | None,

    abnormal_counts: dict[str, int] | None,

    spell_abnormal_counts: dict[str, int] | None,

) -> list[QTreeWidgetItem]:

    """构建搜索结果树节点。



    当提供 top_results 时生成结构化树；否则退化为纯文本 flat 列表。

    """

    items: list[QTreeWidgetItem] = []



    if not top_results:

        for line in lines:

            item = QTreeWidgetItem([line])

            item.setFlags(Qt.ItemFlag.ItemIsEnabled)

            items.append(item)

        return items



    for idx, score in enumerate(top_results, start=1):

        loadout = score.loadout_names

        header_text = (

            f"第{idx}名: {score.weapon_name}  |  "

            f"{damage_metric} {score.final_damage:.1f}  |  "

            f"护甲 {loadout.get('chest', '')}  |  "

            f"护手 {loadout.get('gloves', '')}  |  "

            f"配件A {loadout.get('accessory_a', '')}  |  "

            f"配件B {loadout.get('accessory_b', '')}"

        )

        root = QTreeWidgetItem([header_text])

        root.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsAutoTristate)

        root.setExpanded(idx <= 3)



        if score.segment_breakdown and (segment_counts or abnormal_counts):

            base_skill_breakdown, physical_abnormal_breakdown = split_damage_breakdown(

                score.segment_breakdown

            )

            spell_abnormal_breakdown: dict[str, float] = {}

            skill_breakdown: dict[str, float] = {}

            for key, value in base_skill_breakdown.items():

                if is_spell_abnormal_key(key):

                    spell_abnormal_breakdown[key] = value

                else:

                    skill_breakdown[key] = value



            if skill_breakdown and segment_counts:

                breakdown_lines = format_segment_breakdown_lines(

                    skill_breakdown, segment_counts, indent=""

                )

                for b_line in breakdown_lines:

                    child = QTreeWidgetItem([b_line])

                    child.setForeground(0, _SEG_FG)

                    child.setFlags(Qt.ItemFlag.ItemIsEnabled)

                    root.addChild(child)



                weighted_total, _, skill_type_totals = aggregate_weighted_damage(

                    skill_breakdown, segment_counts

                )

                if len(skill_type_totals) > 1:

                    parts = [f"{k} {v:.1f}" for k, v in skill_type_totals.items()]

                    total_line = QTreeWidgetItem([f"加权合计: {weighted_total:.1f}（{' + '.join(parts)}）"])

                else:

                    total_line = QTreeWidgetItem([f"加权合计: {weighted_total:.1f}"])

                total_line.setFlags(Qt.ItemFlag.ItemIsEnabled)

                root.addChild(total_line)



            if physical_abnormal_breakdown and abnormal_counts:

                ab_lines = format_abnormal_breakdown_lines(

                    physical_abnormal_breakdown, abnormal_counts, indent=""

                )

                for ab_line in ab_lines:

                    child = QTreeWidgetItem([ab_line])

                    child.setForeground(0, _ABNORMAL_FG)

                    child.setFlags(Qt.ItemFlag.ItemIsEnabled)

                    root.addChild(child)



            if spell_abnormal_breakdown and spell_abnormal_counts:

                sp_lines = format_spell_abnormal_breakdown_lines(

                    spell_abnormal_breakdown, spell_abnormal_counts, indent=""

                )

                for sp_line in sp_lines:

                    child = QTreeWidgetItem([sp_line])

                    child.setForeground(0, _ABNORMAL_FG)

                    child.setFlags(Qt.ItemFlag.ItemIsEnabled)

                    root.addChild(child)



        items.append(root)



    return items





class QtSearchResultsDialog(QDialog):

    """全量 / MVP 搜索结果展示弹窗（结构化树视图）。"""



    def __init__(

        self,

        parent: QWidget | None = None,

        *,

        title: str,

        lines: list[str],

        big_font: QFont,

        small_font: QFont,

        top_results: Sequence[LoadoutScore] | None = None,

        damage_metric: str = "伤害",

        segment_counts: dict[str, int] | None = None,

        abnormal_counts: dict[str, int] | None = None,

        spell_abnormal_counts: dict[str, int] | None = None,

    ) -> None:

        super().__init__(parent)

        self.setWindowTitle(title)

        self.resize(960, 760)

        self.setMinimumSize(680, 480)



        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 12, 12, 12)



        tree = QTreeWidget()

        tree.setFont(small_font)

        tree.setHeaderLabels(["搜索结果"])

        tree.header().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        tree.header().setVisible(False)

        tree.setAlternatingRowColors(True)

        tree.setStyleSheet(f"""

            QTreeWidget {{

                background-color: {_DARK_BG}; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 4px;

                alternate-background-color: #252525;

            }}

            QTreeWidget::item {{

                padding: 3px 4px;

                border-bottom: 1px solid #333;

            }}

            QTreeWidget::item:selected {{

                background-color: {_ACCENT}; color: white;

            }}

            QTreeWidget::branch:has-children:!has-siblings:closed,

            QTreeWidget::branch:closed:has-children:has-siblings {{

                border-image: none;

                image: none;

            }}

            QTreeWidget::branch:open:has-children:!has-siblings,

            QTreeWidget::branch:open:has-children:has-siblings {{

                border-image: none;

                image: none;

            }}

        """)

        tree.setIndentation(20)

        tree.setAnimated(True)

        tree.setRootIsDecorated(True)



        tree_items = _build_tree_items(

            lines, top_results,

            damage_metric=damage_metric,

            segment_counts=segment_counts,

            abnormal_counts=abnormal_counts,

            spell_abnormal_counts=spell_abnormal_counts,

        )

        for item in tree_items:

            tree.addTopLevelItem(item)



        layout.addWidget(tree, stretch=1)



        info_label = QPushButton(

            f"共 {len(top_results) if top_results else 0} 个结果  |  "

            f"前 {min(3, len(top_results) if top_results else 0)} 项已展开"

            if top_results else ""

        )

        info_label.setFont(small_font)

        info_label.setStyleSheet("""

            QPushButton {

                background-color: transparent; color: #888;

                border: none; text-align: left; padding: 2px 0;

            }

        """)

        info_label.setEnabled(False)

        layout.addWidget(info_label)



        btn_row = QHBoxLayout()

        btn_row.addStretch()

        close_btn = QPushButton("关闭")

        close_btn.setFont(small_font)

        close_btn.setStyleSheet(f"""

            QPushButton {{

                background-color: transparent; color: {_DARK_FG};

                border: 1px solid #464646; border-radius: 6px;

                padding: 6px 24px;

            }}

            QPushButton:hover {{ border-color: {_ACCENT}; color: white; }}

        """)

        close_btn.clicked.connect(self.accept)

        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

