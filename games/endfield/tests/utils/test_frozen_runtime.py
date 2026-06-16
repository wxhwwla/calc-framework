# SPDX-License-Identifier: AGPL-3.0
"""frozen_runtime 单元测试。"""

from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch

import utils.frozen_runtime as fr


class TestFrozenRuntime(unittest.TestCase):
    def test_frozen_disables_rust(self) -> None:
        with patch.object(sys, "frozen", True, create=True):
            with patch.dict(os.environ, {}, clear=True):
                self.assertFalse(fr.use_rust_search_accel())

    def test_dev_allows_rust_without_fallback(self) -> None:
        with patch.object(sys, "frozen", False, create=True):
            with patch.dict(os.environ, {}, clear=True):
                self.assertTrue(fr.use_rust_search_accel())

    def test_fallback_env_disables_rust(self) -> None:
        with patch.object(sys, "frozen", False, create=True):
            with patch.dict(os.environ, {"RUST_SEARCH_FALLBACK": "1"}, clear=True):
                self.assertFalse(fr.use_rust_search_accel())


if __name__ == "__main__":
    unittest.main()
