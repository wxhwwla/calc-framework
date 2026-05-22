#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BWIKI 侦察模块测试（纯函数与离线 fixture，不访问网络）。"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from bwiki_scout.gallery import extract_gallery_entry_titles, merge_title_lists  # noqa: E402
from bwiki_scout.json_scan import find_json_hints  # noqa: E402
from bwiki_scout.local_schema import compare_name_sets, summarize_local_schema  # noqa: E402
from bwiki_scout.names import normalize_name_for_match  # noqa: E402
from bwiki_scout.parse_draft import build_draft_record, extract_template_params  # noqa: E402
from bwiki_scout.scout import run_scout  # noqa: E402
from bwiki_scout.storage import save_page_bundle  # noqa: E402

_PKG = _REPO_ROOT / "endfield_damage_calculator"
_CHARS = _PKG / "character_weapon_equipment" / "character_data" / "characters.json"
_WEAPONS = _PKG / "character_weapon_equipment" / "weapon_data" / "weapons.json"


class TestParseDraft(unittest.TestCase):
    def test_extract_template_params(self):
        params = extract_template_params("{{干员|名称=秋栗|稀有度=4星|职业=术师}}")
        self.assertEqual(params["名称"], "秋栗")
        self.assertEqual(params["稀有度"], "4星")

    def test_build_draft_operator_lists_missing_local_fields(self):
        record = build_draft_record(
            kind="operator",
            title="秋栗",
            wikitext="{{干员|名称=秋栗}}",
            meta={"pageid": 1},
        )
        self.assertEqual(record["名称"], "秋栗")
        self.assertIn("战技倍率", record["_missing_local_fields"])


class TestJsonScan(unittest.TestCase):
    def test_find_json_hints_detects_json_extension(self):
        hints = find_json_hints("链接到 [[数据.json]] 文件")
        self.assertTrue(hints["link_hits"])


class TestGallery(unittest.TestCase):
    def test_extract_skips_index_php(self):
        html = '<a href="/zmd/index.php">坏链</a><a href="/zmd/%E7%A7%8B%E6%A0%97">秋栗</a>'
        titles = extract_gallery_entry_titles(html)
        self.assertNotIn("index.php", titles)
        self.assertIn("秋栗", titles)

    def test_merge_category_before_gallery(self):
        merged = merge_title_lists(["分类A"], ["图鉴A", "分类A"])
        self.assertEqual(merged[0], "分类A")
        self.assertEqual(len(merged), 2)


class TestNames(unittest.TestCase):
    def test_normalize_strips_spaces(self):
        self.assertEqual(normalize_name_for_match(" 赫拉芬格 "), "赫拉芬格")


class TestLocalSchema(unittest.TestCase):
    def test_summarize_local_schema_reads_files(self):
        summary = summarize_local_schema(_CHARS, _WEAPONS)
        self.assertGreater(summary["operator"]["count"], 0)
        self.assertGreater(summary["weapon"]["count"], 0)

    def test_compare_name_sets(self):
        diff = compare_name_sets(
            {"秋栗", "仅Wiki"},
            {"秋栗"},
            normalize=normalize_name_for_match,
        )
        matched_names = [m["local_name"] for m in diff["matched"]]
        self.assertIn("秋栗", matched_names)
        self.assertIn("仅Wiki", diff["only_wiki"])


class TestRunScoutOffline(unittest.TestCase):
    def test_run_scout_writes_manifest_and_reports(self):
        from bwiki_scout.config import GALLERY_PAGES

        class FakeClient:
            def fetch_parsed_gallery_html(self, page: str) -> str:
                if page == GALLERY_PAGES["operator"]:
                    return '<a href="/zmd/%E7%A7%8B%E6%A0%97">秋栗</a>'
                if page == GALLERY_PAGES["weapon"]:
                    return '<a href="/zmd/%E9%A2%86%E8%88%AA%E8%80%85">领航者</a>'
                if page == GALLERY_PAGES["equipment"]:
                    return '<a href="/zmd/%E8%A3%85%E5%A4%87A">装备A</a>'
                return ""

            def fetch_category_members(self, category_title: str) -> list[str]:
                return []

            def fetch_pages_content(self, titles: list[str]) -> dict:
                return {
                    t: {
                        "title": t,
                        "pageid": 1,
                        "ns": 0,
                        "wikitext": "{{干员|名称=" + t + "}}",
                        "html": f"<p>{t}</p>",
                    }
                    for t in titles
                }

            def search_json_file_candidates(self) -> list[str]:
                return []

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            result = run_scout(
                output_root=out,
                client=FakeClient(),
                per_kind_limit=1,
            )
            self.assertTrue((out / "manifest.json").is_file())
            self.assertTrue((out / "reports" / "summary.md").is_file())
            self.assertGreater(result["page_count"], 0)


if __name__ == "__main__":
    unittest.main()
