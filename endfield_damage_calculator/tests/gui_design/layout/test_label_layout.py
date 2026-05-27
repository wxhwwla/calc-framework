#!/usr/bin/env python3
"""可换行标签宽度计算（无 GUI 窗口）。"""

import unittest

from gui_design.layout.label_wrap import compute_wraplength


class TestComputeWraplength(unittest.TestCase):
    def test_uses_viewport_when_inner_scroll_area_is_wider(self):
        """Scrollable 内层很宽时，应按可见列宽换行，避免横向截断。"""
        wrap = compute_wraplength(1200, viewport_width=360, padding=24, min_wrap=160)
        self.assertEqual(wrap, 336)

    def test_uses_container_when_narrower_than_viewport(self):
        wrap = compute_wraplength(280, viewport_width=360, padding=24, min_wrap=160)
        self.assertEqual(wrap, 256)

    def test_falls_back_to_viewport_when_container_not_laid_out(self):
        wrap = compute_wraplength(0, viewport_width=360, padding=24, min_wrap=160)
        self.assertEqual(wrap, 336)

    def test_respects_min_wrap(self):
        wrap = compute_wraplength(100, viewport_width=120, padding=24, min_wrap=160)
        self.assertEqual(wrap, 160)


if __name__ == "__main__":
    unittest.main()
