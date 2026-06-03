# SPDX-License-Identifier: AGPL-3.0


#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

将本仓库推送到 GitHub（仓库根目录运行，与脚本同目录）。



认证：SSH（git@github.com:...），勿将 Token 写入 remote URL。



用法:

    python scripts/tools/github_upload_module.py              # 默认 patch +1，交互可选 minor

    python scripts/tools/github_upload_module.py --minor      # 第二位 +1（新武器/新乘区等）

    python scripts/tools/github_upload_module.py --no-bump    # 提交并推送，但不改 _VERSION



版本与提交说明流程详见 please_read_me.py 中的 UPLOAD_WORKFLOW。



若本机已配置 Git 提交签名（GPG/SSH），脚本会在 commit 时自动签名，便于 GitHub 显示 Verified。

"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ===== 配置区 =====

DEFAULT_REMOTE_SSH = "git@github.com:wxhwwla/calc-framework.git"
AUTH_MODE = "ssh"
REMOTE_HTTPS = "https://github.com/wxhwwla/calc-framework.git"

KEY_FILE = "git_key.txt"


TARGET_DIR = "games/endfield"

DEFAULT_BRANCH = "main"

SKIP_PULL = False

FORCE_PUSH = False

# =================


_SCRIPT_NAME = os.path.basename(__file__)

_DOWNLOAD_SCRIPT = "scripts/tools/github_download_module.py"

_TOKEN_IN_REMOTE = re.compile(
    r"https://[^@\s]+@github\.com/",
    re.IGNORECASE,
)


def _package_path() -> Path:
    """返回游戏包目录路径。"""
    return Path(_repo_root()) / TARGET_DIR


def _import_upload_meta():
    """动态导入 upload_meta 模块。"""
    from scripts._path_setup import ensure_root

    ensure_root()
    from scripts import upload_meta

    return upload_meta


def _decode_output(output: Any) -> str:
    """将命令输出解码为字符串。"""
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
) -> tuple[int, str, str]:
    """执行 git 命令并返回 (returncode, stdout, stderr)。"""
    try:
        if capture_output:
            proc = subprocess.run(
                ["git", *args],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=check,
                timeout=timeout,
            )

            return proc.returncode, _decode_output(proc.stdout), _decode_output(proc.stderr)

        proc = subprocess.run(
            ["git", *args],
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
    """返回仓库根目录的字符串路径。"""
    return str(Path(__file__).resolve().parent.parent.parent)


def _origin_remote_url() -> str | None:
    """从 git 配置读取 origin 远程 URL。"""

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
    """根据 AUTH_MODE 确定 remote 地址（SSH 或 HTTPS+Token）。"""
    if AUTH_MODE == "ssh":
        origin = _origin_remote_url()

        if origin and not _TOKEN_IN_REMOTE.search(origin):
            return origin

        return DEFAULT_REMOTE_SSH

    if AUTH_MODE == "https_token":
        if not os.path.isfile(KEY_FILE):
            print(f"[错误] HTTPS 模式需要 {KEY_FILE}，建议改用 AUTH_MODE = 'ssh'")

            sys.exit(1)

        with open(KEY_FILE, encoding="utf-8") as f:
            token = f.read().strip()

        if not token:
            print(f"[错误] {KEY_FILE} 为空")

            sys.exit(1)

        path = REMOTE_HTTPS.removeprefix("https://")

        return f"https://wxhwwla:{token}@{path}"

    print(f"[错误] 未知 AUTH_MODE: {AUTH_MODE}")

    sys.exit(1)


def _warn_if_remote_has_embedded_token(stdout: str) -> None:
    """检查 remote URL 中是否嵌入了 Token。"""
    if _TOKEN_IN_REMOTE.search(stdout):
        print("[警告] 检测到 origin 含嵌入 Token 的 HTTPS 地址，将改为 SSH/新地址")


def _ensure_gitignore(repo_dir: str) -> None:
    """确保 .gitignore 包含必要的忽略条目。"""
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
        "git_backup/snapshots/",
    ]

    existing = ""

    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
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
    """初始化/检查 git 仓库，配置 remote 和分支。"""
    script_dir = _repo_root()

    os.chdir(script_dir)

    remote = _remote_url()

    if AUTH_MODE == "ssh":
        print("[信息] 使用 SSH 推送（不在 URL 中携带 Token）")

        # 用 ls-remote 实测 SSH（比 git -T 在 Windows 上更可靠）

        probe_code, _, probe_err = run_git(
            ["ls-remote", remote, "HEAD"],
            check=False,
            capture_output=True,
            timeout=30,
        )
        if probe_code != 0:
            hint = (probe_err or "").strip() or f"exit {probe_code}"
            print(f"[警告] SSH 连通性未确认（{hint}），若推送失败请检查 ~/.ssh 与 GitHub SSH keys")

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


