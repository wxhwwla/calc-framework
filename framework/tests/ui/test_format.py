# SPDX-License-Identifier: AGPL-3.0
"""节点值格式化 — 单元测试。"""


from calc_framework.ui.controls import format_node_value


class TestFormatNodeValue:
    def test_float_default(self):
        assert format_node_value(3.14159) == "3.14159"

    def test_float_with_format_spec(self):
        assert format_node_value(3.14159, ".2f") == "3.14"

    def test_float_with_zero_decimal_format(self):
        assert format_node_value(1254.9936, ".0f") == "1255"

    def test_int_with_format_spec(self):
        assert format_node_value(42, ".2f") == "42.00"

    def test_percent_format(self):
        assert format_node_value(0.156, ".1%") == "15.6%"

    def test_invalid_format_falls_back_to_str(self):
        result = format_node_value(3.14, "invalid")
        assert "3.14" in result

    def test_none_value(self):
        assert format_node_value(None) == "N/A"

    def test_none_value_with_format(self):
        assert format_node_value(None, ".2f") == "N/A"
