#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""第三方许可覆盖门禁：清单中的直接依赖必须出现在 NOTICES.md。

支持 requirements*.txt、pyproject.toml（含 build-system / optional）、
package.json、Cargo.toml，并输出可归档的 JSON 报告。

用法（仓库根目录）::

    python tools/quality/supply_chain/check_licenses.py
    python tools/quality/supply_chain/check_licenses.py --json-out license-coverage.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]

REPO = Path(__file__).resolve().parents[3]
NOTICES_PATH = REPO / "NOTICES.md"

SKIP_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".git",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "node_modules",
        "dist",
        "build",
        "target",
        "output",
        "logs",
        "htmlcov",
    }
)
_REQUIREMENT_PATTERN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
_TOKEN_PATTERN = re.compile(r"[A-Za-z@][A-Za-z0-9@._/\- ]*")
_CARGO_SECTIONS = ("dependencies", "dev-dependencies", "build-dependencies")
_PACKAGE_JSON_GROUPS = (
    "dependencies",
    "devDependencies",
    "optionalDependencies",
    "peerDependencies",
)


def normalize_name(name: str) -> str:
    """按 PEP 503 归一化依赖名（保留 npm scope 的 @/）。"""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _requirement_name(line: str) -> str | None:
    """从 PEP 508 依赖行提取包名；无法识别时返回 None。"""
    candidate = line.split(";", 1)[0].split(" @ ", 1)[0].strip()
    if not candidate or candidate.startswith(("-", "http:", "https:", "git+")):
        return None
    match = _REQUIREMENT_PATTERN.match(candidate)
    return normalize_name(match.group(1)) if match else None


def parse_requirements(path: Path, _seen: set[Path] | None = None) -> set[str]:
    """解析 requirements 文件，递归跟随 -r/--requirement。"""
    seen = _seen if _seen is not None else set()
    resolved = path.resolve()
    if resolved in seen or not path.is_file():
        return set()
    seen.add(resolved)
    names: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(("-r ", "--requirement ")):
            include = line.split(maxsplit=1)[1].strip()
            names |= parse_requirements((path.parent / include).resolve(), seen)
        elif lowered.startswith(("-c ", "--constraint ", "-e ", "--editable ")):
            continue
        else:
            name = _requirement_name(line)
            if name:
                names.add(name)
    return names


def _parse_requirement_list(items: list[str]) -> set[str]:
    return {name for item in items if (name := _requirement_name(str(item))) is not None}


def parse_pyproject(path: Path) -> tuple[set[str], set[str]]:
    """解析 pyproject.toml，返回 (依赖名, 项目自身名)。"""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    build = data.get("build-system", {})
    names = _parse_requirement_list(list(project.get("dependencies", [])))
    for group in project.get("optional-dependencies", {}).values():
        names |= _parse_requirement_list(list(group))
    names |= _parse_requirement_list(list(build.get("requires", [])))
    self_names = {normalize_name(project["name"])} if project.get("name") else set()
    return names, self_names


