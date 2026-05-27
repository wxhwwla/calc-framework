"""控件推断 — 单元测试。

根据 DAG variables 声明推断对应的 UI 控件类型。
"""


from calc_framework.ui.controls import infer_control


class TestInferControl:
    def test_user_input_float_with_min_max_yields_slider(self):
        var = {"type": "float", "source": "user_input", "default": 50, "min": 0, "max": 100}
        spec = infer_control("暴击率", var)
        assert spec.widget == "slider"
        assert spec.default == 50
        assert spec.min_val == 0
        assert spec.max_val == 100

    def test_user_input_int_with_min_max_yields_slider(self):
        var = {"type": "int", "source": "user_input", "default": 5, "min": 1, "max": 10}
        spec = infer_control("等级", var)
        assert spec.widget == "slider"
        assert spec.step == 1

    def test_float_step_defaults(self):
        var = {"type": "float", "source": "user_input", "default": 0, "min": 0, "max": 1}
        spec = infer_control("x", var)
        assert spec.step == 0.01

    def test_user_input_float_without_min_max_yields_spinbox(self):
        var = {"type": "float", "source": "user_input", "default": 1.0}
        spec = infer_control("倍率", var)
        assert spec.widget == "spinbox"

    def test_user_input_bool_yields_switch(self):
        var = {"type": "bool", "source": "user_input", "default": False}
        spec = infer_control("启用", var)
        assert spec.widget == "switch"
        assert spec.default is False

    def test_user_input_str_yields_dropdown(self):
        var = {"type": "str", "source": "user_input", "default": "物理", "options": ["物理", "法术"]}
        spec = infer_control("伤害类型", var)
        assert spec.widget == "dropdown"
        assert spec.options == ["物理", "法术"]

    def test_character_source_no_control(self):
        var = {"type": "float", "source": "character", "default": 0}
        spec = infer_control("角色.基础攻击", var)
        assert spec.widget == "none"

    def test_weapon_source_no_control(self):
        var = {"type": "float", "source": "weapon", "default": 0}
        spec = infer_control("武器.基础攻击", var)
        assert spec.widget == "none"

    def test_equipment_source_no_control(self):
        var = {"type": "float", "source": "equipment", "default": 0}
        spec = infer_control("装备.攻击力平值", var)
        assert spec.widget == "none"

    def test_enemy_source_no_control(self):
        var = {"type": "float", "source": "enemy", "default": 100}
        spec = infer_control("enemy.防御", var)
        assert spec.widget == "none"

    def test_computed_source_no_control(self):
        var = {"type": "float", "source": "computed", "default": 0}
        spec = infer_control("computed.最终攻击力", var)
        assert spec.widget == "none"

    def test_ui_control_override(self):
        var = {
            "type": "float",
            "source": "user_input",
            "default": 0,
            "min": 0,
            "max": 100,
            "ui_control": {"widget": "spinbox", "step": 0.1},
        }
        spec = infer_control("暴击率", var)
        assert spec.widget == "spinbox"
        assert spec.step == 0.1

    def test_missing_default_uses_zero(self):
        var = {"type": "float", "source": "user_input"}
        spec = infer_control("x", var)
        assert spec.default == 0.0

    def test_label_uses_variable_path(self):
        var = {"type": "float", "source": "user_input", "default": 0}
        spec = infer_control("暴击率加成", var)
        assert spec.label == "暴击率加成"

    def test_description_passed_through(self):
        var = {"type": "float", "source": "user_input", "default": 0, "description": "百分比"}
        spec = infer_control("暴击率", var)
        assert spec.description == "百分比"
