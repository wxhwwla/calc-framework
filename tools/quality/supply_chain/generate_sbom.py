#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""从仓库清单与锁文件生成 CycloneDX 1.5 JSON SBOM。

覆盖：

- ``requirements*.txt`` / ``pyproject.toml``：未锁定的 Python 直接依赖，保留原始版本范围；
- ``package-lock.json``：npm 直接与传递依赖（含许可证字段）；
- ``Cargo.lock``：Rust crate（含校验和来源）。

输出用于发布审计与 ``pip-audit`` 结果映射；不替代许可证法律审查。

用法（仓库根目录）::

    python tools/quality/supply_chain/generate_sbom.py
    python tools/quality/supply_chain/generate_sbom.py --output sbom.cdx.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import tomllib

REPO = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = Path("sbom.cdx.json")
TOOL_NAME = "calc-framework-sbom"
TOOL_VERSION = "1.0.0"
_REQUIREMENT_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\s*(.*)$")
_VERSION_RE = re.compile(r'^_VERSION\s*=\s*"([^"]+)"', re.MULTILINE)


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def parse_requirement(line: str) -> dict | None:
    """解析单条依赖字符串为 name + specifier。"""
    candidate = line.split(";", 1)[0].split(" @ ", 1)[0].strip()
    if not candidate or candidate.startswith(("-", "http:", "https:", "git+")):
        return None
    match = _REQUIREMENT_RE.match(candidate)
    if not match:
        return None
    specifier = match.group(2).strip()
    return {"name": _normalize(match.group(1)), "specifier": specifier}


def _python_component(name: str, specifier: str, source: str) -> dict:
    pinned = re.fullmatch(r"==\s*([A-Za-z0-9._+-]+)", specifier)
    version = pinned.group(1) if pinned else "unspecified"
    purl = f"pkg:pypi/{name}" + (f"@{version}" if pinned else "")
    properties = [{"name": "source-manifest", "value": source}]
    if specifier:
        properties.append({"name": "version-specifier", "value": specifier})
    return {
        "type": "library",
        "name": name,
        "version": version,
        "bom-ref": purl,
        "purl": purl,
        "properties": properties,
    }


def components_from_requirements(path: Path, _seen: set[Path] | None = None) -> list[dict]:
    """解析 requirements 文件，递归跟随 -r/--requirement。"""
    seen = _seen if _seen is not None else set()
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        return []
    seen.add(resolved)
    components: list[dict] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.lower().startswith(("-r ", "--requirement ")):
            include = line.split(maxsplit=1)[1].strip()
            components.extend(components_from_requirements((path.parent / include).resolve(), seen))
        elif line.lower().startswith(("-c ", "--constraint ", "-e ", "--editable ")):
            continue
        else:
            parsed = parse_requirement(line)
            if parsed:
                components.append(_python_component(parsed["name"], parsed["specifier"], str(path)))
    return components


def components_from_pyproject(path: Path) -> list[dict]:
    """解析 pyproject 的运行时、可选与构建依赖。"""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    lines = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        lines.extend(group)
    lines.extend(data.get("build-system", {}).get("requires", []))
    components = []
    for line in lines:
        parsed = parse_requirement(str(line))
        if parsed:
            components.append(_python_component(parsed["name"], parsed["specifier"], str(path)))
    return components