def _remote_branch_ref() -> str:
    return f"origin/{DEFAULT_BRANCH}"


def _fetch_origin_main(*, timeout: int = 300) -> None:
    run_git(["fetch", "origin", DEFAULT_BRANCH], check=False, timeout=timeout)


def _count_ahead_behind() -> tuple[int, int]:
    """返回 (领先 origin/main 的 commit 数, 落后数)。"""
    ref = _remote_branch_ref()
    code, _, _ = run_git(["rev-parse", "--verify", ref], check=False, capture_output=True)
    if code != 0:
        return 0, 0
    _, ahead, _ = run_git(
        ["rev-list", "--count", f"{ref}..HEAD"],
        check=False,
        capture_output=True,
    )
    _, behind, _ = run_git(
        ["rev-list", "--count", f"HEAD..{ref}"],
        check=False,
        capture_output=True,
    )
    ahead_n = int(ahead.strip()) if ahead.strip().isdigit() else 0
    behind_n = int(behind.strip()) if behind.strip().isdigit() else 0
    return ahead_n, behind_n


def _stash_error_lines(stderr: str) -> list[str]:
    lines: list[str] = []
    for raw in stderr.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("warning:") and "LF will be replaced by CRLF" in line:
            continue
        lines.append(line)
    return lines


def _stash_dirty_worktree() -> bool:
    """暂存未提交改动；失败时不执行 git reset（避免 Windows 上 .gitignore 锁文件）。"""
    _, status_out, _ = run_git(["status", "--porcelain"], check=False, capture_output=True)
    if not status_out.strip():
        return True

    print("[信息] 暂存本地未提交更改")
    stash_code, _, stash_err = run_git(
        ["stash", "push", "--include-untracked", "-m", "upload-script"],
        check=False,
        capture_output=True,
    )
    if stash_code == 0:
        return True

    issues = _stash_error_lines(stash_err)
    detail = "\n  ".join(issues) if issues else stash_err.strip() or f"exit {stash_code}"
    print(f"[错误] 暂存失败:\n  {detail}")
    print("[提示] 关闭 Cursor/杀毒对仓库的占用后重试，或本次使用 --skip-pull")
    return False


def _pop_stash_if_needed(stashed: bool, *, pull_ok: bool) -> None:
    if not stashed or not pull_ok:
        return
    code, _, stderr = run_git(
        ["stash", "pop", "--index"],
        check=False,
        capture_output=True,
    )
    if code != 0:
        print("[警告] 暂存恢复失败，请手动执行 git stash pop")
        if stderr.strip():
            print(f"[警告] {stderr.strip()}")


def sync_with_remote(*, skip_pull: bool = False) -> bool:
    """拉取远程更新并与本地同步。"""
    if skip_pull or SKIP_PULL:
        print("[信息] 已跳过拉取" + ("（--skip-pull）" if skip_pull else "（SKIP_PULL=True）"))
        return True

    print("[信息] 拉取远程更新...")
    _fetch_origin_main()

    ahead, behind = _count_ahead_behind()
    if behind == 0:
        print(f"[信息] 已与 origin/main 同步（领先 {ahead} commit），跳过 pull")
        return True

    print(f"[信息] 落后 origin/main {behind} 个 commit，执行 pull --rebase...")

    code, stdout, _ = run_git(["rev-list", "--count", "--all"], check=False, capture_output=True)
    has_commits = int(stdout.strip()) > 0 if code == 0 and stdout.strip() else False
    if not has_commits:
        print("[信息] 本地无提交，跳过 pull")
        return True

    stashed = _stash_dirty_worktree()
    if not stashed:
        return False

    code, _, stderr = run_git(
        ["pull", "--rebase", "origin", DEFAULT_BRANCH],
        check=False,
        capture_output=False,
        timeout=300,
    )
    pull_ok = code == 0
    if not pull_ok:
        _code2, heads, _ = run_git(
            ["ls-remote", "--heads", "origin", DEFAULT_BRANCH],
            check=False,
            capture_output=True,
        )
        if not heads.strip():
            print("[信息] 远程尚无 main 分支，将首次推送")
            pull_ok = True
        else:
            print(f"[警告] 拉取失败: {stderr.strip()}")

    _pop_stash_if_needed(stashed, pull_ok=pull_ok)
    return pull_ok


