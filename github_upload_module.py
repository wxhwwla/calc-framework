#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将本仓库推送到 GitHub（仓库根目录运行，与脚本同目录）。

认证方式（推荐）：
    SSH — remote 为 git@github.com:...，需已配置 ~/.ssh 并添加公钥到 GitHub。
    勿再把 Personal Access Token 写入 remote URL 或 git_key.txt。

用法:
    python github_upload_module.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Tuple

# ===== 配置区 =====
# 默认 SSH 地址；若已在仓库内配置 origin，优先使用 origin
DEFAULT_REMOTE_SSH = "git@github.com:wxhwwla/endfield_damage_calculator_2.0.git"
# 仅当无法使用 SSH、且必须用 HTTPS+Token 时改为 "https_token"（不推荐）
AUTH_MODE = "ssh"
REMOTE_HTTPS = "https://github.com/wxhwwla/endfield_damage_calculator_2.0.git"
KEY_FILE = "git_key.txt"

TARGET_DIR = "endfield_damage_calculator"
DEFAULT_BRANCH = "main"
SKIP_PULL = False
FORCE_PUSH = False
# =================

_SCRIPT_NAME = os.path.basename(__file__)
_DOWNLOAD_SCRIPT = "github_download_module.py"
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
    if isinstance(output, memoryview):
        return bytes(output).decode("utf-8", errors="replace")
    return str(output)


def run_git(
    args: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
    timeout: int | None = 30,
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
        proc = subprocess.run(
            ["git"] + args,
            check=check,
            timeout=timeout,
        )
        return proc.returncode, "", ""
    except subprocess.CalledProcessError as e:
        print(f"[错误] Git 命令失败: git {' '.join(args)}")
        print(f"[错误] 返回码: {e.returncode}")
        raise
    except FileNotFoundError:
        print("[错误] 未找到 git，请安装 Git 并加入 PATH")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"[错误] Git 命令超时 ({timeout}s): git {' '.join(args)}")
        raise


def _repo_root() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _origin_remote_url() -> str | None:
    """读取当前仓库 origin；不存在或非 git 仓库时返回 None。"""
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
            print(f"[错误] HTTPS 模式需要 {KEY_FILE}，建议改用 AUTH_MODE = 'ssh'")
            sys.exit(1)
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
        if not token:
            print(f"[错误] {KEY_FILE} 为空")
            sys.exit(1)
        path = REMOTE_HTTPS.removeprefix("https://")
        return f"https://wxhwwla:{token}@{path}"
    print(f"[错误] 未知 AUTH_MODE: {AUTH_MODE}")
    sys.exit(1)


def _warn_if_remote_has_embedded_token(stdout: str) -> None:
    if _TOKEN_IN_REMOTE.search(stdout):
        print("[警告] 检测到 origin 含嵌入 Token 的 HTTPS 地址，将改为 SSH/新地址（请已在 GitHub 撤销旧 Token）")


def _ensure_gitignore(repo_dir: str) -> None:
    """补全根目录 .gitignore 条目（不覆盖已有文件）。"""
    path = os.path.join(repo_dir, ".gitignore")
    wanted = [
        KEY_FILE,
        "git_key.txt",
        ".git/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "build/",
        "dist/",
        "*.spec",
        "*.exe",
        "终末地伤害计算器.exe",
        "debug.log",
        "skills-lock.json",
    ]
    existing = ""
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = f.read()
    to_add = [line for line in wanted if line not in existing]
    if not to_add:
        return
    with open(path, "a", encoding="utf-8") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("\n".join(to_add) + "\n")
    print(f"[信息] 已更新 .gitignore（新增 {len(to_add)} 条）")


def setup_git_repo() -> str:
    script_dir = _repo_root()
    os.chdir(script_dir)

    remote = _remote_url()

    if AUTH_MODE == "ssh":
        print("[信息] 使用 SSH 推送（不在 URL 中携带 Token）")
        code, out, err = run_git(
            ["-T", "git@github.com"],
            check=False,
            capture_output=True,
            timeout=20,
        )
        if code != 1 or "successfully authenticated" not in (out + err).lower():
            print("[警告] SSH 连通性未确认，若推送失败请检查 ~/.ssh 与 GitHub SSH keys")
            print("        22 端口被拦时可配置 Host github.com → ssh.github.com:443")

    _ensure_gitignore(script_dir)

    if not os.path.isdir(".git"):
        print("[信息] 初始化 Git 仓库")
        run_git(["init"])
        run_git(["config", "user.name", "wxhwwla"])
        run_git(["config", "user.email", "wxhwwla@gmail.com"])

    _, current_branch, _ = run_git(["branch", "--show-current"], capture_output=True)
    current_branch = current_branch.strip()
    if current_branch != DEFAULT_BRANCH:
        print(f"[信息] 当前分支「{current_branch}」，切换到 {DEFAULT_BRANCH}")
        code, _, _ = run_git(["checkout", DEFAULT_BRANCH], check=False, capture_output=True)
        if code != 0:
            run_git(["checkout", "-b", DEFAULT_BRANCH])

    _, stdout, _ = run_git(["remote", "-v"], capture_output=True)
    _warn_if_remote_has_embedded_token(stdout)
    if "origin" not in stdout:
        print("[信息] 添加 origin")
        run_git(["remote", "add", "origin", remote])
    else:
        print("[信息] 更新 origin 地址")
        run_git(["remote", "set-url", "origin", remote])

    _, verify, _ = run_git(["remote", "get-url", "origin"], capture_output=True)
    if _TOKEN_IN_REMOTE.search(verify):
        print("[错误] origin 仍含 Token，请手动执行:")
        print(f"  git remote set-url origin {DEFAULT_REMOTE_SSH}")
        sys.exit(1)
    print(f"[信息] origin = {verify.strip()}")
    return remote


