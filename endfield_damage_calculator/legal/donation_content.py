#!/usr/bin/env python3
"""自愿捐赠：文案常量与图片路径（无 GUI 依赖）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DONATION_DIR = Path(__file__).resolve().parent

WECHAT_QR_PATH = DONATION_DIR / "wechat_reward.jpg"
"""微信赞赏码图片路径。

使用方法：将微信赞赏码导出为 JPG，命名为 ``wechat_reward.jpg``，
放置在与本文件同目录（``legal/``）下。
"""


@dataclass(frozen=True)
class DonationTier:
    amount: int
    label: str
    description: str


DONATION_TIERS: tuple[DonationTier, ...] = (
    DonationTier(
        amount=2,
        label="¥2.00",
        description="能让作者喝两天的热水（学校一热水瓶一块钱）",
    ),
    DonationTier(
        amount=6,
        label="¥6.90",
        description="能让作者吃上一顿拼好饭",
    ),
    DonationTier(
        amount=9,
        label="¥9.90",
        description="能让作者吃上一顿不错的拼好饭",
    ),
    DonationTier(
        amount=18,
        label="¥18.00",
        description="这是作者用 flash 更新一天代码使用的 token 的量",
    ),
    DonationTier(
        amount=30,
        label="¥30.00",
        description="这是让作者用 pro 更新一天代码的量",
    ),
    DonationTier(
        amount=200,
        label="¥200.00",
        description="如果你真的很喜欢也很有钱的话，这个也不是不行（已经是上限啦）",
    ),
)


DIALOG_SIZE = (480, 560)
DIALOG_MINSIZE = (420, 500)

DIALOG_TITLE = "自愿捐赠"
DIALOG_HEADER = "🤝 请作者喝杯奶茶（实际上作者几乎不喝饮料）"

DIALOG_INTRO = (
    "本工具完全免费开源。如果你觉得好用，欢迎自愿投喂，"
    "支持作者持续维护和更新。\n\n"
    "微信扫码即可捐赠，金额随意，心意无价。"
)

DIALOG_FOOTER = "感谢你的支持 ❤️"