def _porcelain_paths(porcelain: str) -> list[str]:
    """从 git status --porcelain 输出中提取文件路径列表。"""
    paths: list[str] = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue

        rest = line[3:].strip()

        if " -> " in rest:
            rest = rest.split(" -> ")[-1].strip()

        if rest:
            paths.append(rest)

    return paths


def _collect_change_paths() -> list[str]:
    """收集所有已变更文件的路径。"""
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


@dataclass(frozen=True)
class SigningConfig:
    """本机 Git 提交签名配置快照（用于上传脚本 commit）。"""

    gpgsign: str | None

    signingkey: str | None

    gpg_format: str | None


def _is_truthy_git_config(value: str | None) -> bool:
    """判断 git config 值是否等同于 true。"""
    if not value:
        return False

    return value.strip().lower() in {"true", "1", "yes", "on"}


def _git_config_get(key: str) -> str | None:
    """读取 git config（先本地，再 global）。"""

    for scope in ([], ["--global"]):
        args = ["config", *scope, "--get", key] if scope else ["config", "--get", key]

        code, stdout, _ = run_git(args, check=False, capture_output=True)

        if code == 0 and stdout.strip():
            return stdout.strip()

    return None


def resolve_signing_config(
    getter: Callable[[str], str | None] | None = None,
) -> SigningConfig:
    """解析本机 Git 提交签名配置。"""
    read = getter or _git_config_get
    return SigningConfig(
        gpgsign=read("commit.gpgsign"),
        signingkey=read("user.signingkey"),
        gpg_format=read("gpg.format"),
    )


def commit_extra_args(cfg: SigningConfig) -> list[str]:
    """

    返回追加到 `git commit` 的参数。



    - 已开 commit.gpgsign：由 Git 自动签名，无需 -S

    - 仅有 signingkey：对本提交显式 -S

    """

    if _is_truthy_git_config(cfg.gpgsign):
        return []

    if cfg.signingkey and cfg.signingkey.strip():
        return ["-S"]

    return []


def tag_extra_args(cfg: SigningConfig) -> list[str]:
    """

    返回追加到 `git tag` 的参数。



    Git 没有 `tag.gpgsign` 自动签名配置，tag 须显式 -s。

    """

    if is_signing_configured(cfg):
        return ["-s"]

    return []


def is_signing_configured(cfg: SigningConfig) -> bool:
    """判断签名配置是否就绪。"""
    return bool(commit_extra_args(cfg)) or _is_truthy_git_config(cfg.gpgsign)


def signing_status_message(cfg: SigningConfig) -> str:
    """生成签名状态提示消息。"""
    if is_signing_configured(cfg):
        fmt = (cfg.gpg_format or "openpgp").strip().lower()

        return (
            f"[信息] 已配置提交签名（{fmt}），commit 和 tag 均会签名，"
            "推送后 GitHub 可显示 Verified\n"
            "（密钥须已添加到 GitHub → Settings → SSH and GPG keys → Signing keys）"
        )

    return (
        "[提示] 未检测到提交签名；推送后 commit/tag 可能无 Verified 标记。\n"
        "  配置示例（SSH 签名）：\n"
        "    git config --global gpg.format ssh\n"
        "    git config --global user.signingkey <你的 SSH 公钥路径>\n"
        "    git config --global commit.gpgsign true\n"
        "  然后将你的 SSH 公钥添加到 GitHub → Settings → SSH and GPG keys → Signing keys"
    )


def _ask_bump_kind(*, minor_flag: bool, no_bump: bool) -> str | None:
    """交互询问或根据 flags 确定版本升级类型。"""
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


def _rel_repo_path(path: Path | str) -> str:
    p = Path(path)
    if p.is_absolute():
        return os.path.relpath(p, _repo_root()).replace("\\", "/")
    return p.as_posix()