def sync_with_remote() -> bool:
    if SKIP_PULL:
        print("[信息] 已跳过拉取（SKIP_PULL=True）")
        return True

    print("[信息] 拉取远程更新...")
    code, stdout, _ = run_git(["rev-list", "--count", "--all"], check=False, capture_output=True)
    has_commits = int(stdout.strip()) > 0 if code == 0 and stdout.strip() else False

    code, status_out, _ = run_git(["status", "--porcelain"], check=False, capture_output=True)
    stashed = False
    if status_out.strip() and has_commits:
        print("[信息] 暂存本地未提交更改")
        stash_code, _, stash_err = run_git(["stash", "push", "-m", "upload-script"], check=False, capture_output=True)
        if stash_code != 0:
            print(f"[警告] 暂存失败: {stash_err.strip()}")
            return False
        stashed = True

    if not has_commits:
        print("[信息] 本地无提交，跳过 pull")
        pull_ok = True
    else:
        code, _, stderr = run_git(
            ["pull", "--rebase", "origin", DEFAULT_BRANCH],
            check=False,
            capture_output=False,
            timeout=300,
        )
        pull_ok = code == 0
        if not pull_ok:
            code2, heads, _ = run_git(
                ["ls-remote", "--heads", "origin", DEFAULT_BRANCH],
                check=False,
                capture_output=True,
            )
            if not heads.strip():
                print("[信息] 远程尚无 main 分支，将首次推送")
                pull_ok = True
            else:
                print(f"[警告] 拉取失败: {stderr.strip()}")

    if stashed and pull_ok:
        code, _, stderr = run_git(["stash", "pop"], check=False, capture_output=True)
        if code != 0:
            print(f"[警告] 恢复暂存失败: {stderr.strip()}")

    return pull_ok


def commit_and_push() -> None:
    os.chdir(_repo_root())
    target_path = os.path.join(".", TARGET_DIR)
    if not os.path.isdir(target_path):
        print(f"[错误] 目录不存在: {TARGET_DIR}")
        sys.exit(1)
    if not any(os.scandir(target_path)):
        print(f"[错误] 目录为空: {TARGET_DIR}")
        sys.exit(1)

    _, remote_heads, _ = run_git(
        ["ls-remote", "--heads", "origin", DEFAULT_BRANCH],
        check=False,
        capture_output=True,
    )
    remote_exists = bool(remote_heads.strip())

    has_unpushed = False
    if remote_exists:
        code, ahead, _ = run_git(
            ["rev-list", "--count", f"origin/{DEFAULT_BRANCH}..{DEFAULT_BRANCH}"],
            check=False,
            capture_output=True,
        )
        if code == 0 and ahead.strip().isdigit():
            has_unpushed = int(ahead.strip()) > 0
            if has_unpushed:
                print(f"[信息] 已有 {ahead.strip()} 个提交未推送")

    if not has_unpushed:
        print("[信息] git add .")
        run_git(["add", "."])
        _, porcelain, _ = run_git(["status", "--porcelain"], capture_output=True)
        if not porcelain.strip():
            print("[信息] 无新更改，无需提交")
            if remote_exists:
                print("[完成] 与远程一致")
            return
        msg = f"Update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        print(f"[信息] git commit: {msg}")
        run_git(["commit", "-m", msg])

    push_args = ["push", "origin", DEFAULT_BRANCH]
    if FORCE_PUSH:
        push_args.append("--force-with-lease")
        print("[警告] 使用 --force-with-lease 推送")

    print("[信息] git push ...")
    try:
        run_git(push_args, timeout=300)
        print("[成功] 推送完成")
    except subprocess.CalledProcessError:
        if SKIP_PULL:
            print("[错误] 推送失败；可尝试 SKIP_PULL=False 先拉取，或检查 SSH/权限")
            raise
        print("[信息] 推送失败，尝试 pull --rebase 后重试")
        run_git(["pull", "--rebase", "origin", DEFAULT_BRANCH], timeout=300)
        run_git(push_args, timeout=300)
        print("[成功] 推送完成")


def main() -> None:
    print("=" * 60)
    print("GitHub 上传脚本（SSH）")
    print("=" * 60)
    try:
        setup_git_repo()
        if not sync_with_remote():
            print("[中止] 同步远程失败，未推送")
            sys.exit(1)
        commit_and_push()
        print("=" * 60)
        print("[完成]")
        print("=" * 60)
    except Exception as exc:
        print(f"\n[错误] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
