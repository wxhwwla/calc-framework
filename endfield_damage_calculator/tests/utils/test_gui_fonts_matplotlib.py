#!/usr/bin/env python3
"""matplotlib 中文字体配置。"""

from __future__ import annotations

import unittest
import warnings

from utils.gui_chart_theme import reset_matplotlib_gui_style_for_tests
from utils.gui_fonts import (
    configure_matplotlib_font,
    matplotlib_sans_serif_families,
)
from utils.optional_deps import is_matplotlib_available


class TestGuiFontsMatplotlib(unittest.TestCase):
    def test_sans_serif_includes_cjk_fallbacks(self) -> None:
        families = matplotlib_sans_serif_families()
        self.assertIn("Microsoft YaHei", families)
        self.assertIn("DejaVu Sans", families)

    def test_configure_matplotlib_font_idempotent(self) -> None:
        reset_matplotlib_gui_style_for_tests()
        configure_matplotlib_font()
        import matplotlib.pyplot as plt

        first = list(plt.rcParams["font.sans-serif"])
        configure_matplotlib_font()
        second = list(plt.rcParams["font.sans-serif"])
        self.assertEqual(first, second)
        self.assertFalse(plt.rcParams["axes.unicode_minus"])

    @unittest.skipUnless(is_matplotlib_available(), "需要 matplotlib")
    def test_chinese_pie_title_without_glyph_warnings(self) -> None:
        import matplotlib

        matplotlib.use("Agg")
        from gui_design.shared.damage_visualization import (
            DamageSlice,
            build_damage_pie_figure,
        )

        reset_matplotlib_gui_style_for_tests()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            fig = build_damage_pie_figure(
                (DamageSlice(label="战技", value=80.0), DamageSlice(label="连携技", value=20.0)),
                title="轮转伤害构成",
            )
            import matplotlib.pyplot as plt

            plt.close(fig)
        glyph_warnings = [w for w in caught if "Glyph" in str(w.message)]
        self.assertEqual(glyph_warnings, [], msg=str(glyph_warnings))


if __name__ == "__main__":
    unittest.main()
