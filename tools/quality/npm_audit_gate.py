# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""npm audit 门禁：过滤已知误报后按严重级别失败。

GitHub Advisory 已标明 ``react-router>=7.18.2`` 修复 GHSA-qwww-vcr4-c8h2，
但 npm 公告库仍用 ``>=7.12.0 <8.3.0`` 范围误伤已打补丁版本。本脚本在确认
已安装版本满足补丁门槛后抑制该条，其余漏洞仍按 ``--audit-level`` 阻断。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# GHSA → 抑制条件（包名 + 最低已修复版本）
_FALSE_POSITIVE_GHSAS: dict[str, tuple[str, str]] = {
    "GHSA-qwww-vcr4-c8h2": ("react-router", "7.18.2"),
}

_SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "moderate": 2,
    "high": 3,
    "critical": 4,
}


def _parse_version(ver: str) -> tuple[int, ...]:
    """解析 semver 主.次.补丁（忽略预发布后缀）。"""
    core = ver.split("-", 1)[0].split("+", 1)[0]
    parts: list[int] = []
    for p in core.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def version_gte(installed: str, minimum: str) -> bool:
    """比较已安装版本是否 >= 最低补丁版本。"""
    return _parse_version(installed) >= _parse_version(minimum)


def installed_package_version(lock_data: dict[str, Any], package: str) -> str | None:
    """从 package-lock v2/v3 的 packages 字段读取依赖版本。"""
    packages = lock_data.get("packages") or {}
    direct = packages.get(f"node_modules/{package}")
    if isinstance(direct, dict) and direct.get("version"):
        return str(direct["version"])
    # 兼容嵌套路径
    suffix = f"/node_modules/{package}"
    for key, meta in packages.items():
        if key.endswith(suffix) and isinstance(meta, dict) and meta.get("version"):
            return str(meta["version"])
    return None


def advisory_ids_from_via(via: Any) -> set[str]:
    """从 npm audit ``via`` 字段提取 GHSA / 标题 URL 中的 advisory id。"""
    ids: set[str] = set()
    if not isinstance(via, list):
        return ids
    for item in via:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "")
        for marker in ("GHSA-", "CVE-"):
            if marker in url:
                # .../GHSA-xxxx 或查询串
                tail = url.rsplit("/", 1)[-1]
                if tail.startswith("GHSA-") or tail.startswith("CVE-"):
                    ids.add(tail.split("?")[0])
        title = str(item.get("title") or "")
        for ghsa in _FALSE_POSITIVE_GHSAS:
            if ghsa in url or ghsa in title:
                ids.add(ghsa)
    return ids


def filter_vulnerabilities(
    audit: dict[str, Any],
    *,
    lock_data: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """过滤可抑制的误报，返回剩余漏洞与抑制说明。"""
    vulns = dict(audit.get("vulnerabilities") or {})
    suppressed: list[str] = []

    for name, meta in list(vulns.items()):
        if not isinstance(meta, dict):
            continue
        ids = advisory_ids_from_via(meta.get("via"))
        for ghsa, (pkg, min_ver) in _FALSE_POSITIVE_GHSAS.items():
            if ghsa not in ids:
                continue
            installed = installed_package_version(lock_data, pkg)
            if installed and version_gte(installed, min_ver):
                vulns.pop(name, None)
                suppressed.append(f"{name}: 抑制 {ghsa}（已安装 {pkg}@{installed} >= {min_ver}）")
                break

    # 级联：via 全是包名且这些包已不在剩余集合中
    changed = True
    while changed:
        changed = False
        for name, meta in list(vulns.items()):
            if not isinstance(meta, dict):
                continue
            via = meta.get("via") or []
            if via and all(isinstance(x, str) for x in via) and all(dep not in vulns for dep in via):
                vulns.pop(name, None)
                suppressed.append(f"{name}: 级联抑制（via={via}）")
                changed = True

    return vulns, suppressed


def max_severity(vulns: dict[str, Any]) -> str | None:
    """返回剩余漏洞中的最高严重级别。"""
    best: str | None = None
    best_rank = -1
    for meta in vulns.values():
        if not isinstance(meta, dict):
            continue
        sev = str(meta.get("severity") or "info").lower()
        rank = _SEVERITY_RANK.get(sev, 0)
        if rank > best_rank:
            best_rank = rank
            best = sev
    return best


def should_fail(highest: str | None, audit_level: str) -> bool:
    """最高严重级别是否达到/超过门禁阈值。"""
    if highest is None:
        return False
    return _SEVERITY_RANK.get(highest, 0) >= _SEVERITY_RANK.get(audit_level, 1)


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：在前端目录执行 npm audit 并应用误报过滤。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cwd",
        default="web/frontend",
        help="npm 项目目录（相对仓库根或绝对路径）",
    )
    parser.add_argument(
        "--audit-level",
        default="low",
        choices=list(_SEVERITY_RANK),
        help="达到该级别及以上则失败（与 npm audit --audit-level 一致）",
    )
    parser.add_argument(
        "--registry",
        default="https://registry.npmjs.org/",
        help="npm registry",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[2]
    cwd = Path(args.cwd)
    if not cwd.is_absolute():
        cwd = repo_root / cwd
    lock_path = cwd / "package-lock.json"
    if not lock_path.is_file():
        print(f"FAIL: 找不到 {lock_path}", file=sys.stderr)
        return 2

    npm = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm:
        print("FAIL: 找不到 npm 可执行文件", file=sys.stderr)
        return 2

    proc = subprocess.run(
        [npm, "audit", "--json", f"--registry={args.registry}"],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    try:
        audit = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        print("FAIL: npm audit 未返回合法 JSON", file=sys.stderr)
        print(proc.stdout or proc.stderr, file=sys.stderr)
        return 2

    lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    remaining, suppressed = filter_vulnerabilities(audit, lock_data=lock_data)
    for line in suppressed:
        print(f"INFO: {line}")

    highest = max_severity(remaining)
    if remaining:
        print(f"剩余漏洞 {len(remaining)} 个（最高级别={highest}）:")
        for name, meta in sorted(remaining.items()):
            sev = meta.get("severity") if isinstance(meta, dict) else "?"
            print(f"  - {name}: {sev}")
    else:
        print("npm audit: 无剩余漏洞（含已抑制误报）")

    if should_fail(highest, args.audit_level):
        print(
            f"FAIL: 最高级别 {highest} >= audit-level={args.audit_level}",
            file=sys.stderr,
        )
        return 1
    print(f"PASS: audit-level={args.audit_level}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
