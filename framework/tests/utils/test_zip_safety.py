# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""ZIP 条目安全校验测试。"""

from __future__ import annotations

import stat
import zipfile
from pathlib import Path

import pytest
from utils.zip_safety import safe_extractall, validate_zip_member_name


@pytest.mark.parametrize("name", ["a.txt", "assets/icon.png", "dir/sub/file.bin"])
def test_accepts_safe_names(name: str) -> None:
    assert validate_zip_member_name(name).as_posix() == name


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../evil",
        "assets/../../evil",
        "/abs",
        "C:/evil",
        "assets\\evil",
        "a\x00b",
    ],
)
def test_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(ValueError, match="非法|越界"):
        validate_zip_member_name(name)


def _write_zip(path: Path, entries: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    return path


def test_rejects_sibling_prefix_traversal(tmp_path: Path) -> None:
    zip_path = _write_zip(
        tmp_path / "bad.zip",
        {"../extract-evil/pwn.txt": b"pwn"},
    )
    destination = tmp_path / "extract"

    with (
        zipfile.ZipFile(zip_path) as zf,
        pytest.raises(ValueError, match="非法|越界"),
    ):
        safe_extractall(zf, destination, max_entries=100, max_total_bytes=1024)

    assert not (tmp_path / "extract-evil" / "pwn.txt").exists()


def test_extracts_safe_archive(tmp_path: Path) -> None:
    zip_path = _write_zip(tmp_path / "ok.zip", {"a/b.txt": b"ok"})

    with zipfile.ZipFile(zip_path) as zf:
        safe_extractall(zf, tmp_path / "out")

    assert (tmp_path / "out" / "a" / "b.txt").read_bytes() == b"ok"


def test_rejects_too_many_entries(tmp_path: Path) -> None:
    zip_path = _write_zip(tmp_path / "many.zip", {"a.txt": b"a", "b.txt": b"b"})

    with (
        zipfile.ZipFile(zip_path) as zf,
        pytest.raises(ValueError, match="条目过多"),
    ):
        safe_extractall(zf, tmp_path / "out", max_entries=1)


def test_rejects_oversized_archive(tmp_path: Path) -> None:
    zip_path = _write_zip(tmp_path / "big.zip", {"a.bin": b"x" * 100})

    with (
        zipfile.ZipFile(zip_path) as zf,
        pytest.raises(ValueError, match="超过"),
    ):
        safe_extractall(zf, tmp_path / "out", max_total_bytes=10)


def test_rejects_symlink_entries(tmp_path: Path) -> None:
    zip_path = tmp_path / "link.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        info = zipfile.ZipInfo("link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(info, "target")

    with (
        zipfile.ZipFile(zip_path) as zf,
        pytest.raises(ValueError, match="符号链接"),
    ):
        safe_extractall(zf, tmp_path / "out")
