#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 主应用壳层

DamageCalculatorApp 通过 mixin 组合布局、选择联动、高级页控件与配装刮取；
具体实现见 ``gui_design.shell.app_*`` 子模块。
"""

from utils.platform_win32_patch import apply_platform_win32_patch

apply_platform_win32_patch()

import customtkinter as ctk
from typing import Any, Dict, List, Optional

from calculation.search_cancel import SearchCancelToken
from calculation.single_skill_search_job import build_weapon_candidates
from data.game_data_facade import GameDataFacade
from gui_design.calc_mode_labels import DEFAULT_CALC_MODE_LABEL
from gui_design.confirm_orchestrator import schedule_confirm
from gui_design.gui_settings import gui_settings
from gui_design.loadout_pending import mark_loadout_pending
from gui_design.panels.selection_panel import ChooseTypesStarsNamesLevels
from gui_design.search_settings import build_worker_option_labels
from gui_design.shell.app_char_weapon_link import AppCharWeaponLinkMixin
from gui_design.shell.app_control_dock import AppControlDockMixin
from gui_design.shell.app_loadout_access import AppLoadoutAccessMixin
from gui_design.shell.app_loadout_bridge import AppLoadoutBridgeMixin
from gui_design.shell.app_main_layout import AppMainLayoutMixin
from gui_design.shell.app_selection import AppSelectionMixin
from gui_design.shell.app_window import AppWindowMixin
from gui_design.shell.app_window_events import AppWindowEventsMixin
from gui_design.ui_preferences import load_ui_preferences
from please_read_me import get_exe_version
from utils.gui_fonts import default_ui_font
from utils.gui_window import apply_startup_maximized

__all__ = [
    "DamageCalculatorApp",
    "build_weapon_candidates",
    "main",
    "mark_loadout_pending",
    "schedule_confirm",
]


class DamageCalculatorApp(
    AppMainLayoutMixin,
    AppSelectionMixin,
    AppWindowMixin,
    AppWindowEventsMixin,
    AppCharWeaponLinkMixin,
    AppControlDockMixin,
    AppLoadoutBridgeMixin,
    AppLoadoutAccessMixin,
):
    """
    终末地伤害计算小工具主应用类

    双页签：计算页（五列主视图）与高级页（操作 / 全量搜索 / 多技能次数）。
    """

    def __init__(self) -> None:
        gui_settings()

        self.app: ctk.CTk = ctk.CTk()
        self.app.geometry("1280x720")
        self.app.title(f"终末地伤害计算小工具 v{get_exe_version()}")
        self.app.minsize(1024, 600)

        self.app.bind("<Configure>", self._on_window_resize)
        self.app.bind("<Map>", self._on_window_map, add="+")
        self.app.bind("<Unmap>", self._on_window_unmap, add="+")

        self.big_font: ctk.CTkFont = default_ui_font(size=14, weight="bold")
        self.small_font: ctk.CTkFont = default_ui_font(size=12)

        self.char_frame: Optional[ctk.CTkFrame] = None
        self.weapon_frame: Optional[ctk.CTkFrame] = None
        self.page_tabs: Optional[ctk.CTkTabview] = None
        self.main_page_frame: Optional[ctk.CTkFrame] = None
        self.advanced_page_frame: Optional[ctk.CTkFrame] = None
        self.control_frame: Optional[ctk.CTkFrame] = None
        self._control_dock_body: Optional[ctk.CTkFrame] = None
        self._control_col_actions: Optional[ctk.CTkFrame] = None
        self._control_col_search: Optional[ctk.CTkFrame] = None
        self._control_col_multi: Optional[ctk.CTkFrame] = None
        self.goto_advanced_btn: Optional[ctk.CTkButton] = None
        self.main_confirm_btn: Optional[ctk.CTkButton] = None
        self.back_to_main_btn: Optional[ctk.CTkButton] = None
        self.confirm_btn: Optional[ctk.CTkButton] = None
        self.attribution_btn: Optional[ctk.CTkButton] = None
        self.mvp_search_btn: Optional[ctk.CTkButton] = None
        self.full_search_btn: Optional[ctk.CTkButton] = None
        self.search_workers_var: ctk.StringVar = ctk.StringVar(
            value=build_worker_option_labels()[0]
        )
        self.search_top_n_var: ctk.StringVar = ctk.StringVar(value="10")
        self.search_workers_menu: Optional[ctk.CTkOptionMenu] = None
        self.search_workers_hint_label: Optional[ctk.CTkLabel] = None
        self.search_top_n_menu: Optional[ctk.CTkOptionMenu] = None
        self.search_cancel_btn: Optional[ctk.CTkButton] = None
        self._search_cancel_token: Optional[SearchCancelToken] = None
        self._search_estimated_total_seconds: float = 0.0
        self.search_estimate_label: Optional[ctk.CTkLabel] = None
        self.mvp_status_label: Optional[ctk.CTkLabel] = None
        self.calc_mode_var: ctk.StringVar = ctk.StringVar(value=DEFAULT_CALC_MODE_LABEL)
        self.calc_mode_menu: Optional[ctk.CTkOptionMenu] = None
        self.use_manual_skill_counts_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.damage_component_mode_var: ctk.StringVar = ctk.StringVar(value="技能+异常")
        self.use_expected_crit_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.include_conditional_equipment_crit_var: ctk.BooleanVar = ctk.BooleanVar(value=False)
        self.extra_crit_rate_percent_var: ctk.StringVar = ctk.StringVar(value="0")
        self.extra_crit_damage_percent_var: ctk.StringVar = ctk.StringVar(value="0")
        self.single_skill_scope_var: ctk.StringVar = ctk.StringVar(value="当前武器")
        self.single_skill_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self.single_skill_equipment_scope_var: ctk.StringVar = ctk.StringVar(value="全部装备")
        self.single_skill_equipment_scope_menu: Optional[ctk.CTkOptionMenu] = None
        self._fixed_loadout_slots: Dict[str, Any] = {}
        self._fixed_loadout_frame: Optional[ctk.CTkFrame] = None
        self.skill_count_1_var: ctk.StringVar = ctk.StringVar(value="0")
        self.skill_count_2_var: ctk.StringVar = ctk.StringVar(value="0")
        self.skill_count_3_var: ctk.StringVar = ctk.StringVar(value="0")
        self._segment_count_vars: Dict[str, ctk.StringVar] = {}
        self._physical_abnormal_count_vars: Dict[str, ctk.StringVar] = {}
        self._spell_abnormal_count_vars: Dict[str, ctk.StringVar] = {}
        self._multi_skill_counts_body: Optional[ctk.CTkFrame] = None
        self.char_attr_frame: Optional[ctk.CTkFrame] = None
        self.char_attr_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.weapon_attr_frame: Optional[ctk.CTkFrame] = None
        self.weapon_attr_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.right_frame: Optional[ctk.CTkFrame] = None
        self.right_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.char_panel: Optional[ChooseTypesStarsNamesLevels] = None
        self.weapon_panel: Optional[ChooseTypesStarsNamesLevels] = None
        self.game_data: GameDataFacade = GameDataFacade.create()
        self.all_weapons: List[Dict[str, Any]] = list(self.game_data.weapons)
        self._confirm_refresh_signature: Optional[tuple] = None
        self._confirmed_display_signature: Optional[tuple] = None
        self._confirm_after_id: Optional[str] = None
        self._pending_ui_after_id: Optional[str] = None
        self._confirm_button_default_styles: dict[int, tuple] = {}
        self._skill_count_last_committed: Dict[str, str] = {}
        self._suppress_full_confirm_refresh: bool = False
        self._ui_preferences: Dict[str, Any] = load_ui_preferences()
        self._control_dock_last_width: Optional[int] = None
        self._control_dock_last_compact: Optional[bool] = None
        self._restore_settling: bool = False
        self._restore_after_id: Optional[str] = None
        self._window_has_been_mapped: bool = False

        self._setup_ui()
        self.app.protocol("WM_DELETE_WINDOW", self._on_close)

    def run(self) -> None:
        """启动主事件循环（启动后最大化窗口）。"""
        apply_startup_maximized(self.app)
        self.app.mainloop()


def main() -> None:
    app = DamageCalculatorApp()
    app.run()


if __name__ == "__main__":
    main()
