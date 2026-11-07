# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""许可覆盖门禁：清单解析、NOTICES 匹配与仓库自检的回归测试。"""

from __future__ import annotations

import json
from pathlib import Path

from tools.quality.supply_chain import check_licenses


def test_normalize_name_uses_pep503_form() -> None:
    """依赖名应折叠大小写、下划线与点。"""
    assert check_licenses.normalize_name("PySide6") == "pyside6"
    assert check_licenses.normalize_name("Flask_SQLAlchemy") == "flask-sqlalchemy"
    assert check_licenses.normalize_name("@MUI/material") == "@mui/material"


def test_parse_requirements_follows_includes_and_strips_extras(tmp_path: Path) -> None:
    """requirements 解析应处理 -r、extras、环境标记与可编辑安装。"""
    nested = tmp_path / "nested.txt"
    nested.write_text("httpx>=0.28\n", encoding="utf-8")
    requirement = tmp_path / "requirements.txt"
    requirement.write_text(
        "# 注释\n-r nested.txt\nfastapi>=0.115\nuvicorn[standard]>=0.34 ; python_version < '3.12'\n-e .\n",
        encoding="utf-8",
    )

    assert check_licenses.parse_requirements(requirement) == {
        "fastapi",
        "httpx",
        "uvicorn",
    }


def test_parse_pyproject_reads_runtime_optional_and_build_deps(tmp_path: Path) -> None:
    """pyproject 应覆盖 dependencies、optional-dependencies 与 build-system。"""
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text(
        """
[build-system]
requires = ["setuptools>=61", "wheel"]

[project]
name = "demo"
dependencies = ["requests>=2"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.8"]
""",
        encoding="utf-8",
    )

    dependencies, self_names = check_licenses.parse_pyproject(manifest)

    assert dependencies == {"requests", "pytest", "ruff", "setuptools", "wheel"}
    assert self_names == {"demo"}


def test_parse_package_json_reads_all_dependency_groups(tmp_path: Path) -> None:
    """package.json 应覆盖 dependencies、devDependencies 与 optionalDependencies。"""
    manifest = tmp_path / "package.json"
    manifest.write_text(
        json.dumps(
            {
                "name": "demo-web",
                "dependencies": {"react": "^18"},
                "devDependencies": {"vite": "^6"},
                "optionalDependencies": {"fsevents": "^2"},
            }
        ),
        encoding="utf-8",
    )

    dependencies, self_names = check_licenses.parse_package_json(manifest)

    assert dependencies == {"react", "vite", "fsevents"}
    assert self_names == {"demo-web"}


def test_parse_cargo_toml_reads_all_dependency_sections(tmp_path: Path) -> None:
    """Cargo.toml 应覆盖 dependencies、dev-dependencies 与 target 依赖。"""
    manifest = tmp_path / "Cargo.toml"
    manifest.write_text(
        """
[package]
name = "demo-rust"

[dependencies]
pyo3 = { version = "0.29" }
wasm-bindgen = "0.2"

[dev-dependencies]
approx = "0.5"

[target.'cfg(windows)'.dependencies]
windows = "0.5"
""",
        encoding="utf-8",
    )

    dependencies, self_names = check_licenses.parse_cargo_toml(manifest)

    assert dependencies == {"pyo3", "wasm-bindgen", "approx", "windows"}
    assert self_names == {"demo-rust"}


def test_parse_notices_extracts_package_identifiers(tmp_path: Path) -> None:
    """NOTICES 表格首列中的包名应被提取并归一化。"""
    notices = tmp_path / "NOTICES.md"
    notices.write_text(
        "| 组件 | 许可 | 说明 |\n"
        "|------|------|------|\n"
        "| PySide6 | LGPL-3.0-only | GUI |\n"
        "| MUI（`@mui/material`、`@mui/icons-material`） | MIT | 组件库 |\n"
        "| React / React DOM | MIT | 前端 |\n",
        encoding="utf-8",
    )

    parsed = check_licenses.parse_notices(notices)
    assert {
        "pyside6",
        "@mui/material",
        "@mui/icons-material",
        "react",
    } <= parsed
    assert "react-dom" in parsed or "dom" in parsed


def test_find_missing_reports_unknown_components() -> None:
    """未在 NOTICES 中出现的依赖必须报告，并保留来源清单。"""
    dependencies = {
        "react": {"web/frontend/package.json"},
        "mystery-pkg": {"requirements.txt"},
    }

    assert check_licenses.find_missing(dependencies, {"react"}) == {"mystery-pkg": {"requirements.txt"}}


def test_find_missing_accepts_exact_scoped_name() -> None:
    """NOTICES 写 @scope/name 时，清单中的同包应视为已覆盖。"""
    dependencies = {"@mui/material": {"package.json"}}
    notices = {"@mui/material"}

    assert check_licenses.find_missing(dependencies, notices) == {}


def test_collect_dependencies_excludes_local_projects(tmp_path: Path) -> None:
    """仓库自身的包名不应要求出现在 NOTICES 中。"""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "local-pkg"\ndependencies = ["local-pkg", "httpx"]\n',
        encoding="utf-8",
    )

    dependencies = check_licenses.collect_dependencies([pyproject])

    assert dependencies == {"httpx": {str(pyproject)}}


def test_repository_notices_cover_all_direct_dependencies() -> None:
    """仓库实际清单必须全部被 NOTICES 覆盖。"""
    assert check_licenses.main([]) == 0


def test_main_writes_json_report(tmp_path: Path) -> None:
    """--json-out 应输出机器可读的缺口报告。"""
    report = tmp_path / "license-coverage.json"

    exit_code = check_licenses.main(["--json-out", str(report)])

    assert exit_code == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["missing"] == {}
    assert payload["checked_manifests"]
