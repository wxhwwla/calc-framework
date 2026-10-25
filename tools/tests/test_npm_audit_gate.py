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
