# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Windows Authenticode 代码签名（可选）。

通过环境变量或 CLI 启用，未配置证书时跳过签名（本地开发不受影响）。

环境变量::

    CODE_SIGN_ENABLED=1
    CODE_SIGN_CERT_SHA1=<证书指纹>   # signtool /sha1
    CODE_SIGN_TIMESTAMP_URL=http://timestamp.digicert.com  # 可选
    CODE_SIGN_DESCRIPTION=Game Calc Platform               # 可选
    SIGNTOOL_PATH=C:\\Program Files\\...\\signtool.exe     # 可选

CI 亦可使用 PFX::

    CODE_SIGN_PFX_PATH=path/to/cert.pfx
    CODE_SIGN_PFX_PASSWORD=secret
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_TIMESTAMP = "http://timestamp.digicert.com"
_PE_SUFFIXES = (".exe", ".dll", ".msi")


@dataclass(frozen=True)
class CodeSignConfig:
    """代码签名运行时配置。"""

    enabled: bool
    signtool: Path | None
    cert_sha1: str | None
    pfx_path: Path | None
    pfx_password: str | None
    timestamp_url: str
    description: str


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def find_signtool() -> Path | None:
    """定位 ``signtool.exe``（PATH 或 Windows SDK 常见路径）。"""
    override = os.environ.get("SIGNTOOL_PATH", "").strip()
    if override:
        path = Path(override)
        if path.is_file():
            return path

    found = shutil.which("signtool")
    if found:
        return Path(found)

    program_files = os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)")
    kits_root = Path(program_files) / "Windows Kits" / "10" / "bin"
    if kits_root.is_dir():
        candidates = sorted(kits_root.glob("*/x64/signtool.exe"), reverse=True)
        if candidates:
            return candidates[0]
    return None


def resolve_code_sign_config() -> CodeSignConfig:
    """从环境变量解析签名配置。"""
    pfx_raw = os.environ.get("CODE_SIGN_PFX_PATH", "").strip()
    pfx_path = Path(pfx_raw) if pfx_raw else None
    cert_sha1 = os.environ.get("CODE_SIGN_CERT_SHA1", "").strip() or None
    has_material = bool(cert_sha1 or (pfx_path and pfx_path.is_file()))
    enabled = _env_truthy("CODE_SIGN_ENABLED") and has_material
    return CodeSignConfig(
        enabled=enabled,
        signtool=find_signtool() if enabled else None,
        cert_sha1=cert_sha1,
        pfx_path=pfx_path if pfx_path and pfx_path.is_file() else None,
        pfx_password=os.environ.get("CODE_SIGN_PFX_PASSWORD", "").strip() or None,
        timestamp_url=os.environ.get("CODE_SIGN_TIMESTAMP_URL", _DEFAULT_TIMESTAMP).strip() or _DEFAULT_TIMESTAMP,
        description=os.environ.get("CODE_SIGN_DESCRIPTION", "Game Calc Platform").strip() or "Game Calc Platform",
    )


def _build_sign_cmd(config: CodeSignConfig, target: Path) -> list[str]:
    if config.signtool is None:
        raise FileNotFoundError("signtool.exe 未找到")
    cmd = [
        str(config.signtool),
        "sign",
        "/fd",
        "SHA256",
        "/tr",
        config.timestamp_url,
        "/td",
        "SHA256",
        "/d",
        config.description,
    ]
    if config.pfx_path is not None:
        cmd.extend(["/f", str(config.pfx_path)])
        if config.pfx_password:
            cmd.extend(["/p", config.pfx_password])
    elif config.cert_sha1:
        cmd.extend(["/sha1", config.cert_sha1])
    else:
        raise ValueError("未配置 CODE_SIGN_CERT_SHA1 或 CODE_SIGN_PFX_PATH")
    cmd.append(str(target))
    return cmd


def sign_pe_file(path: Path, config: CodeSignConfig | None = None) -> bool:
    """对单个 PE 文件签名；未启用或失败时返回 False。"""
    cfg = config or resolve_code_sign_config()
    if not cfg.enabled:
        return False
    if path.suffix.lower() not in _PE_SUFFIXES:
        return False
    if not path.is_file():
        return False
    if cfg.signtool is None or not cfg.signtool.is_file():
        return False
    cmd = _build_sign_cmd(cfg, path)
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return result.returncode == 0


def iter_pe_files(root: Path) -> list[Path]:
    """枚举发布目录内待签名的 PE 文件。"""
    if not root.is_dir():
        return []
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in _PE_SUFFIXES:
            files.append(path)
    return sorted(files)


def sign_release_tree(root: Path, config: CodeSignConfig | None = None) -> list[Path]:
    """签名发布目录内全部 PE；返回成功签名的路径列表。"""
    cfg = config or resolve_code_sign_config()
    if not cfg.enabled:
        return []
    signed: list[Path] = []
    for pe in iter_pe_files(root):
        if sign_pe_file(pe, cfg):
            signed.append(pe)
    return signed
