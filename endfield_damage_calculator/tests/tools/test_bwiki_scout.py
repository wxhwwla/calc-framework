#!/usr/bin/env python3
"""BWIKI 侦察模块测试（纯函数与离线 fixture，不访问网络）。"""

import tempfile
import unittest
from pathlib import Path

from bwiki_scout.detail_levels import (  # noqa: E402
    compare_operator_to_local,
    operator_detail_title,
    parse_operator_detail_wikitext,
)
from bwiki_scout.gallery import extract_gallery_entry_titles, merge_title_lists  # noqa: E402
from bwiki_scout.json_scan import find_json_hints  # noqa: E402
from bwiki_scout.local_schema import compare_name_sets, summarize_local_schema  # noqa: E402
from bwiki_scout.names import normalize_name_for_match  # noqa: E402
from bwiki_scout.parse_draft import build_draft_record, extract_template_params  # noqa: E402
from bwiki_scout.scout import run_scout  # noqa: E402

from tests.fixtures.path_roots import PKG_ROOT

_CHARS = PKG_ROOT / "character_weapon_equipment" / "character_data" / "characters.json"
_WEAPONS = PKG_ROOT / "character_weapon_equipment" / "weapon_data" / "weapons.json"


_DETAIL_FIXTURE = """{{干员/逐级等级|
| 力量1 = 21 | 敏捷1 = 9 | 智识1 = 8 | 意志1 = 11
| 攻击1 = 30 | 生命1 = 500 | 防御1 = 0
| 力量90 = 176 | 敏捷90 = 96 | 智识90 = 86 | 意志90 = 106
| 攻击90 = 300 | 生命90 = 5495 | 防御90 = 0
}}"""


class TestDetailLevels(unittest.TestCase):
    def test_operator_detail_title(self):
        self.assertEqual(operator_detail_title("秋栗"), "秋栗/详细数据")

    def test_parse_operator_detail_wikitext_extracts_attack_curve(self):
        curves = parse_operator_detail_wikitext(_DETAIL_FIXTURE, max_level=90)
        self.assertEqual(curves["levels"][0], 1)
        self.assertEqual(curves["levels"][-1], 90)
        self.assertEqual(curves["基础攻击力"][0], 30)
        self.assertEqual(curves["基础攻击力"][89], 300)
        self.assertIsNone(curves["基础攻击力"][1])

    def test_compare_operator_to_local_flags_mismatch(self):
        wiki = parse_operator_detail_wikitext(_DETAIL_FIXTURE, max_level=90)
        local = {
            "名称": "测试",
            "等级": list(range(1, 91)),
            "基础攻击力": [31] + [0.0] * 88 + [300.0],
            "力量": [0.0] * 90,
            "敏捷": [0.0] * 90,
            "智识": [0.0] * 90,
            "意志": [0.0] * 90,
        }
        summary = compare_operator_to_local(
            operator_name="测试",
            wiki_curves=wiki,
            local_record=local,
            fields=("基础攻击力",),
        )
        self.assertGreater(summary["mismatch_count"], 0)
        self.assertEqual(summary["mismatches"][0]["level"], 1)


class TestParseDraft(unittest.TestCase):
    def test_extract_template_params(self):
        params = extract_template_params("{{干员|名称=秋栗|稀有度=4星|职业=术师}}")
        self.assertEqual(params["名称"], "秋栗")
        self.assertEqual(params["稀有度"], "4星")

    def test_extract_template_params_multiline_value(self):
        wikitext = (
            "{{武器|词条3内容=攻击力+5.0%。\n"
            "同名效果最多叠加2层，每层单独计算持续时间。\n"
            "|词条3副2内容=造成物理异常时获得攻击力}}"
        )
        params = extract_template_params(wikitext)
        self.assertIn("同名效果最多叠加2层", params["词条3内容"])
        self.assertEqual(params["词条3副2内容"], "造成物理异常时获得攻击力")
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


class TestWeaponWikiRankCurveFit(unittest.TestCase):
    def test_steel_echo_conditional_curve_fits_and_bakes(self) -> None:
        from bwiki_scout.weapon_wiki import (  # noqa: E402
            bake_rank_curve_from_params,
            fit_bonus_params_from_rank_curve,
        )

        wiki = [7.5, 9.0, 10.5, 12.0, 13.5, 15.0, 16.5, 18.0, 21.0]
        params = fit_bonus_params_from_rank_curve(wiki)
        self.assertEqual(bake_rank_curve_from_params(params), wiki)
        self.assertEqual(params.get("base"), 7.5)
        self.assertEqual(params.get("growth"), 1.5)

    def test_wrong_rank_multiple_curve_not_auto_fitted(self) -> None:
        from bwiki_scout.weapon_wiki import fit_bonus_params_from_rank_curve  # noqa: E402

        wrong = [float(21 * (i + 1)) for i in range(9)]
        params = fit_bonus_params_from_rank_curve(wrong)
        # 虽可拟合 base=21 growth=21，但语义为误录；须保留九档并依赖契约/人工纠正
        self.assertEqual(params.get("curve"), wrong)
        self.assertNotIn("base", params)


if __name__ == "__main__":
    unittest.main()
