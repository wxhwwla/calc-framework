#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据来源与许可：文案常量及 GUI 对话框。"""

from __future__ import annotations

import webbrowser
from pathlib import Path

import customtkinter as ctk

REPO_URL = "https://github.com/wxhwwla/endfield_damage_calculator_2.0"
LICENSE_URL = f"{REPO_URL}/blob/main/LICENSE"
DATA_LICENSE_URL = f"{REPO_URL}/blob/main/DATA_LICENSE"
NOTICES_URL = f"{REPO_URL}/blob/main/NOTICES.md"
ATTRIBUTION_DOC_URL = (
    f"{REPO_URL}/blob/main/docs/%E6%95%B0%E6%8D%AE%E6%9D%A5%E6%BA%90%E4%B8%8E%E8%AE%B8%E5%8F%AF.md"
)
COMMERCIAL_OUTLINE_URL = (
    f"{REPO_URL}/blob/main/docs/"
    "%E5%95%86%E4%B8%9A%E8%AE%B8%E5%8F%AF%E8%A6%81%E7%82%B9.md"
)
BWIKI_ZMD_URL = "https://wiki.biligame.com/zmd/"
CC_BY_SA_40_URL = "https://creativecommons.org/licenses/by-sa/4.0/deed.zh"
AGPL_30_URL = "https://www.gnu.org/licenses/agpl-3.0.html"
COMMERCIAL_CONTACT = "wxhwwla@gmail.com"

# 默认尺寸须容纳简略正文 + 全部链接按钮；过小会导致底部按钮被裁切
ATTRIBUTION_DIALOG_SIZE = (620, 760)
ATTRIBUTION_DIALOG_MINSIZE = (560, 700)
ATTRIBUTION_TEXTBOX_HEIGHT = 200

SUMMARY_TEXT = """【非官方工具】
本程序为爱好者计算器，不代表游戏官方或 BWIKI 运营方。
使用本程序或数据即表示您已阅读相关许可。

【数据来源】
· JSON：本仓库维护（非商业可随软件使用）
· 参考：终末地 BWIKI """ + BWIKI_ZMD_URL + """
· 游戏名称、数值、美术等：版权归游戏权利方

【数据许可 DATA_LICENSE】
· 仅授权数据「整理编排」，不授予游戏官方 IP
· 须同时遵守游戏协议、BWIKI / CC BY-SA 4.0
· 商用：禁止使用本仓库 JSON 与 bwiki_scout 采集流程
· 商用方须自行合法获数，不得声称来自本项目商业授权

【软件许可 LICENSE】
· 默认 AGPL-3.0（再分发 / 网络服务须满足开源义务）
· 闭源或免开源义务商用：须书面商业许可（""" + COMMERCIAL_CONTACT + """）
· 商业许可不包含游戏数据

【免责声明】
数据与计算结果仅供参考，不保证与游戏内一致。

详细条款、典型情形与合规清单见下方链接。"""


def attribution_doc_local_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "docs" / "数据来源与许可.md"


def data_license_local_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "DATA_LICENSE"


def notices_local_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "NOTICES.md"


def _local_or_remote(local: Path, remote: str) -> str:
    return local.as_uri() if local.is_file() else remote


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

    body_font = small_font or ctk.CTkFont(family="微软雅黑", size=12)
    title_font = font or ctk.CTkFont(family="微软雅黑", size=14, weight="bold")

    # 自下而上 pack，避免 expand 文本框挤占底部按钮区域
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

    _row("完整说明（含典型情形对照）", _local_or_remote(attribution_doc_local_path(), ATTRIBUTION_DOC_URL))
    _row("软件许可 LICENSE", _local_or_remote(Path(__file__).resolve().parent.parent.parent / "LICENSE", LICENSE_URL))
    _row("数据许可 DATA_LICENSE", _local_or_remote(data_license_local_path(), DATA_LICENSE_URL))
    _row("第三方声明 NOTICES", _local_or_remote(notices_local_path(), NOTICES_URL))
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
