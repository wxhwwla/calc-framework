# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""治理契约测试：所有者、开放债务、安全联系渠道必须可执行且一致。"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
MAINTAINER = "@wxhwwla"
P0_P1_ITEMS = (
    "R-01",
    "R-02",
    "R-03",
    "R-04",
    "R-05",
    "R-06",
    "R-07",
    "R-08",
    "R-09",
    "R-10",
)


def _codeowners_entries() -> list[list[str]]:
    text = (REPO / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    return [line.split() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def test_codeowners_covers_key_directories() -> None:
    """关键目录必须有明确所有者。"""
    entries = _codeowners_entries()
    paths = {entry[0] for entry in entries}

    for required in (
        "/.github/",
        "/docs/",
        "/framework/",
        "/games/",
        "/web/",
        "/tools/",
        "/scripts/",
        "/release_bundle/",
    ):
        assert required in paths, f"CODEOWNERS 缺少 {required}"

    assert all(entry[-1].startswith("@") for entry in entries)


def test_maintainers_lists_roles_and_private_contact() -> None:
    """维护者文件应登记角色、责任人与私密联系邮箱。"""
    text = (REPO / "MAINTAINERS.md").read_text(encoding="utf-8")

    for role in ("项目维护者", "发布负责人", "安全响应", "数据与合规"):
        assert role in text
    assert MAINTAINER in text
    assert "wxhwwla@gmail.com" in text


def test_security_policy_has_private_channel() -> None:
    """SECURITY.md 必须给出可用的私密联系方式，而不是指向 git 历史。"""
    text = (REPO / "SECURITY.md").read_text(encoding="utf-8")

    assert "wxhwwla@gmail.com" in text
    assert "Security Advisory" in text
    assert "见 git 历史提交者信息" not in text


def test_open_debt_registry_covers_all_p0_p1() -> None:
    """所有 P0/P1 审查项都应在治理登记中有负责人、状态和验收条件。"""
    text = (REPO / "docs" / "开放问题与治理.md").read_text(encoding="utf-8")

    assert "docs/项目审查问题与修复清单.md" in text
    for item in P0_P1_ITEMS:
        row = re.search(rf"^\| {item} \|.*$", text, flags=re.MULTILINE)
        assert row is not None, f"治理登记缺少 {item}"
        assert MAINTAINER in row.group(0)
        assert "2027-" in row.group(0)


def test_registry_states_are_from_allowed_vocabulary() -> None:
    """状态必须使用约定枚举，避免自由文本导致无法统计。"""
    text = (REPO / "docs" / "开放问题与治理.md").read_text(encoding="utf-8")
    allowed = {"open", "in-progress", "blocked", "verify", "accepted", "closed"}
    rows = re.findall(r"^\| R-\d+ \| [^|]+ \| ([^|]+) \|", text, flags=re.MULTILINE)

    assert rows
    assert {state.strip() for state in rows} <= allowed
