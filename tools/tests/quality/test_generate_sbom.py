# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""SBOM 生成：清单解析、CycloneDX 结构与仓库覆盖的回归测试。"""

from __future__ import annotations

import json
from pathlib import Path

from tools.quality.supply_chain import generate_sbom


def test_parse_requirement_keeps_specifier() -> None:
    """Python 未锁定版本时保留原始范围，供 SBOM 属性记录。"""
    parsed = generate_sbom.parse_requirement("fastapi>=0.115,<1.0")

    assert parsed == {"name": "fastapi", "specifier": ">=0.115,<1.0"}


def test_components_from_requirements_follow_includes(tmp_path: Path) -> None:
    """requirements 的 -r 引用应被展开。"""
    nested = tmp_path / "nested.txt"
    nested.write_text("httpx>=0.28\n", encoding="utf-8")
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("-r nested.txt\nfastapi>=0.115\n", encoding="utf-8")

    components = generate_sbom.components_from_requirements(manifest)
    refs = {component["bom-ref"] for component in components}

    assert "pkg:pypi/fastapi" in refs
    assert "pkg:pypi/httpx" in refs


def test_components_from_package_lock_include_license(tmp_path: Path) -> None:
    """npm 锁文件应生成带版本与许可证的组件。"""
    lock = tmp_path / "package-lock.json"
    lock.write_text(
        json.dumps(
            {
                "lockfileVersion": 3,
                "packages": {
                    "": {"name": "demo", "version": "1.0.0"},
                    "node_modules/react": {"version": "18.3.1", "license": "MIT"},
                },
            }
        ),
        encoding="utf-8",
    )

    components = generate_sbom.components_from_package_lock(lock)

    assert components == [
        {
            "type": "library",
            "name": "react",
            "version": "18.3.1",
            "bom-ref": "pkg:npm/react@18.3.1",
            "purl": "pkg:npm/react@18.3.1",
            "licenses": [{"license": {"name": "MIT"}}],
            "scope": "required",
        }
    ]


def test_components_from_cargo_lock(tmp_path: Path) -> None:
    """Cargo.lock 应生成 crate 组件并跳过根包。"""
    lock = tmp_path / "Cargo.lock"
    lock.write_text(
        """
version = 3

[[package]]
name = "demo"
version = "0.1.0"

[[package]]
name = "wasm-bindgen"
version = "0.2.100"
source = "registry+https://github.com/rust-lang/crates.io-index"
checksum = "abc"
""",
        encoding="utf-8",
    )

    components = generate_sbom.components_from_cargo_lock(lock)

    assert [component["purl"] for component in components] == ["pkg:cargo/wasm-bindgen@0.2.100"]


def test_build_sbom_is_deterministic_and_valid() -> None:
    """相同组件应生成相同 serialNumber，且结构通过自校验。"""
    components = [
        {
            "type": "library",
            "name": "fastapi",
            "version": "unspecified",
            "bom-ref": "pkg:pypi/fastapi",
            "purl": "pkg:pypi/fastapi",
            "properties": [{"name": "specifier", "value": ">=0.115"}],
        }
    ]

    first = generate_sbom.build_sbom(components, version="3.31.3")
    second = generate_sbom.build_sbom(components, version="3.31.3")

    assert first["serialNumber"] == second["serialNumber"]
    assert first["bomFormat"] == "CycloneDX"
    assert first["specVersion"] == "1.5"
    assert generate_sbom.validate_sbom(first) == []


def test_validate_sbom_rejects_missing_fields() -> None:
    """缺少 specVersion 或组件字段时必须报错。"""
    errors = generate_sbom.validate_sbom({"bomFormat": "CycloneDX", "components": [{"name": "x"}]})

    assert any("specVersion" in error for error in errors)
    assert any("bom-ref" in error for error in errors)


def test_repository_sbom_covers_all_ecosystems(tmp_path: Path) -> None:
    """真实仓库 SBOM 应同时包含 Python、npm 与 Cargo 组件。"""
    output = tmp_path / "sbom.cdx.json"

    assert generate_sbom.main(["--output", str(output)]) == 0

    document = json.loads(output.read_text(encoding="utf-8"))
    purls = {component["purl"] for component in document["components"]}
    assert any(purl.startswith("pkg:pypi/fastapi") for purl in purls)
    assert any(purl.startswith("pkg:npm/react@") for purl in purls)
    assert any(purl.startswith("pkg:cargo/wasm-bindgen@") for purl in purls)
    assert generate_sbom.validate_sbom(document) == []
