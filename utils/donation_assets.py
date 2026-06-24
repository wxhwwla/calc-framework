# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""捐赠二维码路径解析（无 Qt 依赖，GUI / Web / WSGI 共用）。"""

from __future__ import annotations

from pathlib import Path

from utils.path_utils import get_resource_path

DONATION_DIR_REL = "resources/donation"

# (展示标签, 候选文件名，按优先级)
DONATION_IMAGE_SLOTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "微信赞赏码",
        (
            "donation_qr.jpg",
            "donation_qr.jpeg",
            "donation_q.jpg",
            "donation_qr.png",
            "donation_qr.webp",
        ),
    ),
    (
        "爱发电",
        (
            "afdian_qr.png",
            "afdian_qr.jpg",
            "afdian_qr.jpeg",
            "afdian_qr.webp",
        ),
    ),
)

# 各槽位首选文件名（文档 / 回退提示用）
WECHAT_DONATION_PREFERRED = "donation_qr.jpg"
AFDIAN_DONATION_PREFERRED = "afdian_qr.png"


def _label_for_filename(name: str) -> str:
    for label, candidates in DONATION_IMAGE_SLOTS:
        if name in candidates:
            return label
    return name


def resolve_donation_images() -> list[dict[str, str]]:
    """解析当前存在的捐赠图，返回 ``file`` / ``label`` / ``rel``。"""
    found: list[dict[str, str]] = []
    for label, candidates in DONATION_IMAGE_SLOTS:
        for name in candidates:
            rel = f"{DONATION_DIR_REL}/{name}"
            if get_resource_path(rel).exists():
                found.append({"file": name, "label": label, "rel": rel})
                break
    return found


def resolve_donation_rel_paths() -> list[str]:
    return [item["rel"] for item in resolve_donation_images()]


def default_wechat_donation_rel() -> str:
    """微信槽位默认路径（用于 layout widget 回退，文件可不存在）。"""
    return f"{DONATION_DIR_REL}/{WECHAT_DONATION_PREFERRED}"


def is_allowed_donation_filename(name: str) -> bool:
    """WSGI 静态文件白名单：仅 donation* / afdian* 且为常见图片后缀。"""
    if not name or "/" in name or "\\" in name or ".." in name:
        return False
    lower = name.lower()
    if not lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return False
    stem = Path(lower).stem
    return stem.startswith("donation") or stem.startswith("afdian")


def caption_for_donation_path(image_path: str) -> str:
    return _label_for_filename(Path(image_path.replace("\\", "/")).name)
