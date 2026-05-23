#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据来源与许可：CTk 对话框（常量见 attribution_content）。"""

from __future__ import annotations

import webbrowser
from pathlib import Path

import customtkinter as ctk

from legal.attribution_content import (
    AGPL_30_URL,
    ATTRIBUTION_DIALOG_MINSIZE,
    ATTRIBUTION_DIALOG_SIZE,
    ATTRIBUTION_DOC_URL,
    ATTRIBUTION_TEXTBOX_HEIGHT,
    BWIKI_ZMD_URL,
    CC_BY_SA_40_URL,
    COMMERCIAL_OUTLINE_URL,
    DATA_LICENSE_URL,
    LICENSE_URL,
    NOTICES_URL,
    SUMMARY_TEXT,
    attribution_doc_local_path,
    data_license_local_path,
    local_or_remote,
    notices_local_path,
)

__all__ = (
    "AGPL_30_URL",
    "ATTRIBUTION_DIALOG_MINSIZE",
    "ATTRIBUTION_DIALOG_SIZE",
    "ATTRIBUTION_DOC_URL",
    "ATTRIBUTION_TEXTBOX_HEIGHT",
    "BWIKI_ZMD_URL",
    "CC_BY_SA_40_URL",
    "COMMERCIAL_OUTLINE_URL",
    "COMMERCIAL_CONTACT",
    "DATA_LICENSE_URL",
    "LICENSE_URL",
    "NOTICES_URL",
    "REPO_URL",
    "SUMMARY_TEXT",
    "attribution_doc_local_path",
    "data_license_local_path",
    "notices_local_path",
    "open_attribution_dialog",
)

# 兼容旧 import 路径
from legal.attribution_content import (  # noqa: E402
    COMMERCIAL_CONTACT,
    REPO_URL,
)


def open_attribution_dialog(
    parent: ctk.CTk | ctk.CTkToplevel,
    *,
    font: ctk.CTkFont | None = None,
    small_font: ctk.CTkFont | None = None,
) -> ctk.CTkToplevel:
    """打开「数据来源与许可」模态窗口。"""
    dialog = ctk.CTkToplevel(parent)
    dialog.title("数据来源与许可")
    w, h = ATTRIBUTION_DIALOG_SIZE
    dialog.geometry(f"{w}x{h}")
    dialog.minsize(*ATTRIBUTION_DIALOG_MINSIZE)
    dialog.transient(parent)
    dialog.grab_set()

    from utils.gui_fonts import default_ui_font

    body_font = small_font or default_ui_font(size=12)
    title_font = font or default_ui_font(size=14, weight="bold")

    ctk.CTkButton(dialog, text="关闭", font=body_font, command=dialog.destroy).pack(
        side="bottom", pady=(0, 16)
    )

    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(side="bottom", fill="x", padx=16, pady=(4, 8))

    def _row(label: str, url: str) -> None:
        ctk.CTkButton(
            btn_frame,
            text=label,
            font=body_font,
            command=lambda u=url: webbrowser.open(u),
        ).pack(fill="x", pady=3)

    _row(
        "完整说明（含典型情形对照）",
        local_or_remote(attribution_doc_local_path(), ATTRIBUTION_DOC_URL),
    )
    _row(
        "软件许可 LICENSE",
        local_or_remote(Path(__file__).resolve().parent.parent.parent / "LICENSE", LICENSE_URL),
    )
    _row("数据许可 DATA_LICENSE", local_or_remote(data_license_local_path(), DATA_LICENSE_URL))
    _row("第三方声明 NOTICES", local_or_remote(notices_local_path(), NOTICES_URL))
    _row("商业许可洽谈要点（非合同）", COMMERCIAL_OUTLINE_URL)
    _row("AGPL-3.0 全文", AGPL_30_URL)
    _row("终末地 BWIKI", BWIKI_ZMD_URL)
    _row("CC BY-SA 4.0", CC_BY_SA_40_URL)

    ctk.CTkLabel(dialog, text="数据来源与许可（简略）", font=title_font).pack(
        side="top", padx=16, pady=(16, 8), anchor="w"
    )

    textbox = ctk.CTkTextbox(
        dialog, font=body_font, wrap="word", height=ATTRIBUTION_TEXTBOX_HEIGHT
    )
    textbox.pack(side="top", fill="both", expand=True, padx=16, pady=8)
    textbox.insert("1.0", SUMMARY_TEXT)
    textbox.configure(state="disabled")

    dialog.update_idletasks()
    return dialog
