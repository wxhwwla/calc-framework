#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""伤害可视化（matplotlib）测试。"""



import unittest

from games.endfield.gui.shared.damage_visualization import (
    damage_breakdown_from_skill_map,
    is_matplotlib_available,
)


class TestDamageVisualization(unittest.TestCase):

    def test_breakdown_normalizes_percentages(self) -> None:

        parts = damage_breakdown_from_skill_map({"战技": 200.0, "连携技": 100.0})

        self.assertAlmostEqual(sum(p.value for p in parts), 300.0)

        self.assertEqual(len(parts), 2)



    @unittest.skipUnless(is_matplotlib_available(), "需要 matplotlib")

    def test_builds_pie_figure_without_display(self) -> None:

        from gui.shared.damage_visualization import build_damage_pie_figure



        fig = build_damage_pie_figure(

            damage_breakdown_from_skill_map({"战技": 80.0, "连携技": 20.0}),

            title="测试",

        )

        self.assertIsNotNone(fig.axes)

        import matplotlib.pyplot as plt



        plt.close(fig)





if __name__ == "__main__":

    unittest.main()

