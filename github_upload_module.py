
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将本仓库推送到 GitHub（仓库根目录运行，与脚本同目录）。

认证：SSH（git@github.com:...），勿将 Token 写入 remote URL。

用法:
    python github_upload_module.py              # 默认 patch +1，交互可选 minor
    python github_upload_module.py --minor      # 第二位 +1（新武器/新乘区等）
    python github_upload_module.py --no-bump    # 提交并推送，但不改 _VERSION

版本与提交说明流程详见 endfield_damage_calculator/please_read_me.py 中的 UPLOAD_WORKFLOW。
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Tuple

# ===== 配置区 =====
DEFAULT_REMOTE_SSH = "git@github.com:wxhwwla/endfield_damage_calculator_2.0.git"
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


def _package_path() -> Path:
    return Path(_repo_root()) / TARGET_DIR


def _import_upload_meta():
    """从 Python 包目录加载 upload_meta（运行时改 sys.path；见仓库根 pyrightconfig.json）。"""
    pkg = str(_package_path())
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    import upload_meta  # noqa: E402  # pyright: 依赖 extraPaths，运行时由上方 sys.path 保证

    return upload_meta


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
        print("[警告] 检测到 origin 含嵌入 Token 的 HTTPS 地址，将改为 SSH/新地址")


def _ensure_gitignore(repo_dir: str) -> None:
    path = os.path.join(repo_dir, ".gitignore")
    wanted = [
        KEY_FILE,
        "git_key.txt",
        ".git-upload-msg.txt",
        "__pycache__/",
        "*.py[cod]",
        ".venv/",
        "build/",
        "dist/",
        "*.spec",
        "*.exe",
        "终末地伤害计算器.exe",
        "*.log",
        "debug.log",
        "skills-lock.json",
        ".pytest_cache/",
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


def _porcelain_paths(porcelain: str) -> List[str]:
    paths: List[str] = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        rest = line[3:].strip()
        if " -> " in rest:
            rest = rest.split(" -> ")[-1].strip()
        if rest:
            paths.append(rest)
    return paths


def _collect_change_paths() -> List[str]:
    _, porcelain, _ = run_git(["status", "--porcelain"], capture_output=True)
    paths = _porcelain_paths(porcelain)
    _, diff_unstaged, _ = run_git(["diff", "--name-only"], check=False, capture_output=True)
    _, diff_staged, _ = run_git(["diff", "--cached", "--name-only"], check=False, capture_output=True)
    for chunk in (diff_unstaged, diff_staged):
        for line in chunk.splitlines():
            p = line.strip()
            if p:
                paths.append(p)
    return paths


def _ask_bump_kind(*, minor_flag: bool, no_bump: bool) -> Optional[str]:
    if no_bump:
        return None
    if minor_flag:
        return "minor"
    if sys.stdin.isatty():
        print("版本升级: [P]atch 第三位+1 (回车默认) / [M]inor 第二位+1")
        choice = input("> ").strip().lower()
        if choice in ("m", "minor"):
            return "minor"
        return "patch"
    return "patch"


def _commit_with_message(message: str) -> None:
    msg_path = os.path.join(_repo_root(), ".git-upload-msg.txt")
    with open(msg_path, "w", encoding="utf-8") as f:
        f.write(message)
        f.write("\n")
    try:
        run_git(["commit", "-F", msg_path])
    finally:
        if os.path.isfile(msg_path):
            os.remove(msg_path)


def _push_to_remote() -> bool:
    push_args = ["push", "origin", DEFAULT_BRANCH]
    if FORCE_PUSH:
        push_args.append("--force-with-lease")
        print("[警告] 使用 --force-with-lease 推送")
    print("[信息] git push ...")
    try:
        run_git(push_args, timeout=300)
        print("[成功] 推送完成")
        return True
    except subprocess.CalledProcessError:
        if SKIP_PULL:
            print("[错误] 推送失败；可稍后重试，或使用 --no-bump 仅补推")
            raise
        print("[信息] 推送失败，尝试 pull --rebase 后重试")
        run_git(["pull", "--rebase", "origin", DEFAULT_BRANCH], timeout=300)
        run_git(push_args, timeout=300)
        print("[成功] 推送完成")
        return True


def commit_and_push(*, minor: bool = False, no_bump: bool = False) -> None:
    os.chdir(_repo_root())
    target_path = os.path.join(".", TARGET_DIR)
    if not os.path.isdir(target_path):
        print(f"[错误] 目录不存在: {TARGET_DIR}")
        sys.exit(1)
    if not any(os.scandir(target_path)):
        print(f"[错误] 目录为空: {TARGET_DIR}")
        sys.exit(1)

    meta = _import_upload_meta()
    readme_path = meta.please_read_me_path(_package_path())

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
                print(f"[信息] 已有 {ahead.strip()} 个提交未推送（不 bump 版本）")

    created_commit = False
    push_succeeded = False

    if not has_unpushed:
        change_paths = _collect_change_paths()
        business = meta.classify_changed_paths(change_paths, TARGET_DIR)

        _, porcelain, _ = run_git(["status", "--porcelain"], capture_output=True)
        if not porcelain.strip():
            print("[信息] 无新更改，无需提交")
            if remote_exists:
                print("[完成] 与远程一致")
            return

        if not business:
            print("[信息] 仅 please_read_me.py 有改动，视为非业务提交，不 bump 版本")
            no_bump = True

        version_for_msg = meta.read_version(readme_path)
        if business and not no_bump:
            kind = _ask_bump_kind(minor_flag=minor, no_bump=False)
            current = meta.read_version(readme_path)
            if kind == "minor":
                version_for_msg = meta.bump_minor(current)
                print(f"[信息] 版本 minor: {current} → {version_for_msg}")
            else:
                version_for_msg = meta.bump_patch(current)
                print(f"[信息] 版本 patch: {current} → {version_for_msg}")
            meta.write_version(readme_path, version_for_msg)

        title, bullets = meta.summarize_changes(change_paths)
        meta.write_summary_block(readme_path, title, bullets)
        print(f"[信息] 已写入上传总结至 {readme_path.name} 底部")

        print("[信息] git add .")
        run_git(["add", "."])

        title_read, bullets_read = meta.read_summary_for_commit(readme_path)
        commit_msg = meta.build_commit_message(version_for_msg, title_read, bullets_read)
        print(f"[信息] git commit:\n{commit_msg.splitlines()[0]} ...")
        _commit_with_message(commit_msg)
        created_commit = True
    else:
        print("[信息] 跳过新版本 commit，仅推送已有提交")

    try:
        push_succeeded = _push_to_remote()
    except subprocess.CalledProcessError:
        push_succeeded = False
        print("[警告] 推送未成功；please_read_me 底部总结块已保留，版本未回滚")
        raise

    if push_succeeded and created_commit:
        meta.remove_summary_block(readme_path)
        print(f"[信息] 已删除 {readme_path.name} 底部 UPLOAD_SUMMARY 块")
        print(f"[信息] 当前 _VERSION = {meta.read_version(readme_path)}（_EXE_VERSION 请打包前自行修改）")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="推送本仓库到 GitHub（SSH），并按规则更新 _VERSION。",
    )
    parser.add_argument(
        "--minor",
        action="store_true",
        help="第二位版本 +1、第三位归零（新武器/新乘区等）",
    )
    parser.add_argument(
        "--no-bump",
        action="store_true",
        help="本次有业务改动也不递增 _VERSION",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.minor and args.no_bump:
        print("[错误] --minor 与 --no-bump 不能同时使用")
        sys.exit(1)

    print("=" * 60)
    print("GitHub 上传脚本（SSH）")
    print("=" * 60)
    try:
        setup_git_repo()
        if not sync_with_remote():
            print("[中止] 同步远程失败，未推送")
            sys.exit(1)
        commit_and_push(minor=args.minor, no_bump=args.no_bump)
        print("=" * 60)
        print("[完成]")
        print("=" * 60)
    except Exception as exc:
        print(f"\n[错误] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
