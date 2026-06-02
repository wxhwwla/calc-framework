#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据版本自动管理 — sync_all 写入后自动标记数据版本。

数据版本文件：``games/endfield/data/data_version.json``

版本号语义（semver）：
  - MAJOR: 破坏性 schema 变更（手动改）
  - MINOR: 新增实体（干员/武器/装备）
  - PATCH: 已有实体数据值变化

触发时机（在 sync_all --apply 成功写入后调用）：
  1. 检查是否有实际的数据变更（new / updated / added）
  2. 如果有新增实体 → bump MINOR
  3. 如果只有值变化 → bump PATCH
  4. 如果无变更 → 不 bump
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


# 数据版本文件路径（相对于仓库根）
DATA_VERSION_RELPATH = "games/endfield/data/data_version.json"

# 验证测试路径
VERIFY_TEST_PATHS = [
    "games/endfield/tests/test_calculation.py",
    "games/endfield/tests/test_game_data_contract.py",
]


def _repo_root() -> Path:
    """返回仓库根目录路径（通过 __file__ 推算）。"""
    return Path(__file__).resolve().parents[2]


def data_version_path() -> Path:
    """data_version_path 实现。"""
    return _repo_root() / DATA_VERSION_RELPATH


def read_data_version(path: Path | None = None) -> dict[str, Any]:
    """读取数据版本文件，不存在时返回默认版本。"""
    p = path or data_version_path()
    if not p.is_file():
        return {"version": "1.0.0"}
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def write_data_version(state: dict[str, Any], path: Path | None = None) -> None:
    """写入数据版本文件。"""
    p = path or data_version_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_semver(version: str) -> tuple[int, int, int]:
    """解析 semver 字符串 → (major, minor, patch)。"""
    parts = version.split(".")
    major = int(parts[0]) if len(parts) > 0 else 1
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return (major, minor, patch)


def format_semver(major: int, minor: int, patch: int) -> str:
    """ format_semver 实现。

    Args:
        major: 参数描述。
        minor: 参数描述。
        patch: 参数描述。

    Returns:
        返回值描述。
    """
    return f"{major}.{minor}.{patch}"


def bump_patch(version: str) -> str:
    """版本号 PATCH +1。"""
    major, minor, patch = parse_semver(version)
    return format_semver(major, minor, patch + 1)


def bump_minor(version: str) -> str:
    """版本号 MINOR +1，PATCH 归零。"""
    major, minor, _ = parse_semver(version)
    return format_semver(major, minor + 1, 0)


def has_data_changes(sync_results: list[dict[str, Any]]) -> bool:
    """检查同步结果中是否有实际的数据写入。"""
    for result in sync_results:
        if not result.get("dry_run", True):
            updated_count = result.get("updated_count", 0)
            planned = result.get("planned", [])
            added = result.get("added", [])
            if updated_count > 0 or added:
                return True
    return False


def count_new_entities(sync_results: list[dict[str, Any]]) -> int:
    """统计同步结果中的新增实体数量。"""
    total = 0
    for result in sync_results:
        total += len(result.get("added", []))
    return total


def has_updated_values(sync_results: list[dict[str, Any]]) -> bool:
    """检查是否有已有实体的数据值变化。"""
    for result in sync_results:
        if not result.get("dry_run", True):
            updated_count = result.get("updated_count", 0)
            if updated_count > 0:
                return True
    return False


def determine_bump_type(sync_results: list[dict[str, Any]]) -> str | None:
    """根据同步结果判断需要哪种 version bump。

    Returns:
        "minor" — 新增了实体
        "patch" — 只有值变化
        None — 无变更，无需 bump
    """
    if not has_data_changes(sync_results):
        return None
    if count_new_entities(sync_results) > 0:
        return "minor"
    if has_updated_values(sync_results):
        return "patch"
    return None


def bump_data_version(
    sync_results: list[dict[str, Any]],
    data_version_file: Path | None = None,
    force_version: str | None = None,
) -> str | None:
    """根据同步结果自动提升数据版本号。

    参数:
        sync_results: sync_all 各部分的同步结果列表
        data_version_file: 数据版本文件路径，默认使用 data_version_path()
        force_version: 强制指定版本号，跳过自动 bump 判断

    返回:
        新的版本号字符串，无变更时返回 None
    """
    path = data_version_file or data_version_path()
    state = read_data_version(path)
    old_version = state.get("version", "1.0.0")

    if force_version:
        new_version = force_version
    else:
        bump_type = determine_bump_type(sync_results)
        if bump_type is None:
            return None
        if bump_type == "minor":
            new_version = bump_minor(old_version)
        else:
            new_version = bump_patch(old_version)

    state["version"] = new_version
    write_data_version(state, path)
    return new_version


def run_verify_tests() -> dict[str, Any]:
    """运行数据验证测试，返回测试结果摘要。"""
    repo = _repo_root()
    test_args = [
        sys.executable,
        "-m",
        "pytest",
    ] + VERIFY_TEST_PATHS + [
        "-q",
        "--tb=short",
    ]

    result = subprocess.run(
        test_args,
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=120,
    )

    passed = "passed" in result.stdout and "failed" not in result.stdout
    return {
        "passed": passed,
        "stdout": result.stdout[-500:],
        "stderr": result.stderr[-500:],
        "returncode": result.returncode,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI 入口：python -m tools.bwiki_scout.bump_data_version [--force X.Y.Z]

    用法:
        python -m tools.bwiki_scout.bump_data_version
        python -m tools.bwiki_scout.bump_data_version --force 2.0.0
        python -m tools.bwiki_scout.bump_data_version --verify
    """
    if argv is None:
        argv = sys.argv[1:]

    force_version = None
    do_verify = False

    i = 0
    while i < len(argv):
        if argv[i] == "--force" and i + 1 < len(argv):
            force_version = argv[i + 1]
            i += 2
        elif argv[i] == "--verify":
            do_verify = True
            i += 1
        elif argv[i] in ("--help", "-h"):
            _print_help()
            return 0
        else:
            print(f"未知参数: {argv[i]}", file=sys.stderr)
            return 1

    path = data_version_path()
    state = read_data_version(path)
    old_version = state.get("version", "1.0.0")

    if force_version:
        state["version"] = force_version
        write_data_version(state, path)
        print(f"数据版本: {old_version} → {force_version}")
    else:
        print(f"当前数据版本: {old_version}")
        print(f"文件: {path}")

    if do_verify:
        print("\n正在验证数据...")
        verify_result = run_verify_tests()
        if verify_result["passed"]:
            print("✅ 数据验证通过")
        else:
            print("❌ 数据验证失败:")
            if verify_result["stdout"]:
                print(verify_result["stdout"])
            if verify_result["stderr"]:
                print(verify_result["stderr"])

    return 0


def _print_help() -> None:
    """_print_help 实现。"""
    print("""数据版本管理

用法:
  python -m tools.bwiki_scout.bump_data_version            # 查看当前版本
  python -m tools.bwiki_scout.bump_data_version --force 1.2.0  # 强制设版本
  python -m tools.bwiki_scout.bump_data_version --verify   # 查看 + 运行验证
""")


if __name__ == "__main__":
    sys.exit(main())
