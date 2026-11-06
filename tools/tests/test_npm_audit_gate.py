# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""npm_audit_gate 误报过滤行为测试。"""

from __future__ import annotations

from tools.quality.npm_audit_gate import (
    filter_vulnerabilities,
    should_fail,
    version_gte,
)


def test_version_gte_handles_patch() -> None:
    assert version_gte("7.18.2", "7.18.2")
    assert version_gte("7.18.3", "7.18.2")
    assert not version_gte("7.18.1", "7.18.2")


def test_suppress_ghsa_when_patched() -> None:
    audit = {
        "vulnerabilities": {
            "react-router": {
                "name": "react-router",
                "severity": "high",
                "via": [
                    {
                        "source": 1,
                        "name": "react-router",
                        "url": "https://github.com/advisories/GHSA-qwww-vcr4-c8h2",
                        "title": "RSC CSRF",
                        "severity": "high",
                    }
                ],
            },
            "react-router-dom": {
                "name": "react-router-dom",
                "severity": "high",
                "via": ["react-router"],
            },
        }
    }
    lock = {
        "packages": {
            "node_modules/react-router": {"version": "7.18.2"},
        }
    }
    remaining, suppressed = filter_vulnerabilities(audit, lock_data=lock)
    assert remaining == {}
    assert any("GHSA-qwww-vcr4-c8h2" in s for s in suppressed)
    assert any("react-router-dom" in s for s in suppressed)


def test_keep_when_unpatched() -> None:
    audit = {
        "vulnerabilities": {
            "react-router": {
                "name": "react-router",
                "severity": "high",
                "via": [
                    {
                        "url": "https://github.com/advisories/GHSA-qwww-vcr4-c8h2",
                        "severity": "high",
                    }
                ],
            }
        }
    }
    lock = {"packages": {"node_modules/react-router": {"version": "7.17.0"}}}
    remaining, _ = filter_vulnerabilities(audit, lock_data=lock)
    assert "react-router" in remaining


def test_should_fail_respects_level() -> None:
    assert should_fail("high", "low")
    assert not should_fail(None, "low")
    assert not should_fail("low", "high")


def test_accepted_risk_suppressed_with_reason() -> None:
    """无上游修复的构建期漏洞按接受风险处理，并打印原因。"""
    audit = {
        "vulnerabilities": {
            "glob": {
                "name": "glob",
                "severity": "moderate",
                "via": [
                    {
                        "url": "https://github.com/advisories/GHSA-3g3m-2fjr-6pw4",
                        "title": "Glob: AbortSignal cancellation bypass",
                        "severity": "moderate",
                    }
                ],
            },
            "workbox-build": {
                "name": "workbox-build",
                "severity": "moderate",
                "via": ["glob"],
            },
        }
    }
    lock = {"packages": {"node_modules/glob": {"version": "11.1.0"}}}
    remaining, suppressed = filter_vulnerabilities(audit, lock_data=lock)
    assert remaining == {}
    assert any("接受风险" in s and "GHSA-3g3m-2fjr-6pw4" in s for s in suppressed)
    assert any("workbox-build" in s for s in suppressed)


def test_accepted_risk_not_suppressed_outside_vulnerable_range() -> None:
    """版本超出受影响上限时不再按接受风险放行，避免掩盖新问题。"""
    audit = {
        "vulnerabilities": {
            "glob": {
                "name": "glob",
                "severity": "moderate",
                "via": [{"url": "https://github.com/advisories/GHSA-3g3m-2fjr-6pw4"}],
            }
        }
    }
    lock = {"packages": {"node_modules/glob": {"version": "15.0.0"}}}
    remaining, _ = filter_vulnerabilities(audit, lock_data=lock)
    assert "glob" in remaining
