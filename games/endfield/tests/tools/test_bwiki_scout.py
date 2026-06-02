#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""BWIKI 侦察模块测试（纯函数与离线 fixture，不访问网络）。"""

import tempfileimport unittestfrom pathlib import Pathfrom bwiki_scout.detail_levels import (  # noqa: E402    compare_operator_to_local,    operator_detail_title,    parse_operator_detail_wikitext,)from bwiki_scout.gallery import extract_gallery_entry_titles, merge_title_lists  # noqa: E402from bwiki_scout.json_scan import find_json_hints  # noqa: E402from bwiki_scout.local_schema import compare_name_sets, summarize_local_schema  # noqa: E402from bwiki_scout.names import normalize_name_for_match  # noqa: E402from bwiki_scout.parse_draft import build_draft_record, extract_template_params  # noqa: E402from bwiki_scout.scout import run_scout  # noqa: E402from games.endfield.tests.conftest import DATA_DIR_CHARS = DATA_DIR / "characters.json"
_WEAPONS = DATA_DIR / "weapons.json"


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
        from bwiki_scout.weapon_wiki import (  # noqa: E402            bake_rank_curve_from_params,            fit_bonus_params_from_rank_curve,        )

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


class TestIncrementalSync(unittest.TestCase):
    """增量同步状态管理测试。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state_path = self.tmp / "sync_state.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_bundle(self, wikitext: str = "", html: str = "") -> dict:
        return {"wikitext": wikitext, "html": html}

    # ── 哈希运算 ──

    def test_content_hash_deterministic(self):
        from bwiki_scout.incremental_sync import _content_hash
        h1 = _content_hash("hello")
        h2 = _content_hash("hello")
        self.assertEqual(h1, h2)

    def test_content_hash_different_input(self):
        from bwiki_scout.incremental_sync import _content_hash
        self.assertNotEqual(_content_hash("aaa"), _content_hash("bbb"))

    def test_bundle_hash_combines_wikitext_and_html(self):
        from bwiki_scout.incremental_sync import _bundle_hash
        h1 = _bundle_hash(self._make_bundle("a", "b"))
        h2 = _bundle_hash(self._make_bundle("a", "c"))
        h3 = _bundle_hash(self._make_bundle("b", "b"))
        self.assertEqual(h1, _bundle_hash(self._make_bundle("a", "b")))
        self.assertNotEqual(h1, h2)
        self.assertNotEqual(h1, h3)

    def test_bundle_hash_no_wikitext(self):
        from bwiki_scout.incremental_sync import _bundle_hash
        h = _bundle_hash({})
        self.assertIsInstance(h, str)
        self.assertEqual(len(h), 64)

    # ── 状态加载/保存 ──

    def test_load_sync_state_no_file(self):
        from bwiki_scout.incremental_sync import load_sync_state
        state = load_sync_state(self.tmp)
        self.assertEqual(state, {"version": 1, "entities": {}})

    def test_save_and_load_round_trip(self):
        from bwiki_scout.incremental_sync import load_sync_state, save_sync_state
        state = {"version": 1, "entities": {"测试A": "abc123"}}
        save_sync_state(self.tmp, state)
        loaded = load_sync_state(self.tmp)
        self.assertEqual(loaded, state)
        self.assertTrue(self.state_path.is_file())

    # ── 记录与检测 ──

    def test_record_entity_sync(self):
        from bwiki_scout.incremental_sync import load_sync_state, record_entity_sync
        state = load_sync_state(self.tmp)
        bundle = self._make_bundle("测试内容", "<p>测试</p>")
        record_entity_sync(state, "角色A", bundle)
        self.assertIn("角色A", state["entities"])
        self.assertEqual(len(state["entities"]["角色A"]), 64)

    def test_content_changed_new_entity_returns_true(self):
        from bwiki_scout.incremental_sync import content_changed
        state = {"version": 1, "entities": {}}
        bundle = self._make_bundle("内容", "<p>内容</p>")
        self.assertTrue(content_changed(state, "新角色", bundle))

    def test_content_changed_same_content_returns_false(self):
        from bwiki_scout.incremental_sync import (
            content_changed,
            record_entity_sync,
        )
        state = {"version": 1, "entities": {}}
        bundle = self._make_bundle("相同内容", "<p>相同</p>")
        record_entity_sync(state, "角色A", bundle)
        self.assertFalse(content_changed(state, "角色A", bundle))

    def test_content_changed_different_content_returns_true(self):
        from bwiki_scout.incremental_sync import (
            content_changed,
            record_entity_sync,
        )
        state = {"version": 1, "entities": {}}
        bundle1 = self._make_bundle("旧内容", "<p>旧</p>")
        record_entity_sync(state, "角色A", bundle1)
        bundle2 = self._make_bundle("新内容", "<p>新</p>")
        self.assertTrue(content_changed(state, "角色A", bundle2))

    # ── 清理 ──

    def test_remove_entity(self):
        from bwiki_scout.incremental_sync import remove_entity
        state = {"version": 1, "entities": {"角色A": "abc", "角色B": "def"}}
        remove_entity(state, "角色A")
        self.assertNotIn("角色A", state["entities"])
        self.assertIn("角色B", state["entities"])

    def test_remove_entity_nonexistent(self):
        from bwiki_scout.incremental_sync import remove_entity
        state = {"version": 1, "entities": {"角色A": "abc"}}
        remove_entity(state, "不存在")  # should not raise
        self.assertIn("角色A", state["entities"])

    def test_cleanup_stale_entities(self):
        from bwiki_scout.incremental_sync import cleanup_stale_entities
        state = {"version": 1, "entities": {"角色A": "abc", "角色B": "def", "角色C": "ghi"}}
        known = {"角色A", "角色C"}
        count = cleanup_stale_entities(state, known)
        self.assertEqual(count, 1)
        self.assertIn("角色A", state["entities"])
        self.assertNotIn("角色B", state["entities"])
        self.assertIn("角色C", state["entities"])

    def test_cleanup_stale_no_action(self):
        from bwiki_scout.incremental_sync import cleanup_stale_entities
        state = {"version": 1, "entities": {"角色A": "abc"}}
        count = cleanup_stale_entities(state, {"角色A", "角色B"})
        self.assertEqual(count, 0)
        self.assertIn("角色A", state["entities"])

    # ── get_entity_hash ──

    def test_get_entity_hash_known(self):
        from bwiki_scout.incremental_sync import get_entity_hash
        state = {"version": 1, "entities": {"角色A": "abc123"}}
        self.assertEqual(get_entity_hash(state, "角色A"), "abc123")

    def test_get_entity_hash_unknown(self):
        from bwiki_scout.incremental_sync import get_entity_hash
        state = {"version": 1, "entities": {}}
        self.assertIsNone(get_entity_hash(state, "角色A"))


class TestDataVersionBump(unittest.TestCase):
    """自动 version bump 测试。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.version_path = self.tmp / "data_version.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ── semver 解析/格式化 ──

    def test_parse_semver_standard(self):
        from bwiki_scout.bump_data_version import parse_semver
        self.assertEqual(parse_semver("1.2.3"), (1, 2, 3))

    def test_parse_semver_partial(self):
        from bwiki_scout.bump_data_version import parse_semver
        self.assertEqual(parse_semver("2"), (2, 0, 0))
        self.assertEqual(parse_semver("2.1"), (2, 1, 0))

    def test_format_semver(self):
        from bwiki_scout.bump_data_version import format_semver
        self.assertEqual(format_semver(3, 5, 1), "3.5.1")
        self.assertEqual(format_semver(0, 0, 0), "0.0.0")

    # ── bump 函数 ──

    def test_bump_patch(self):
        from bwiki_scout.bump_data_version import bump_patch
        self.assertEqual(bump_patch("1.2.3"), "1.2.4")
        self.assertEqual(bump_patch("0.0.0"), "0.0.1")

    def test_bump_minor(self):
        from bwiki_scout.bump_data_version import bump_minor
        self.assertEqual(bump_minor("1.2.3"), "1.3.0")
        self.assertEqual(bump_minor("0.0.0"), "0.1.0")

    def test_bump_minor_resets_patch(self):
        from bwiki_scout.bump_data_version import bump_minor
        self.assertEqual(bump_minor("5.9.99"), "5.10.0")

    # ── 读/写版本文件 ──

    def test_read_data_version_no_file(self):
        from bwiki_scout.bump_data_version import read_data_version
        state = read_data_version(self.version_path)
        self.assertEqual(state, {"version": "1.0.0"})

    def test_write_and_read_data_version(self):
        from bwiki_scout.bump_data_version import (
            read_data_version,
            write_data_version,
        )
        state = {"version": "2.3.1"}
        write_data_version(state, self.version_path)
        self.assertTrue(self.version_path.is_file())
        loaded = read_data_version(self.version_path)
        self.assertEqual(loaded, state)

    # ── 变更检测 ──

    def test_has_data_changes_dry_run(self):
        from bwiki_scout.bump_data_version import has_data_changes
        results = [{"dry_run": True, "updated_count": 5}]
        self.assertFalse(has_data_changes(results))

    def test_has_data_changes_with_updated(self):
        from bwiki_scout.bump_data_version import has_data_changes
        results = [{"dry_run": False, "updated_count": 3, "added": [], "planned": ["A"]}]
        self.assertTrue(has_data_changes(results))

    def test_has_data_changes_with_added(self):
        from bwiki_scout.bump_data_version import has_data_changes
        results = [{"dry_run": False, "updated_count": 0, "added": ["新干员"], "planned": ["新干员"]}]
        self.assertTrue(has_data_changes(results))

    def test_has_data_changes_no_changes(self):
        from bwiki_scout.bump_data_version import has_data_changes
        results = [{"dry_run": False, "updated_count": 0, "added": [], "planned": []}]
        self.assertFalse(has_data_changes(results))

    def test_count_new_entities(self):
        from bwiki_scout.bump_data_version import count_new_entities
        results = [
            {"added": ["A", "B"]},
            {"added": ["C"]},
            {"added": []},
        ]
        self.assertEqual(count_new_entities(results), 3)

    def test_has_updated_values(self):
        from bwiki_scout.bump_data_version import has_updated_values
        results = [{"dry_run": False, "updated_count": 2}]
        self.assertTrue(has_updated_values(results))

    # ── bump 类型判断 ──

    def test_determine_bump_type_none(self):
        from bwiki_scout.bump_data_version import determine_bump_type
        self.assertIsNone(determine_bump_type([{"dry_run": False, "updated_count": 0, "added": []}]))

    def test_determine_bump_type_minor(self):
        from bwiki_scout.bump_data_version import determine_bump_type
        self.assertEqual(
            determine_bump_type([{"dry_run": False, "updated_count": 0, "added": ["新干员"], "planned": ["新干员"]}]),
            "minor",
        )

    def test_determine_bump_type_patch(self):
        from bwiki_scout.bump_data_version import determine_bump_type
        self.assertEqual(
            determine_bump_type([{"dry_run": False, "updated_count": 3, "added": [], "planned": ["A"]}]),
            "patch",
        )

    def test_determine_bump_type_dry_run_ignored(self):
        from bwiki_scout.bump_data_version import determine_bump_type
        self.assertIsNone(determine_bump_type([{"dry_run": True, "updated_count": 5, "added": []}]))

    # ── bump_data_version 集成 ──

    def test_bump_data_version_patch(self):
        from bwiki_scout.bump_data_version import bump_data_version
        results = [{"dry_run": False, "updated_count": 2, "added": [], "planned": ["A"]}]
        new_ver = bump_data_version(results, data_version_file=self.version_path)
        self.assertEqual(new_ver, "1.0.1")

    def test_bump_data_version_minor(self):
        from bwiki_scout.bump_data_version import bump_data_version
        results = [{"dry_run": False, "updated_count": 0, "added": ["新角色"], "planned": ["新角色"]}]
        new_ver = bump_data_version(results, data_version_file=self.version_path)
        self.assertEqual(new_ver, "1.1.0")

    def test_bump_data_version_no_change(self):
        from bwiki_scout.bump_data_version import bump_data_version
        results = [{"dry_run": False, "updated_count": 0, "added": [], "planned": []}]
        new_ver = bump_data_version(results, data_version_file=self.version_path)
        self.assertIsNone(new_ver)

    def test_bump_data_version_force(self):
        from bwiki_scout.bump_data_version import bump_data_version
        results = []
        new_ver = bump_data_version(results, data_version_file=self.version_path, force_version="2.0.0")
        self.assertEqual(new_ver, "2.0.0")

    def test_bump_data_version_multiple_patches(self):
        from bwiki_scout.bump_data_version import bump_data_version
        r = [{"dry_run": False, "updated_count": 1, "added": [], "planned": ["A"]}]
        v1 = bump_data_version(r, data_version_file=self.version_path)
        self.assertEqual(v1, "1.0.1")
        v2 = bump_data_version(r, data_version_file=self.version_path)
        self.assertEqual(v2, "1.0.2")
        v3 = bump_data_version(r, data_version_file=self.version_path)
        self.assertEqual(v3, "1.0.3")


if __name__ == "__main__":
    unittest.main()
