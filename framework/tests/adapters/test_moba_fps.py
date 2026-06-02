# SPDX-License-Identifier: AGPL-3.0
"""MOBA / FPS 适配器集成测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from calc_framework.dag.service import DAGService

ADAPTERS_DIR = Path(__file__).resolve().parents[2] / "adapters"


def _load_moba_svc() -> DAGService:
    path = ADAPTERS_DIR / "moba" / "moba.dag.json"
    svc = DAGService.from_file(str(path))
    svc.register_function("armor_mult", _moba_armor_mult)
    return svc


def _load_fps_svc() -> DAGService:
    path = ADAPTERS_DIR / "fps" / "fps.dag.json"
    svc = DAGService.from_file(str(path))
    svc.register_function("le", _le)
    svc.register_function("ge", _ge)
    return svc


def _moba_armor_mult(armor: float, _pct: float, _flat: float) -> float:
    effective = max(0, armor)
    return 100.0 / (100.0 + effective)


def _le(a: float, b: float) -> float:
    return 1.0 if a <= b else 0.0


def _ge(a: float, b: float) -> float:
    return 1.0 if a >= b else 0.0


@pytest.fixture
def moba_svc():
    return _load_moba_svc()


@pytest.fixture
def fps_svc():
    return _load_fps_svc()


class TestMobaAdapter:
    """MOBA 伤害公式测试。"""

    def test_schema_loads(self):
        import json

        from calc_framework.data.attr_schema import AttributeSchema

        schema_path = ADAPTERS_DIR / "moba" / "attr_schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema = AttributeSchema.from_dict(data)
        assert len(schema.attributes) == 21
        names = [a.name for a in schema.attributes]
        assert "character.attack_damage" in names
        assert "user_input.ad_ratio" in names
        assert "enemy.armor" in names

    def test_ad_only_skill(self, moba_svc):
        """物理 AD 技能。"""
        ctx = {
            "character": {"attack_damage": 100, "ability_power": 0, "cooldown_reduction": 0},
            "user_input": {"skill_base_damage": 200, "ad_ratio": 0.8, "ap_ratio": 0, "is_physical": True, "is_crit": False, "skill_cooldown": 10},
            "enemy": {"armor": 50, "magic_resist": 30},
        }
        r = moba_svc.evaluate(ctx)
        assert r.outputs["技能总伤害"] == pytest.approx(186.67, rel=0.01)
        assert r.outputs["基础伤害"] == pytest.approx(280.0, rel=0.01)
        assert r.outputs["物理减伤比"] == pytest.approx(100 / 150, rel=0.01)

    def test_ap_only_skill(self, moba_svc):
        """魔法 AP 技能。"""
        ctx = {
            "character": {"attack_damage": 60, "ability_power": 200, "cooldown_reduction": 0},
            "user_input": {"skill_base_damage": 150, "ad_ratio": 0, "ap_ratio": 0.6, "is_physical": False, "is_crit": False, "skill_cooldown": 10},
            "enemy": {"armor": 50, "magic_resist": 40},
        }
        r = moba_svc.evaluate(ctx)
        expected = (150 + 0.6 * 200) * 100 / 140
        assert r.outputs["技能总伤害"] == pytest.approx(expected, rel=0.01)
        assert r.outputs["魔法减伤比"] == pytest.approx(100 / 140, rel=0.01)

    def test_crit_physical(self, moba_svc):
        ctx = {
            "character": {"attack_damage": 80, "crit_dmg": 2.0, "cooldown_reduction": 0},
            "user_input": {"skill_base_damage": 100, "ad_ratio": 1.0, "ap_ratio": 0, "is_physical": True, "is_crit": True, "skill_cooldown": 10},
            "enemy": {"armor": 30, "magic_resist": 30},
        }
        r = moba_svc.evaluate(ctx)
        assert r.outputs["技能总伤害"] == pytest.approx(540 * 100 / 130, rel=0.01)
        assert r.outputs["暴击后伤害"] == 540

    def test_no_crit(self, moba_svc):
        ctx = {
            "character": {"attack_damage": 80, "cooldown_reduction": 0},
            "user_input": {"skill_base_damage": 100, "ad_ratio": 0, "ap_ratio": 0, "is_physical": True, "is_crit": False, "skill_cooldown": 10},
            "enemy": {"armor": 0, "magic_resist": 0},
        }
        r = moba_svc.evaluate(ctx)
        assert r.outputs["暴击后伤害"] == 100

    def test_armor_penetration(self, moba_svc):
        ctx = {
            "character": {"lethality": 30, "armor_pen_pct": 0.3, "cooldown_reduction": 0},
            "user_input": {"skill_base_damage": 100, "ad_ratio": 0, "ap_ratio": 0, "is_physical": True, "is_crit": False, "skill_cooldown": 10},
            "enemy": {"armor": 100, "magic_resist": 30},
        }
        effective = max(0, (100 - 30) * (1 - 0.3))
        expected = 100.0 / (100.0 + effective)
        r = moba_svc.evaluate(ctx)
        assert r.outputs["物理减伤比"] == pytest.approx(expected, rel=0.01)
        assert r.outputs["技能总伤害"] == pytest.approx(100 * expected, rel=0.01)

    def test_cooldown_reduction(self, moba_svc):
        ctx = {
            "character": {"cooldown_reduction": 0.4},
            "user_input": {"skill_cooldown": 10, "is_physical": True, "is_crit": False},
            "enemy": {"armor": 0, "magic_resist": 0},
        }
        r = moba_svc.evaluate(ctx)
        assert r.outputs["实际冷却(秒)"] == pytest.approx(6.0, rel=0.01)

    def test_full_moba_pipeline(self):
        from calc_framework.config.manager import AdapterManager
        mgr = AdapterManager()
        pkg = mgr.load("MOBA 英雄伤害计算")
        ctx = {
            "character": {"attack_damage": 120, "ability_power": 0, "cooldown_reduction": 0},
            "user_input": {"skill_base_damage": 250, "ad_ratio": 1.2, "ap_ratio": 0, "is_physical": True, "is_crit": False, "skill_cooldown": 10},
            "enemy": {"armor": 80, "magic_resist": 30},
        }
        r = pkg.dag_service.evaluate(ctx)
        assert "技能总伤害" in r.outputs
        assert r.outputs["技能总伤害"] > 0


class TestFpsAdapter:
    """FPS 武器伤害公式测试。"""

    def test_schema_loads(self):
        import json

        from calc_framework.data.attr_schema import AttributeSchema

        schema_path = ADAPTERS_DIR / "fps" / "attr_schema.json"
        data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema = AttributeSchema.from_dict(data)
        assert len(schema.attributes) == 15

    def _ctx(self, **overrides):
        base = {
            "weapon": {"base_damage": 30, "decay_start": 15, "decay_end": 50, "min_damage_ratio": 0.5, "fire_rate": 600, "mag_size": 30, "reload_time": 2.5},
            "enemy": {"distance": 5, "armor": 0, "head_mult": 2.0, "body_mult": 1.0},
            "user_input": {"is_head": False, "is_limb": False, "wall_pen_count": 0},
        }
        for k, v in overrides.items():
            sec, field = k.split(".", 1)
            if sec in base:
                base[sec][field] = v
            else:
                base[sec] = {field: v}
        return base

    def test_close_range_no_decay(self, fps_svc):
        ctx = self._ctx(**{"enemy.distance": 5})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["距离衰减系数"] == pytest.approx(1.0, rel=0.01)
        assert r.outputs["单发伤害"] == 30

    def test_far_range_min_damage(self, fps_svc):
        ctx = self._ctx(**{"enemy.distance": 100, "weapon.min_damage_ratio": 0.5})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["距离衰减系数"] == pytest.approx(0.5, rel=0.01)
        assert r.outputs["单发伤害"] == pytest.approx(15.0, rel=0.01)

    def test_mid_range_linear_decay(self, fps_svc):
        ctx = self._ctx(**{"weapon.decay_start": 10, "weapon.decay_end": 30, "weapon.min_damage_ratio": 0.4, "enemy.distance": 20})
        r = fps_svc.evaluate(ctx)
        expected = 1 - (1 - 0.4) * 0.5
        assert r.outputs["距离衰减系数"] == pytest.approx(expected, rel=0.01)

    def test_headshot_mult(self, fps_svc):
        ctx = self._ctx(**{"enemy.head_mult": 2.5, "user_input.is_head": True})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["部位倍率"] == 2.5
        assert r.outputs["单发伤害"] == 75.0

    def test_body_shot(self, fps_svc):
        ctx = self._ctx(**{"user_input.is_head": False, "user_input.is_limb": False})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["部位倍率"] == 1.0
        assert r.outputs["单发伤害"] == 30

    def test_limb_shot(self, fps_svc):
        ctx = self._ctx(**{"user_input.is_limb": True})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["部位倍率"] == 0.75
        assert r.outputs["单发伤害"] == 22.5

    def test_armor_reduction(self, fps_svc):
        ctx = self._ctx(**{"enemy.armor": 100})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["护甲减伤比"] == pytest.approx(100 / 200, rel=0.01)

    def test_wall_penetration(self, fps_svc):
        ctx = self._ctx(**{"user_input.wall_pen_count": 1})
        r = fps_svc.evaluate(ctx)
        assert r.outputs["单发伤害"] == 15.0

    def test_sustained_dps(self, fps_svc):
        ctx = self._ctx()
        r = fps_svc.evaluate(ctx)
        assert r.outputs["原始 DPS"] == pytest.approx(300.0, rel=0.01)
        expected_sust = 300 * (30 / 10) / (30 / 10 + 2.5)
        assert r.outputs["持续 DPS(含换弹)"] == pytest.approx(expected_sust, rel=0.01)

    def test_full_fps_pipeline(self):
        from calc_framework.config.manager import AdapterManager
        mgr = AdapterManager()
        pkg = mgr.load("FPS 武器伤害计算")
        ctx = self._ctx(**{"weapon.base_damage": 25, "enemy.armor": 50, "user_input.is_head": True})
        r = pkg.dag_service.evaluate(ctx)
        assert "单发伤害" in r.outputs
        assert r.outputs["单发伤害"] > 0
        assert r.outputs["距离衰减系数"] == 1.0
