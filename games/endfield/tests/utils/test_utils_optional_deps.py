# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
from __future__ import annotations

from unittest.mock import patch

from utils.optional_deps import (
    GUI_OPTIONAL_DEPS,
    OptionalDependency,
    ensure_runtime_dependencies,
    format_missing_gui_extras,
    format_missing_lines,
    format_missing_runtime_dependencies,
    is_matplotlib_available,
    matplotlib_install_hint,
    missing_dependencies,
    missing_runtime_packages,
)


class TestIsMatplotlibAvailable:
    def test_returns_bool(self) -> None:
        assert isinstance(is_matplotlib_available(), bool)


class TestMatplotlibInstallHint:
    def test_contains_matplotlib(self) -> None:
        assert "matplotlib" in matplotlib_install_hint()


class TestMissingRuntimePackages:
    def test_returns_list_of_tuples(self) -> None:
        missing = missing_runtime_packages()

        assert isinstance(missing, list)

        for item in missing:
            assert len(item) == 2


class TestFormatMissingRuntimeDependencies:
    def test_returns_string(self) -> None:
        text = format_missing_runtime_dependencies()

        assert isinstance(text, str)

    def test_no_unknown(self) -> None:
        text = format_missing_runtime_dependencies()

        assert "未知" not in text

    def test_includes_pip_hint_when_missing(self) -> None:
        with patch("utils.optional_deps.is_matplotlib_available", return_value=False):
            text = format_missing_runtime_dependencies()

            assert "matplotlib" in text

            assert "pip install" in text

    def test_empty_when_all_installed(self) -> None:
        with patch("utils.optional_deps.is_matplotlib_available", return_value=True):
            text = format_missing_runtime_dependencies()

            assert text == ""


class TestMissingDependencies:
    def test_subset_of_input(self) -> None:
        missing = missing_dependencies(GUI_OPTIONAL_DEPS)

        assert len(missing) <= len(GUI_OPTIONAL_DEPS)

    def test_available_dep_not_in_missing(self) -> None:
        dep = OptionalDependency(feature="test", module="os", pip_hint="")

        missing = missing_dependencies([dep])

        assert dep not in missing

    def test_unavailable_dep_in_missing(self) -> None:
        dep = OptionalDependency(
            feature="nonexistent",
            module="_nonexistent_module_xyz_",
            pip_hint="pip install nothing",
        )

        missing = missing_dependencies([dep])

        assert dep in missing

    def test_with_custom_probe_true(self) -> None:
        dep = OptionalDependency(feature="custom", module="", pip_hint="", probe=lambda: True)

        missing = missing_dependencies([dep])

        assert dep not in missing

    def test_with_custom_probe_false(self) -> None:
        dep = OptionalDependency(feature="custom", module="", pip_hint="", probe=lambda: False)

        missing = missing_dependencies([dep])

        assert dep in missing


class TestFormatMissingLines:
    def test_empty_when_none_missing(self) -> None:
        dep = OptionalDependency(feature="ok", module="os", pip_hint="pip")

        text = format_missing_lines([dep])

        assert text == ""

    def test_contains_pip_hint_when_missing(self) -> None:
        dep = OptionalDependency(feature="missing", module="_xyz_", pip_hint="pip install xyz")

        text = format_missing_lines([dep])

        assert "pip install" in text

        assert "missing" in text

    def test_custom_prefix(self) -> None:
        dep = OptionalDependency(feature="f", module="_xyz_", pip_hint="pip")

        text = format_missing_lines([dep], prefix=">> ")

        assert text.startswith(">> ")


class TestFormatMissingGuiExtras:
    def test_returns_string(self) -> None:
        text = format_missing_gui_extras()

        assert isinstance(text, str)


class TestEnsureRuntimeDependencies:
    def test_frozen_skips(self) -> None:
        with patch("utils.optional_deps.sys") as mock_sys:
            mock_sys.frozen = True

            ensure_runtime_dependencies()

    def test_non_frozen_prints_warning(self) -> None:
        with (
            patch("utils.optional_deps.is_matplotlib_available", return_value=False),
            patch("utils.optional_deps.sys") as mock_sys,
        ):
            mock_sys.frozen = False

            ensure_runtime_dependencies()


class TestOptionalDependencyDataclass:
    def test_available_with_module(self) -> None:
        dep = OptionalDependency(feature="test", module="os", pip_hint="")

        assert dep.available() is True

    def test_unavailable_with_bad_module(self) -> None:
        dep = OptionalDependency(feature="test", module="_not_a_real_module_", pip_hint="")

        assert dep.available() is False

    def test_available_with_probe(self) -> None:
        dep = OptionalDependency(feature="test", module="", pip_hint="", probe=lambda: False)

        assert dep.available() is False