def components_from_package_lock(path: Path) -> list[dict]:
    """解析 package-lock.json 的 packages 映射。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    components: list[dict] = []
    for key, entry in data.get("packages", {}).items():
        if not key or entry.get("link") or not entry.get("version"):
            continue
        name = entry.get("name") or key.rsplit("node_modules/", 1)[-1]
        version = str(entry["version"])
        purl = f"pkg:npm/{quote(name, safe='/')}@{version}"
        component = {
            "type": "library",
            "name": name,
            "version": version,
            "bom-ref": purl,
            "purl": purl,
            "scope": "optional" if entry.get("dev") else "required",
        }
        license_name = entry.get("license")
        if isinstance(license_name, str) and license_name:
            component["licenses"] = [{"license": {"name": license_name}}]
        elif isinstance(license_name, dict) and license_name.get("type"):
            component["licenses"] = [{"license": {"name": license_name["type"]}}]
        components.append(component)
    return components


def components_from_cargo_lock(path: Path) -> list[dict]:
    """解析 Cargo.lock，跳过无 source 的本地根包。"""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    components: list[dict] = []
    for package in data.get("package", []):
        if not package.get("source") or not package.get("version"):
            continue
        name = str(package["name"])
        version = str(package["version"])
        purl = f"pkg:cargo/{name}@{version}"
        component = {
            "type": "library",
            "name": name,
            "version": version,
            "bom-ref": purl,
            "purl": purl,
            "properties": [{"name": "source-lock", "value": str(path)}],
        }
        if package.get("checksum"):
            component["hashes"] = [{"alg": "SHA-256", "content": package["checksum"]}]
        components.append(component)
    return components


def _read_version(repo: Path) -> str:
    version_file = repo / "scripts" / "_version.py"
    if version_file.is_file():
        match = _VERSION_RE.search(version_file.read_text(encoding="utf-8"))
        if match:
            return match.group(1)
    return "unknown"


def collect_components(repo: Path = REPO) -> list[dict]:
    """收集仓库内所有支持的清单/锁文件组件并去重。"""
    components: list[dict] = []
    for path in sorted(repo.rglob("requirements*.txt")):
        if "node_modules" not in path.parts and ".venv" not in path.parts:
            components.extend(components_from_requirements(path))
    for path in sorted(repo.rglob("pyproject.toml")):
        if not any(part in {".venv", "node_modules", "dist", "build"} for part in path.parts):
            components.extend(components_from_pyproject(path))
    for path in sorted(repo.rglob("package-lock.json")):
        if "node_modules" not in path.parts:
            components.extend(components_from_package_lock(path))
    for path in sorted(repo.rglob("Cargo.lock")):
        if "target" not in path.parts:
            components.extend(components_from_cargo_lock(path))

    deduped: dict[str, dict] = {}
    for component in components:
        deduped.setdefault(component["bom-ref"], component)
    return [deduped[ref] for ref in sorted(deduped)]


def build_sbom(components: list[dict], *, version: str, generated_at: str | None = None) -> dict:
    """构建确定性 serialNumber 的 CycloneDX 1.5 文档。"""
    ordered = sorted(components, key=lambda item: item["bom-ref"])
    seed = "|".join(f"{item['bom-ref']}@{item.get('version')}" for item in ordered)
    serial = uuid.uuid5(uuid.NAMESPACE_URL, f"calc-framework-sbom:{version}:{seed}")
    timestamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{serial}",
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": {
                "components": [
                    {
                        "type": "application",
                        "name": TOOL_NAME,
                        "version": TOOL_VERSION,
                    }
                ]
            },
            "component": {
                "type": "application",
                "name": "calc-framework-platform",
                "version": version,
                "bom-ref": f"calc-framework-platform@{version}",
            },
        },
        "components": ordered,
    }


def validate_sbom(document: dict) -> list[str]:
    """校验 CycloneDX 必填字段与组件唯一性。"""
    errors: list[str] = []
    if document.get("bomFormat") != "CycloneDX":
        errors.append("缺少或错误的 bomFormat")
    if not document.get("specVersion"):
        errors.append("缺少 specVersion")
    components = document.get("components")
    if not isinstance(components, list) or not components:
        errors.append("缺少 components")
        return errors
    seen: set[str] = set()
    for index, component in enumerate(components):
        for field in ("name", "version", "bom-ref", "purl"):
            if not component.get(field):
                errors.append(f"components[{index}] 缺少 {field}")
        ref = component.get("bom-ref")
        if ref in seen:
            errors.append(f"重复 bom-ref: {ref}")
        elif ref:
            seen.add(ref)
    return errors


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：生成并校验 SBOM。"""
    parser = argparse.ArgumentParser(description="生成 CycloneDX 1.5 SBOM")
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--generated-at", type=str, default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    components = collect_components(args.repo)
    document = build_sbom(
        components,
        version=_read_version(args.repo),
        generated_at=args.generated_at,
    )
    errors = validate_sbom(document)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ecosystems: dict[str, int] = {}
    for component in components:
        ecosystem = component["purl"].split("/", 1)[0].removeprefix("pkg:")
        ecosystems[ecosystem] = ecosystems.get(ecosystem, 0) + 1
    summary = "、".join(f"{key} {value}" for key, value in sorted(ecosystems.items()))
    print(f"SBOM 已写入 {args.output}：{len(components)} 个组件（{summary}）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