def parse_package_json(path: Path) -> tuple[set[str], set[str]]:
    """解析 package.json，返回 (依赖名, 包自身名)。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    names = {normalize_name(name) for group in _PACKAGE_JSON_GROUPS for name in data.get(group, {})}
    self_names = {normalize_name(data["name"])} if data.get("name") else set()
    return names, self_names


def _cargo_names(table: dict) -> set[str]:
    names: set[str] = set()
    for section in _CARGO_SECTIONS:
        for key, spec in table.get(section, {}).items():
            package = spec.get("package", key) if isinstance(spec, dict) else key
            names.add(normalize_name(str(package)))
    for target in table.get("target", {}).values():
        names |= _cargo_names(target)
    if "workspace" in table:
        names |= _cargo_names(table["workspace"])
    return names


def parse_cargo_toml(path: Path) -> tuple[set[str], set[str]]:
    """解析 Cargo.toml，返回 (依赖名, crate 自身名)。"""
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    names = _cargo_names(data)
    self_names: set[str] = set()
    for section in ("package", "lib"):
        name = data.get(section, {}).get("name")
        if name:
            self_names.add(normalize_name(str(name)))
    return names, self_names


def _extract_tokens(cell: str) -> set[str]:
    """从 NOTICES 表格首列提取包名标识符。"""
    text = cell.replace("`", " ")
    text = re.sub(r"[（）、，；]|\s+/\s+", "\n", text)
    tokens: set[str] = set()
    for segment in text.splitlines():
        for match in _TOKEN_PATTERN.finditer(segment):
            token = match.group(0).strip().rstrip(".-_ ")
            if not token:
                continue
            token = re.sub(r"\s+", "-", token.lower()).replace("_", "-").replace(".", "-")
            if re.fullmatch(r"@?[a-z0-9][a-z0-9@/_-]*", token):
                tokens.add(token)
    return tokens


def parse_notices(path: Path = NOTICES_PATH) -> set[str]:
    """解析 NOTICES.md 的表格首列，返回已声明的包名集合。"""
    tokens: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        first = cells[0]
        if not first or set(first) <= set("-: "):
            continue
        if first in {"组件", "来源"}:
            continue
        tokens |= _extract_tokens(first)
    return tokens


def _is_skipped(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        parts = path.parts
    return any(part in SKIP_DIR_NAMES for part in parts)


def discover_manifests(repo: Path = REPO) -> list[Path]:
    """发现仓库内所有受支持的依赖清单。"""
    manifests: set[Path] = set()
    for pattern in ("requirements*.txt", "pyproject.toml", "package.json", "Cargo.toml"):
        for path in repo.rglob(pattern):
            if path.is_file() and not _is_skipped(path, repo):
                manifests.add(path)
    return sorted(manifests)


def collect_dependencies(manifests: list[Path]) -> dict[str, set[str]]:
    """汇总清单中的直接依赖，并剔除仓库自身包名。"""
    dependencies: dict[str, set[str]] = {}
    self_names: set[str] = set()
    for path in manifests:
        if path.name == "package.json":
            names, own = parse_package_json(path)
        elif path.name == "Cargo.toml":
            names, own = parse_cargo_toml(path)
        elif path.name == "pyproject.toml":
            names, own = parse_pyproject(path)
        elif path.name.startswith("requirements") and path.suffix == ".txt":
            names, own = parse_requirements(path), set()
        else:
            continue
        self_names |= own
        for name in names:
            dependencies.setdefault(name, set()).add(str(path))
    for own in self_names:
        dependencies.pop(own, None)
    return dependencies


def find_missing(dependencies: dict[str, set[str]], notices: set[str]) -> dict[str, set[str]]:
    """返回未被 NOTICES 覆盖的依赖及其来源清单。"""
    missing: dict[str, set[str]] = {}
    for name, sources in dependencies.items():
        if name in notices:
            continue
        missing[name] = sources
    return missing


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：检查许可覆盖并可选输出 JSON 报告。"""
    parser = argparse.ArgumentParser(description="检查 NOTICES 对直接依赖的覆盖")
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--notices", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args(argv)

    notices_path = args.notices if args.notices is not None else args.repo / "NOTICES.md"
    manifests = discover_manifests(args.repo)
    dependencies = collect_dependencies(manifests)
    notices = parse_notices(notices_path)
    missing = find_missing(dependencies, notices)

    print(
        f"许可覆盖检查：{len(manifests)} 个清单、{len(dependencies)} 个直接依赖、"
        f"NOTICES {len(notices)} 个标识符、{len(missing)} 个缺口。"
    )
    for name in sorted(missing):
        sources = ", ".join(sorted(missing[name]))
        print(f"MISSING: {name}（来源: {sources}）")

    if args.json_out is not None:
        payload = {
            "checked_manifests": [str(path) for path in manifests],
            "dependency_count": len(dependencies),
            "notice_token_count": len(notices),
            "missing": {name: sorted(sources) for name, sources in sorted(missing.items())},
        }
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if missing:
        print(f"许可覆盖检查失败：{len(missing)} 个依赖未在 NOTICES.md 中声明。")
        return 1
    print("许可覆盖检查通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
