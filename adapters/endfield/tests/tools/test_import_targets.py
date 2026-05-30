#!/usr/bin/env python3
"""BWIKI manifest → 同步目标解析测试。"""

import json
import tempfile
import unittest
from pathlib import Path

from bwiki_scout.detail_levels import operator_detail_title  # noqa: E402
from bwiki_scout.import_targets import (  # noqa: E402
    filter_operator_titles,
    load_manifest_titles,
    operator_wiki_cache_ready,
    resolve_operator_sync_names,
    resolve_weapon_sync_names,
    weapon_wiki_import_ready,
)
from bwiki_scout.storage import save_page_bundle  # noqa: E402

from adapters.endfield.tests.conftest import REPO_ROOT

_RAW_QIULI = REPO_ROOT / "tools/bwiki_scout/output/raw/秋栗"
_RAW_QIULI_DETAIL = REPO_ROOT / "tools/bwiki_scout/output/raw/秋栗_详细数据"
_RAW_ZHULIN = REPO_ROOT / "tools/bwiki_scout/output/raw/逐鳞3.0"


class TestImportTargets(unittest.TestCase):
    def test_filter_operator_titles_skips_gallery_meta_pages(self):
        titles = ["秋栗", "物品图鉴", "后勤技能一览"]
        self.assertEqual(filter_operator_titles(titles), ["秋栗"])

    def test_resolve_operator_names_default_only_local(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp) / "raw"
            raw.mkdir()
            names = resolve_operator_sync_names(
                local_names={"秋栗", "佩丽卡"},
                manifest_titles=["秋栗", "新干员", "物品图鉴"],
                raw_dir=raw,
                only=None,
                include_new=False,
            )
        self.assertEqual(names, ["佩丽卡", "秋栗"])

    def test_resolve_operator_names_include_new_when_cache_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "raw"
            raw.mkdir()
            main = {"title": "新干员", "wikitext": "{{干员|职业=近卫}}", "html": ""}
            detail = {
                "title": operator_detail_title("新干员"),
                "wikitext": "|力量1=1\n|攻击1=10\n",
                "html": "",
            }
            save_page_bundle(raw, "新干员", main)
            save_page_bundle(raw, operator_detail_title("新干员"), detail)
            (root / "manifest.json").write_text(
                json.dumps({"kinds": {"operator": {"titles": ["秋栗", "新干员"]}}}),
                encoding="utf-8",
            )
            names = resolve_operator_sync_names(
                local_names={"秋栗"},
                manifest_titles=load_manifest_titles(root, "operator"),
                raw_dir=raw,
                only=None,
                include_new=True,
            )
        self.assertEqual(names, ["新干员", "秋栗"])

    @unittest.skipUnless(
        _RAW_ZHULIN.is_dir(),
        "需要 BWIKI 缓存 raw/逐鳞3.0",
    )
    def test_weapon_import_ready_for_cached_zhulin(self):
        raw = _RAW_ZHULIN.parent
        self.assertTrue(weapon_wiki_import_ready(raw, "逐鳞3.0"))

    @unittest.skipUnless(
        _RAW_ZHULIN.is_dir(),
        "需要 BWIKI 缓存 raw/逐鳞3.0",
    )
    def test_resolve_weapon_include_new_adds_wiki_only_weapon(self):
        raw = _RAW_ZHULIN.parent
        names = resolve_weapon_sync_names(
            local_names=set(),
            manifest_titles=["逐鳞3.0", "无成长简表"],
            raw_dir=raw,
            only=None,
            include_new=True,
        )
        self.assertIn("逐鳞3.0", names)

    @unittest.skipUnless(
        _RAW_QIULI.is_dir() and _RAW_QIULI_DETAIL.is_dir(),
        "需要 BWIKI 秋栗缓存",
    )
    def test_operator_cache_ready_for_qiuli(self):
        raw = _RAW_QIULI.parent
        self.assertTrue(operator_wiki_cache_ready(raw, "秋栗"))

    def test_wiki_imported_weapon_matches_project_json_shape(self):
        """BWIKI --new 写入后，条目须含 90 级基础攻击与潜能曲线字段。"""
        path = REPO_ROOT / "games" / "endfield" / "character_weapon_equipment" / "weapon_data" / "weapons.json"
        rows = json.loads(path.read_text(encoding="utf-8"))
        jet = next(r for r in rows if r.get("名称") == "J.E.T.")
        self.assertEqual(jet["类型"], "长柄武器")
        self.assertEqual(len(jet["基础攻击力"]), 90)
        self.assertEqual(len(jet["等级"]), 90)
        normal = jet.get("normal_skills") or []
        special = jet.get("special_skills") or []
        self.assertTrue(any(item.get("effect") == "法术伤害+" for item in normal))
        self.assertGreaterEqual(len(special), 2)
        self.assertEqual(special[0].get("name"), "施放战技后，法术伤害+")
        self.assertEqual(special[1].get("name"), "施放连携技后，法术伤害+")


if __name__ == "__main__":
    unittest.main()
