#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 GitHub 拉取代码并覆盖本地工作区（仓库根目录运行）。

认证：SSH（git@github.com:...），不再依赖 git_key.txt。

警告：会丢弃本地未提交更改，使用前请确认。

用法:
    python github_download_module.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from typing import Any, Tuple

DEFAULT_REMOTE_SSH = "git@github.com:wxhwwla/endfield_damage_calculator_2.0.git"
AUTH_MODE = "ssh"
REMOTE_HTTPS = "https://github.com/wxhwwla/endfield_damage_calculator_2.0.git"
KEY_FILE = "git_key.txt"
DEFAULT_BRANCH = "main"

_TOKEN_IN_REMOTE = re.compile(
    r"https://[^@\s]+@github\.com/",
    re.IGNORECASE,
)


def _decode_output(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        return output
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return str(output)


def run_git(
    args: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
    timeout: int | None = None,
) -> Tuple[int, str, str]:
    try:
        if capture_output:
            proc = subprocess.run(
                ["git"] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf-8",
                errors="replace",
                check=check,
                timeout=timeout,
            )
            return proc.returncode, _decode_output(proc.stdout), _decode_output(proc.stderr)
        proc = subprocess.run(["git"] + args, check=check, timeout=timeout)
        return proc.returncode, "", ""
    except subprocess.CalledProcessError:
        print(f"[错误] Git 命令失败: git {' '.join(args)}")
        raise
    except FileNotFoundError:
        print("[错误] 未找到 git")
        sys.exit(1)


def _repo_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _origin_remote_url() -> str | None:
    if not os.path.isdir(os.path.join(_repo_root(), ".git")):
        return None
    code, url, _ = run_git(
        ["remote", "get-url", "origin"],
        check=False,
        capture_output=True,
    )
    if code != 0:
        return None
    url = url.strip()
    return url or None


def _remote_url() -> str:
    if AUTH_MODE == "ssh":
        origin = _origin_remote_url()
        if origin and not _TOKEN_IN_REMOTE.search(origin):
            return origin
        return DEFAULT_REMOTE_SSH
    if AUTH_MODE == "https_token":
        if not os.path.isfile(KEY_FILE):
            print(f"[错误] 需要 {KEY_FILE} 或改用 AUTH_MODE='ssh'")
            sys.exit(1)
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        path = REMOTE_HTTPS.removeprefix("https://")
        return f"https://wxhwwla:{token}@{path}"
    sys.exit(f"[错误] 未知 AUTH_MODE: {AUTH_MODE}")


def setup_git_repo() -> None:
    os.chdir(_repo_root())
    remote = _remote_url()

    if not os.path.isdir(".git"):
        print("[信息] 初始化 Git 仓库")
        run_git(["init"])
        run_git(["config", "user.name", "wxhwwla"])
        run_git(["config", "user.email", "wxhwwla@gmail.com"])

    _, stdout, _ = run_git(["remote", "-v"], capture_output=True)
    if _TOKEN_IN_REMOTE.search(stdout):
        print("[警告] 原 origin 含嵌入 Token，将替换为 SSH 地址")
    if "origin" not in stdout:
        run_git(["remote", "add", "origin", remote])
    else:
        run_git(["remote", "set-url", "origin", remote])

    _, cur, _ = run_git(["branch", "--show-current"], capture_output=True)
    if cur.strip() != DEFAULT_BRANCH:
        code, _, _ = run_git(["checkout", DEFAULT_BRANCH], check=False, capture_output=True)
        if code != 0:
            run_git(["checkout", "-b", DEFAULT_BRANCH])


def force_pull() -> bool:
    os.chdir(_repo_root())
    print("[信息] 强制与 origin/main 对齐（本地未提交更改将丢失）")

    code, status, _ = run_git(["status", "--porcelain"], capture_output=True)
    if status.strip():
        print("[警告] 存在本地更改，将 reset --hard")

    run_git(["fetch", "origin"], timeout=300)
    code, _, stderr = run_git(
        ["reset", "--hard", f"origin/{DEFAULT_BRANCH}"],
        check=False,
        capture_output=True,
    )
    if code != 0:
        print(f"[错误] reset 失败: {stderr.strip()}")
        return False

    run_git(["clean", "-fd"], check=False)
    print("[成功] 已与远程 main 一致")
    return True


def main() -> None:
    print("=" * 60)
    print("GitHub 拉取脚本（SSH，覆盖本地）")
    print("=" * 60)
    try:
        setup_git_repo()
        if not force_pull():
            sys.exit(1)
        print("=" * 60)
        print("[完成] 本地已与远程同步")
        print("=" * 60)
    except Exception as exc:
        print(f"\n[错误] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
