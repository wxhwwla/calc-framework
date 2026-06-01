#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""捐赠图片路径解析测试（不依赖 Qt）。"""

from __future__ import annotations

import unittest
from pathlib import Path

from utils.gui.donation import (
    DONATION_IMAGE_PATH,
    _default_donation_rel_paths,
    _dialog_image_paths,
)
from utils.path_utils import get_resource_path


class TestDonationPaths(unittest.TestCase):
    def test_default_rel_paths(self) -> None:
        names = [Path(p).name for p in _default_donation_rel_paths()]
        self.assertEqual(names, ["donation_qr.png", "afdian_qr.png"])

    def test_dialog_paths_include_existing_defaults(self) -> None:
        paths = _dialog_image_paths()
        if get_resource_path(DONATION_IMAGE_PATH).exists():
            self.assertTrue(any(p.endswith("donation_qr.png") for p in paths))

    def test_custom_pack_asset_path(self) -> None:
        custom = "assets/my_qr.png"
        self.assertEqual(_dialog_image_paths(custom), [custom])


if __name__ == "__main__":
    unittest.main()