def _stage_upload_changes(change_paths: list[str], version_path: Path) -> None:
    """只暂存本次上传相关路径，避免 git add . 把无关改动一并提交。"""
    paths: list[str] = []
    seen: set[str] = set()
    for raw in change_paths:
        rel = _rel_repo_path(raw)
        if rel and rel not in seen:
            seen.add(rel)
            paths.append(rel)
    version_rel = _rel_repo_path(version_path)
    if version_rel not in seen:
        paths.append(version_rel)
    if not paths:
        print("[错误] 无有效暂存路径")
        sys.exit(1)
    print(f"[信息] git add（{len(paths)} 个路径，非全仓库）")
    run_git(["add", "--", *paths])


def _pre_commit_installed() -> bool:
    return os.path.isfile(os.path.join(_repo_root(), ".git", "hooks", "pre-commit"))


def _staged_file_list() -> list[str]:
    _, out, _ = run_git(["diff", "--cached", "--name-only"], check=False, capture_output=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def _run_pre_commit_on_staged(*, rounds: int = 2) -> bool:
    """运行 pre-commit；若钩子自动改文件则 re-add 后最多重试 rounds 次。"""
    if not _pre_commit_installed():
        return True
    for attempt in range(1, rounds + 1):
        files = _staged_file_list()
        if not files:
            return True
        print(f"[信息] pre-commit 检查（第 {attempt}/{rounds} 轮，{len(files)} 个文件）…")
        proc = subprocess.run(
            ["pre-commit", "run", "--files", *files],
            cwd=_repo_root(),
            check=False,
        )
        if proc.returncode == 0:
            return True
        run_git(["add", "--", *files], check=False)
    print("[错误] pre-commit 未通过，commit 已取消")
    print("[提示] 本地执行: pre-commit run --files <路径> → 修复 ruff 等问题 → git add → 再跑上传脚本 --no-bump")
    return False


def _commit_with_message(message: str) -> None:
    """使用指定消息执行 git commit。"""
    cfg = resolve_signing_config()
    extra = commit_extra_args(cfg)
    msg_path = os.path.join(_repo_root(), ".git-upload-msg.txt")

    with open(msg_path, "w", encoding="utf-8") as f:
        f.write(message)

        f.write("\n")

    try:
        run_git(["commit", *extra, "-F", msg_path])

    except subprocess.CalledProcessError as exc:
        print("[错误] git commit 失败（常见原因：pre-commit / ruff 未通过）")
        if _pre_commit_installed():
            print("[提示] 查看上方 pre-commit 输出；修复后 git add 再执行 python github_upload_module.py --no-bump")
        raise exc

    finally:
        if os.path.isfile(msg_path):
            os.remove(msg_path)


def _push_to_remote() -> bool:
    """将当前分支推送到 origin。"""
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

        print("[信息] 推送失败，尝试 fetch → pull --rebase 后重试")

        _fetch_origin_main()
        _, behind = _count_ahead_behind()
        if behind == 0:
            raise
        if not _stash_dirty_worktree():
            raise
        run_git(["pull", "--rebase", "origin", DEFAULT_BRANCH], timeout=300)
        _pop_stash_if_needed(True, pull_ok=True)

        run_git(push_args, timeout=300)

        print("[成功] 推送完成")

        return True


def _push_tag(version: str) -> bool:
    """创建并推送 git 标签。"""
    tag = f"v{version}"
    _, existing_tags, _ = run_git(["tag", "-l", tag], capture_output=True)

    if tag in existing_tags.strip().split("\n"):
        print(f"[信息] 标签 {tag} 已存在，跳过创建")

    else:
        print(f"[信息] 创建标签 {tag}")

        cfg = resolve_signing_config()

        tag_args = ["tag", "-a", tag, "-m", f"Release {tag}"]

        tag_args.extend(tag_extra_args(cfg))

        run_git(tag_args)

    print(f"[信息] 推送标签 {tag} ...")

    run_git(["push", "origin", tag], timeout=120)

    print(f"[信息] 标签 {tag} 已推送，GitHub Actions 将自动构建发布版")

    return True


def _maybe_backup_git_for_minor(*, current_version: str, skip: bool) -> None:
    """Minor 上传前备份 .git；失败则中止。"""
    if skip:
        print("[信息] 已跳过 .git 备份（--no-git-backup）")
        return
    try:
        from scripts.tools import git_backup

        dest = git_backup.backup_git_dir(
            Path(_repo_root()),
            current_version=current_version,
            bump_kind="minor",
        )
        rel = dest.relative_to(_repo_root())
        print(f"[信息] Minor 上传前已备份 .git → {rel}")
        print(f"[信息] 说明与恢复步骤见 {git_backup.GIT_BACKUP_ROOT}/README.md")
    except Exception as exc:
        print(f"[错误] .git 备份失败: {exc}")
        print("[中止] Minor 上传须先成功备份；若磁盘不足可用 --no-git-backup（不推荐）")
        sys.exit(1)


def commit_and_push(
    *,
    minor: bool = False,
    no_bump: bool = False,
    push_tag: bool = False,
    skip_git_backup: bool = False,
) -> None:
    """执行 git 提交与推送流程（含版本管理和总结块管理）。"""
    os.chdir(_repo_root())
    target_path = os.path.join(".", TARGET_DIR)

    if not os.path.isdir(target_path):
        print(f"[错误] 目录不存在: {TARGET_DIR}")

        sys.exit(1)

    if not any(os.scandir(target_path)):
        print(f"[错误] 目录为空: {TARGET_DIR}")

        sys.exit(1)

    meta = _import_upload_meta()

    readme_path = meta.please_read_me_path()

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
                _maybe_backup_git_for_minor(
                    current_version=current,
                    skip=skip_git_backup,
                )

                version_for_msg = meta.bump_minor(current)

                print(f"[信息] 版本 minor: {current} → {version_for_msg}")

            else:
                version_for_msg = meta.bump_patch(current)

                print(f"[信息] 版本 patch: {current} → {version_for_msg}")

            meta.write_version(readme_path, version_for_msg)

        title, bullets = meta.summarize_changes(change_paths)

        meta.write_summary_block(readme_path, title, bullets)

        print(f"[信息] 已写入上传总结至 {readme_path.name} 底部")

        _stage_upload_changes(change_paths, readme_path)

        if not _run_pre_commit_on_staged():
            sys.exit(1)

        title_read, bullets_read = meta.read_summary_for_commit(readme_path)

        commit_msg = meta.build_commit_message(version_for_msg, title_read, bullets_read)

        print(signing_status_message(resolve_signing_config()))

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

        print(
            f"[信息] 当前 _VERSION = {meta.read_version(readme_path)}"
            f"（_EXE_VERSION = {meta.read_exe_version(readme_path)}）"
        )

    if push_succeeded and push_tag:
        version = meta.read_exe_version(readme_path)

        _push_tag(version)


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
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

    parser.add_argument(
        "--tag",
        action="store_true",
        help="推送 git 标签（v{version}），触发 GitHub Actions 构建并发布 Verified 发行版",
    )

    parser.add_argument(
        "--skip-pull",
        action="store_true",
        help="跳过远程拉取，直接提交并推送",
    )

    parser.add_argument(
        "--force-push",
        action="store_true",
        help="使用 --force-with-lease 推送（覆盖远程历史，用于修复损坏提交后重推）",
    )

    parser.add_argument(
        "--no-git-backup",
        action="store_true",
        help="Minor 上传时不备份 .git 到 git_backup/snapshots/（不推荐）",
    )

    return parser.parse_args()


def main() -> None:
    """CLI 入口。执行完整的 Git 提交与推送流程。"""
    global FORCE_PUSH

    args = parse_args()

    if args.minor and args.no_bump:
        print("[错误] --minor 与 --no-bump 不能同时使用")

        sys.exit(1)

    if args.force_push:
        FORCE_PUSH = True

    print("=" * 60)

    print("GitHub 上传脚本（SSH）")

    print("=" * 60)

    try:
        setup_git_repo()

        if not sync_with_remote(skip_pull=args.skip_pull):
            print("[中止] 同步远程失败，未推送")

            sys.exit(1)

        commit_and_push(
            minor=args.minor,
            no_bump=args.no_bump,
            push_tag=args.tag,
            skip_git_backup=args.no_git_backup,
        )

        print("=" * 60)

        print("[完成]")

        print("=" * 60)

    except Exception as exc:
        print(f"\n[错误] {exc}")

        sys.exit(1)


if __name__ == "__main__":
    main()
