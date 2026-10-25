# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""code_sign 模块测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from utils.code_sign import CodeSignConfig, iter_pe_files, resolve_code_sign_config, sign_pe_file


def test_resolve_code_sign_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("CODE_SIGN_ENABLED", raising=False)
    monkeypatch.delenv("CODE_SIGN_CERT_SHA1", raising=False)
    cfg = resolve_code_sign_config()
    assert cfg.enabled is False


def test_resolve_code_sign_enabled_with_cert(monkeypatch, tmp_path: Path) -> None:
    fake_tool = tmp_path / "signtool.exe"
    fake_tool.write_text("", encoding="utf-8")
    monkeypatch.setenv("CODE_SIGN_ENABLED", "1")
    monkeypatch.setenv("CODE_SIGN_CERT_SHA1", "ABCD1234")
    monkeypatch.setenv("SIGNTOOL_PATH", str(fake_tool))
    cfg = resolve_code_sign_config()
    assert cfg.enabled is True
    assert cfg.cert_sha1 == "ABCD1234"
    assert cfg.signtool == fake_tool


def test_iter_pe_files(tmp_path: Path) -> None:
    (tmp_path / "app.exe").write_bytes(b"pe")
    (tmp_path / "readme.txt").write_text("x", encoding="utf-8")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "lib.dll").write_bytes(b"dll")
    names = {p.name for p in iter_pe_files(tmp_path)}
    assert names == {"app.exe", "lib.dll"}


def test_sign_pe_file_skips_when_disabled(tmp_path: Path) -> None:
    exe = tmp_path / "app.exe"
    exe.write_bytes(b"pe")
    cfg = CodeSignConfig(
        enabled=False,
        signtool=None,
        cert_sha1=None,
        pfx_path=None,
        pfx_password=None,
        timestamp_url="http://timestamp.digicert.com",
        description="test",
    )
    assert sign_pe_file(exe, cfg) is False


@patch("utils.code_sign.subprocess.run")
def test_sign_pe_file_invokes_signtool(mock_run, tmp_path: Path) -> None:
    fake_tool = tmp_path / "signtool.exe"
    fake_tool.write_text("", encoding="utf-8")
    exe = tmp_path / "Game Calc Platform.exe"
    exe.write_bytes(b"pe")
    mock_run.return_value.returncode = 0
    cfg = CodeSignConfig(
        enabled=True,
        signtool=fake_tool,
        cert_sha1="ABCD",
        pfx_path=None,
        pfx_password=None,
        timestamp_url="http://timestamp.digicert.com",
        description="Game Calc Platform",
    )
    assert sign_pe_file(exe, cfg) is True
    assert mock_run.called
