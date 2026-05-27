"""DataContext 类型定义与工厂函数 — 单元测试。"""

from calc_framework.data.context import DataContext, make_context


class TestMakeContext:
    def test_returns_dict(self):
        ctx = make_context()
        assert isinstance(ctx, dict)

    def test_has_all_standard_keys_with_empty_dicts(self):
        ctx = make_context()
        assert ctx == {
            "character": {},
            "weapon": {},
            "equipment": {},
            "enemy": {},
            "computed": {},
        }

    def test_accepts_arbitrary_extra_keys(self):
        ctx = make_context(character={"level": 80}, custom={"foo": "bar"})
        assert ctx["character"] == {"level": 80}
        assert ctx["custom"] == {"foo": "bar"}

    def test_extra_keys_do_not_clobber_standard_keys(self):
        ctx = make_context(enemy={"defense": 100}, enemy2={"defense": 200})
        assert ctx["enemy"] == {"defense": 100}
        assert ctx["enemy2"] == {"defense": 200}

    def test_can_be_passed_to_engine_evaluate(self):
        ctx = make_context(
            character={"基础攻击": 500},
            computed={"技能倍率": 1.0},
        )
        assert ctx["character"]["基础攻击"] == 500
        assert ctx["computed"]["技能倍率"] == 1.0

    def test_typeddict_annotation(self):
        ctx: DataContext = make_context()
        assert isinstance(ctx, dict)
        assert "character" in ctx
