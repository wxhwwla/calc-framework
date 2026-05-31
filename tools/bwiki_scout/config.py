#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""BWIKI 侦察默认配置。"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_ROOT = Path(__file__).resolve().parent / "output"
RAW_DIR = OUTPUT_ROOT / "raw"
REPORTS_DIR = OUTPUT_ROOT / "reports"

WIKI_HOST = "wiki.biligame.com"
WIKI_SITE_PATH = "/zmd"
API_URL = f"https://{WIKI_HOST}{WIKI_SITE_PATH}/api.php"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36 "
    "(endfield-damage-calculator-bwiki-scout; +https://github.com/wxhwwla/endfield_damage_calculator_2.0)"
)
REQUEST_INTERVAL_SEC = 1.0
BATCH_PAGE_SIZE = 20

GALLERY_PAGES: dict[str, str] = {
    "operator": "干员图鉴",
    "weapon": "武器图鉴",
    "equipment": "装备图鉴",
}

# 分类补全（若不存在则 API 返回空列表）
CATEGORY_TITLES: dict[str, str] = {
    "operator": "Category:干员",
    "weapon": "Category:武器",
    "equipment": "Category:装备",
}

LOCAL_CHARACTERS_JSON = REPO_ROOT / "adapters" / "endfield" / "data" / "characters.json"
LOCAL_WEAPONS_JSON = REPO_ROOT / "adapters" / "endfield" / "data" / "weapons.json"
LOCAL_EQUIPMENTS_JSON = REPO_ROOT / "adapters" / "endfield" / "data" / "equipments.json"
