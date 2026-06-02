# SPDX-License-Identifier: AGPL-3.0
"""DataContextLoader 抽象基类 — 单元测试。"""

from abc import ABC

import pytest

from calc_framework.data.context import make_context
from calc_framework.data.loader import DataContextLoader


class _MockLoader(DataContextLoader):
    def build_context(self, **kwargs):
        return make_context(
            character={"name": kwargs.get("name", "")},
        )


class TestDataContextLoader:
    def test_is_abc(self):
        assert issubclass(DataContextLoader, ABC)

    def test_cannot_instantiate_without_implementation(self):
        with pytest.raises(TypeError):
            DataContextLoader()  # type: ignore[abstract]

    def test_concrete_implementation_works(self):
        loader = _MockLoader()
        ctx = loader.build_context(name="Tester")
        assert ctx["character"]["name"] == "Tester"

    def test_concrete_build_context_returns_dict(self):
        loader = _MockLoader()
        ctx = loader.build_context()
        assert isinstance(ctx, dict)
        assert "character" in ctx
