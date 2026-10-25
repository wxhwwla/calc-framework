# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""secrets baseline 校验逻辑测试。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

import tools.quality.generate_secrets_baseline as baseline_mod


def test_verify_passes_when_baseline_unchanged(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    baseline = tmp_path / ".secrets.baseline"
    payload = {"version": "1.5.0", "results": {}}
    baseline.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(baseline_mod, "BASELINE", baseline)

    def _fake_scan(*, update: bool) -> str:
        return baseline.read_text(encoding="utf-8")

    monkeypatch.setattr(baseline_mod, "_run_scan", _fake_scan)
    baseline_mod.verify_no_new_secrets()


def test_verify_fails_when_new_secret_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    baseline = tmp_path / ".secrets.baseline"
    before = {"version": "1.5.0", "results": {}}
    after = {
        "version": "1.5.0",
        "results": {
            "fake.py": [
                {
                    "type": "Secret Keyword",
                    "hashed_secret": "abc123",
                    "is_verified": False,
                    "is_secret": True,
                    "line_number": 1,
                }
            ],
        },
    }
    baseline.write_text(json.dumps(before), encoding="utf-8")
    monkeypatch.setattr(baseline_mod, "BASELINE", baseline)

    def _fake_scan(*, update: bool) -> str:
        return json.dumps(after)

    monkeypatch.setattr(baseline_mod, "_run_scan", _fake_scan)
    with pytest.raises(SystemExit) as exc:
        baseline_mod.verify_no_new_secrets()
    assert exc.value.code == 1
