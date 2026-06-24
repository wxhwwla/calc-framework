#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""双特殊能力：Wiki 解析与 JSON 字段。"""

import io
import sys
import unittest
from contextlib import redirect_stdout

from games.endfield.tests.conftest import PKG_ROOT, REPO_ROOT, TOOLS_ROOT

for p in (TOOLS_ROOT, PKG_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


from bwiki_scout.weapon_wiki import build_weapon_seed_spec_from_wiki  # noqa: E402

_RAW_JIANFENG = REPO_ROOT / "tools/bwiki_scout/output/raw/O.B.J.尖峰"

_RAW_JET = REPO_ROOT / "tools/bwiki_scout/output/raw/J.E.T"


class TestWeaponDualSpecial(unittest.TestCase):
    @unittest.skipUnless(_RAW_JIANFENG.is_dir(), "需要 BWIKI 缓存 O.B.J.尖峰")
    def test_jianfeng_has_two_conditional_specials_no_third_bonus(self):
        wikitext = (_RAW_JIANFENG / "wikitext.txt").read_text(encoding="utf-8")

        with redirect_stdout(io.StringIO()):
            spec = build_weapon_seed_spec_from_wiki(name="O.B.J.尖峰", wikitext=wikitext)

        self.assertEqual(len(spec["bonus_attrs"]), 2)

        self.assertEqual(spec["special_1"]["name"], "造成的伤害增加+")

        self.assertEqual(spec["special_2"]["name"], "攻击力+")

        self.assertFalse(spec["special_2"].get("enabled") is False)

    @unittest.skipUnless(_RAW_JET.is_dir(), "需要 BWIKI 缓存 J.E.T")
    def test_jet_third_bonus_plus_two_specials(self):
        wikitext = (_RAW_JET / "wikitext.txt").read_text(encoding="utf-8")

        with redirect_stdout(io.StringIO()):
            spec = build_weapon_seed_spec_from_wiki(name="J.E.T.", wikitext=wikitext)

        self.assertIn("法术伤害+", spec["bonus_attrs"])

        self.assertEqual(spec["special_1"]["name"], "施放战技后，法术伤害+")

        self.assertEqual(spec["special_2"]["name"], "施放连携技后，法术伤害+")


if __name__ == "__main__":
    unittest.main()
