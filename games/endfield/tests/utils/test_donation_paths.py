#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""捐赠图片路径解析测试（不依赖 Qt）。"""

from __future__ import annotations

import unittest
from pathlib import Path

from utils.donation_assets import (
    is_allowed_donation_filename,
    resolve_donation_images,
    resolve_donation_rel_paths,
)
from utils.gui.donation import _dialog_image_paths
from utils.path_utils import get_resource_path


class TestDonationPaths(unittest.TestCase):
    def test_resolve_matches_existing_files(self) -> None:
        images = resolve_donation_images()
        for item in images:
            self.assertTrue(get_resource_path(item["rel"]).exists())
            self.assertIn(item["label"], ("微信赞赏码", "爱发电"))

    def test_dialog_paths_use_resolved_slots(self) -> None:
        paths = _dialog_image_paths()
        resolved = resolve_donation_rel_paths()
        if resolved:
            self.assertEqual(paths, resolved)

    def test_custom_pack_asset_path(self) -> None:
        custom = "assets/my_qr.png"
        self.assertEqual(_dialog_image_paths(custom), [custom])

    def test_allowed_donation_filenames(self) -> None:
        self.assertTrue(is_allowed_donation_filename("donation_q.jpg"))
        self.assertTrue(is_allowed_donation_filename("afdian_qr.png"))
        self.assertFalse(is_allowed_donation_filename("../secret.png"))
        self.assertFalse(is_allowed_donation_filename("other.png"))

    def test_wechat_jpg_if_present(self) -> None:
        names = [Path(p).name for p in resolve_donation_rel_paths()]
        wechat = get_resource_path("resources/donation/donation_q.jpg")
        if wechat.exists():
            self.assertIn("donation_q.jpg", names)


if __name__ == "__main__":
    unittest.main()
