#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""数据来源与许可：文案常量与本地路径（无 GUI 依赖）。"""



from __future__ import annotations

from pathlib import Path

REPO_URL = "https://github.com/wxhwwla/calc-framework"

LICENSE_URL = f"{REPO_URL}/blob/main/LICENSE"

DATA_LICENSE_URL = f"{REPO_URL}/blob/main/DATA_LICENSE"

NOTICES_URL = f"{REPO_URL}/blob/main/NOTICES.md"

ATTRIBUTION_DOC_URL = f"{REPO_URL}/blob/main/docs/%E6%95%B0%E6%8D%AE%E6%9D%A5%E6%BA%90%E4%B8%8E%E8%AE%B8%E5%8F%AF.md"

COMMERCIAL_OUTLINE_URL = f"{REPO_URL}/blob/main/docs/%E5%95%86%E4%B8%9A%E8%AE%B8%E5%8F%AF%E8%A6%81%E7%82%B9.md"

BWIKI_ZMD_URL = "https://wiki.biligame.com/zmd/"

CC_BY_SA_40_URL = "https://creativecommons.org/licenses/by-sa/4.0/deed.zh"

AGPL_30_URL = "https://www.gnu.org/licenses/agpl-3.0.html"

COMMERCIAL_CONTACT = "wxhwwla@gmail.com"



ATTRIBUTION_DIALOG_SIZE = (620, 760)

ATTRIBUTION_DIALOG_MINSIZE = (560, 700)

ATTRIBUTION_TEXTBOX_HEIGHT = 200



SUMMARY_TEXT = (

    "【非官方工具】\n"

    "本程序为爱好者计算器，不代表游戏官方或 BWIKI 运营方。\n"

    "使用本程序或数据即表示您已阅读相关许可。\n"

    "\n"

    "【数据来源】\n"

    f"· JSON：本仓库维护（非商业可随软件使用）\n"

    f"· 参考：终末地 BWIKI {BWIKI_ZMD_URL}\n"

    f"· 游戏名称、数值、美术等：版权归游戏权利方\n"

    "\n"

    "【数据许可 DATA_LICENSE】\n"

    "· 仅授权数据「整理编排」，不授予游戏官方 IP\n"

    "· 须同时遵守游戏协议、BWIKI / CC BY-SA 4.0\n"

    "· 商用：禁止使用本仓库 JSON 与 bwiki_scout 采集流程\n"

    "· 商用方须自行合法获数，不得声称来自本项目商业许可\n"

    "\n"

    "【软件许可 LICENSE】\n"

    f"· 默认 AGPL-3.0（再分发 / 网络服务须满足开源义务）\n"

    f"· 闭源或免开源义务商用：须书面商业许可（{COMMERCIAL_CONTACT}）\n"

    "· 商业许可不包含游戏数据\n"

    "\n"

    "【免责声明】\n"

    "数据与计算结果仅供参考，不保证与游戏内一致。\n"

    "\n"

    "详细条款、典型情形与合规清单见下方链接。"

)





def attribution_doc_local_path() -> Path:

    return Path(__file__).resolve().parent.parent.parent.parent.parent / "docs" / "数据来源与许可.md"
    """attribution doc local path。"""





def data_license_local_path() -> Path:

    return Path(__file__).resolve().parent.parent.parent.parent.parent / "DATA_LICENSE"
    """data license local path。"""





def notices_local_path() -> Path:

    return Path(__file__).resolve().parent.parent.parent.parent.parent / "NOTICES.md"
    """notices local path。"""





def local_or_remote(local: Path, remote: str) -> str:

    return local.as_uri() if local.is_file() else remote
    """local or remote。"""

