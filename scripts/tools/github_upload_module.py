#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Push this repo to GitHub over SSH and bump scripts/_version.py when needed."""

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

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# ===== 配置区 =====

DEFAULT_REMOTE_SSH = "git@github.com:wxhwwla/calc-framework.git"
AUTH_MODE = "ssh"
REMOTE_HTTPS = "https://github.com/wxhwwla/calc-framework.git"

KEY_FILE = "git_key.txt"


TARGET_DIR = "games/endfield"

WORK_BRANCH = "develop"
RELEASE_BRANCH = "main"
DEFAULT_BRANCH = WORK_BRANCH

SKIP_PULL = False

FORCE_PUSH = False

# =================


_TOKEN_IN_REMOTE = re.compile(
    r"https://[^@\s]+@github\.com/",
    re.IGNORECASE,
)


def _import_upload_meta():
    """动态导入 upload_meta 模块。"""
    from scripts._path_setup import ensure_root

    ensure_root()
    from scripts._version import ensure_summary_marker_assignments, please_read_me_path

    if ensure_summary_marker_assignments(please_read_me_path()):
        print("[信息] 已修复 _version.py 内 SUMMARY_BEGIN/SUMMARY_END 常量")
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


def _git_dir() -> Path:
    return Path(_repo_root()) / ".git"


def _is_rebase_in_progress() -> bool:
    git_dir = _git_dir()
    return (git_dir / "rebase-merge").is_dir() or (git_dir / "rebase-apply").is_dir()


def _is_merge_in_progress() -> bool:
    return (_git_dir() / "MERGE_HEAD").is_file()


def preflight_upload(*, check_only: bool = False) -> bool:
    """上传前自检；check_only 时通过则打印提示并返回 True。"""
    root = _repo_root()
    if not os.path.isdir(os.path.join(root, ".git")):
        print("[错误] 未找到 .git 目录")
        return False
    if _is_rebase_in_progress():
        print("[错误] rebase 进行中，请先 git rebase --continue 或 --abort")
        return False
    if _is_merge_in_progress():
        print("[错误] merge 进行中，请先完成或 abort merge")
        return False

    ref = _remote_branch_ref()
    code, _, _ = run_git(["rev-parse", "--verify", ref], check=False, capture_output=True)
    if code != 0:
        if check_only:
            print(f"[信息] 远程尚无 origin/{WORK_BRANCH}，可首次推送")
        return True

    code, merge_base, _ = run_git(
        ["merge-base", "HEAD", ref],
        check=False,
        capture_output=True,
    )
    if code != 0 or not merge_base.strip():
        print(f"[错误] 本地与 origin/{WORK_BRANCH} 无共同祖先（断历史），需人工 reconcile")
        return False

    if check_only:
        print("[信息] 自检通过，可以上传")
    return True


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

    if current_branch != WORK_BRANCH:
        print(f"[信息] 当前分支「{current_branch}」，切换到 {WORK_BRANCH}")

        code, _, _ = run_git(["checkout", WORK_BRANCH], check=False, capture_output=True)

        if code != 0:
            # 检查 develop 是否已存在本地
            _, branches, _ = run_git(["branch"], capture_output=True)
            if WORK_BRANCH in branches:
                # 已存在但切换失败 → 本地有未提交改动
                print(f"[错误] 本地有未提交的改动，无法自动切换到 {WORK_BRANCH}")
                print(
                    f"[提示] 请手动处理：git stash --include-untracked && git checkout {WORK_BRANCH} && git stash pop"
                )
                print(f"[提示] 或直接在 {WORK_BRANCH} 分支上运行本脚本（推荐）")
                sys.exit(1)
            # 分支不存在 → 从 main 创建
            code, _, _ = run_git(
                ["checkout", "-b", WORK_BRANCH, f"origin/{RELEASE_BRANCH}"],
                check=False,
                capture_output=True,
            )
            if code != 0:
                run_git(["checkout", "-b", WORK_BRANCH])
            print(f"[信息] 已创建本地分支 {WORK_BRANCH}")

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
    return f"origin/{WORK_BRANCH}"


def _remote_release_ref() -> str:
    return f"origin/{RELEASE_BRANCH}"


def _fetch_origin_work(*, timeout: int = 300) -> None:
    run_git(["fetch", "origin", WORK_BRANCH], check=False, timeout=timeout)


def _fetch_origin_release(*, timeout: int = 300) -> None:
    run_git(["fetch", "origin", RELEASE_BRANCH], check=False, timeout=timeout)


def _fetch_all_origin_branches(*, timeout: int = 300) -> None:
    run_git(
        ["fetch", "origin", WORK_BRANCH, RELEASE_BRANCH],
        check=False,
        timeout=timeout,
    )


def _fetch_origin_main(*, timeout: int = 300) -> None:
    _fetch_origin_work(timeout=timeout)


def _count_ahead_behind() -> tuple[int, int]:
    """返回 (领先 origin/develop 的 commit 数, 落后数)。"""
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
        print(f"[信息] 已与 origin/{WORK_BRANCH} 同步（领先 {ahead} commit），跳过 pull")
        return True

    print(f"[信息] 落后 origin/{WORK_BRANCH} {behind} 个 commit，执行 pull --rebase...")

    code, stdout, _ = run_git(["rev-list", "--count", "--all"], check=False, capture_output=True)
    has_commits = int(stdout.strip()) > 0 if code == 0 and stdout.strip() else False
    if not has_commits:
        print("[信息] 本地无提交，跳过 pull")
        return True

    stashed = _stash_dirty_worktree()
    if not stashed:
        return False

    code, _, stderr = run_git(
        ["pull", "--rebase", "origin", WORK_BRANCH],
        check=False,
        capture_output=False,
        timeout=300,
    )
    pull_ok = code == 0
    if not pull_ok:
        _code2, heads, _ = run_git(
            ["ls-remote", "--heads", "origin", WORK_BRANCH],
            check=False,
            capture_output=True,
        )
        if not heads.strip():
            print(f"[信息] 远程尚无 {WORK_BRANCH} 分支，将首次推送")
            pull_ok = True
        else:
            print(f"[警告] 拉取失败: {stderr.strip()}")

    _pop_stash_if_needed(stashed, pull_ok=pull_ok)
    return pull_ok


def _unquote_git_path(raw: str) -> str:
    """解析 git status 中带 C 风格转义的双引号路径。"""
    text = raw.strip()
    if not (text.startswith('"') and text.endswith('"')):
        return text
    inner = text[1:-1]
    out = bytearray()
    i = 0
    while i < len(inner):
        ch = inner[i]
        if ch != "\\":
            out.extend(ch.encode("utf-8"))
            i += 1
            continue
        i += 1
        if i >= len(inner):
            break
        esc = inner[i]
        if esc in ('"', "\\"):
            out.extend(esc.encode("utf-8"))
            i += 1
        elif esc == "n":
            out.extend(b"\n")
            i += 1
        elif esc == "t":
            out.extend(b"\t")
            i += 1
        elif esc.isdigit():
            j = i
            while j < len(inner) and j < i + 3 and inner[j].isdigit():
                j += 1
            out.append(int(inner[i:j], 8))
            i = j
        else:
            out.extend(esc.encode("utf-8"))
            i += 1
    return out.decode("utf-8")


def _normalize_change_path(raw: str) -> str:
    """将 git 输出路径规范为仓库内 POSIX 相对路径（勿对转义路径用 Path）。"""
    path = _unquote_git_path(raw.strip())
    if not path:
        return ""
    path = path.replace("\\", "/")
    root = _repo_root().replace("\\", "/")
    if os.path.isabs(path) or (len(path) > 1 and path[1] == ":"):
        try:
            return os.path.relpath(path, root).replace("\\", "/")
        except ValueError:
            return path
    return path


def _porcelain_paths(porcelain: str) -> list[str]:
    """从 git status --porcelain 输出中提取文件路径列表。
    跳过已删除（D）条目——这些已被 git rm --cached 从索引移除，不应重新 add。
    """
    paths: list[str] = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue

        # XY status: X=staging, Y=working tree. 跳过 D (已删除)
        if line[0] == "D" or line[0:2] in (" D", "DD"):
            continue

        rest = line[3:].strip()

        if " -> " in rest:
            rest = rest.split(" -> ")[-1].strip()

        normalized = _normalize_change_path(rest)
        if normalized:
            paths.append(normalized)

    return paths


def _collect_change_paths() -> list[str]:
    """收集所有已变更文件的路径（排除已删除条目）。"""
    path_git = ["-c", "core.quotepath=false"]
    _, porcelain, _ = run_git([*path_git, "status", "--porcelain"], capture_output=True)
    paths = _porcelain_paths(porcelain)
    # diff --diff-filter=d 排除已从索引删除的文件
    for diff_cmd in (
        ["diff", "--diff-filter=d", "--name-only"],
        ["diff", "--cached", "--diff-filter=d", "--name-only"],
    ):
        _, out, _ = run_git([*path_git, *diff_cmd], check=False, capture_output=True)
        for line in out.splitlines():
            normalized = _normalize_change_path(line)
            if normalized:
                paths.append(normalized)

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
    if isinstance(path, Path):
        p = path
        if p.is_absolute():
            return os.path.relpath(p, _repo_root()).replace("\\", "/")
        return p.as_posix()
    return _normalize_change_path(str(path))


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
    print(f"[信息] git add（{len(paths)} 个路径，非全仓库，分批进行）")
    # 过滤已删除的文件（git add 不存在的文件会报错）
    paths = [p for p in paths if os.path.exists(os.path.join(_repo_root(), p))]
    if not paths:
        print("[错误] 全部路径对应的文件已不存在（可能已被删除）")
        sys.exit(1)
    # 分批 add 避免 Windows 命令行长度限制（CreateProcess 上限 ~8191 字符）
    batch_size = 50
    for i in range(0, len(paths), batch_size):
        batch = paths[i : i + batch_size]
        run_git(["add", "--", *batch])
    print(f"[信息] git add 完成（{len(paths)} 个路径，共 {(len(paths) + batch_size - 1) // batch_size} 批）")


def _pre_commit_installed() -> bool:
    return os.path.isfile(os.path.join(_repo_root(), ".git", "hooks", "pre-commit"))


def _staged_file_list() -> list[str]:
    _, out, _ = run_git(
        ["-c", "core.quotepath=false", "diff", "--cached", "--name-only"],
        check=False,
        capture_output=True,
    )
    paths: list[str] = []
    for line in out.splitlines():
        normalized = _normalize_change_path(line)
        if normalized:
            paths.append(normalized)
    return paths


def _unstaged_modified_paths() -> list[str]:
    """返回工作区有改动但未进入 index 的路径（commit hook stash 冲突源）。"""
    _, porcelain, _ = run_git(
        ["-c", "core.quotepath=false", "status", "--porcelain"],
        check=False,
        capture_output=True,
    )
    paths: list[str] = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        if line[0] == " " and line[1] not in (" ", "?"):
            normalized = _normalize_change_path(line[3:])
            if normalized:
                paths.append(normalized)
    return paths


def _refresh_staging_for_commit(change_paths: list[str], version_path: Path) -> None:
    """commit 前重新 git add，消除 index/工作区不一致，避免 commit hook stash 冲突。"""
    merged: list[str] = []
    seen: set[str] = set()
    for raw in (*change_paths, *_collect_change_paths()):
        rel = _rel_repo_path(raw)
        if rel and rel not in seen:
            seen.add(rel)
            merged.append(rel)
    version_rel = _rel_repo_path(version_path)
    if version_rel not in seen:
        merged.append(version_rel)
    unstaged = _unstaged_modified_paths()
    added = 0
    for path in unstaged:
        if path not in seen:
            seen.add(path)
            merged.append(path)
            added += 1
    if added:
        print(f"[信息] 补暂存 {added} 个工作区改动（避免 commit hook stash 冲突）")
    print(f"[信息] git add（{len(merged)} 个路径，commit 前同步）")
    # 过滤已删除的文件（git add 不存在的文件会报错）
    merged = [p for p in merged if os.path.exists(os.path.join(_repo_root(), p))]
    if not merged:
        print("[信息] 无有效文件需暂存，跳过 git add")
        return
    batch_size = 50
    for i in range(0, len(merged), batch_size):
        batch = merged[i : i + batch_size]
        run_git(["add", "--", *batch])
    print(f"[信息] commit 前同步完成（{len(merged)} 个路径，共 {(len(merged) + batch_size - 1) // batch_size} 批）")


def _pre_commit_has_lint_errors(output: str) -> bool:
    lint_failed = False
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("ruff-lint") and "Failed" in stripped:
            lint_failed = True
            break
    if not lint_failed:
        return False
    # ruff --fix --exit-non-zero-on-fix：已全部自动修正时仍 Failed，应 re-add 重试
    if re.search(r"\(\d+ fixed, 0 remaining\)", output):
        return False
    return not re.search(r"Found \d+ errors? .*0 remaining", output)


def _run_pre_commit_on_staged(*, rounds: int = 2) -> bool:
    """运行 pre-commit；若钩子自动改文件则 re-add 后最多重试 rounds 次。"""
    if not _pre_commit_installed():
        return True
    print(
        f"[信息] pre-commit 最多 {rounds} 轮；"
        "仅 ruff-format / mixed-line-ending / ruff-lint 自动修正时第 1 轮 Failed 属正常；"
        "ruff-lint Failed 且仍有 remaining 为代码错误，不会靠重试解决"
    )
    for attempt in range(1, rounds + 1):
        files = _staged_file_list()
        if not files:
            return True
        print(f"[信息] pre-commit 检查（第 {attempt}/{rounds} 轮，{len(files)} 个文件）…")
        proc = subprocess.run(
            ["pre-commit", "run", "--files", *files],
            cwd=_repo_root(),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.stdout:
            print(proc.stdout, end="")
        if proc.stderr:
            print(proc.stderr, end="", file=sys.stderr)
        if proc.returncode == 0:
            if attempt > 1:
                print(f"[信息] pre-commit 第 {attempt} 轮已通过")
            return True
        if _pre_commit_has_lint_errors(output):
            print("[错误] ruff-lint 未通过（代码问题，非 format/换行），请按上方报错修复")
            return False
        if attempt < rounds:
            print(
                f"[信息] pre-commit 第 {attempt} 轮：钩子已自动修正格式/换行，已重新 git add，继续第 {attempt + 1} 轮…"
            )
        if files:
            run_git(["add", "--", *files], check=False)
    print("[错误] pre-commit 未通过，commit 已取消")
    print("[提示] 修复 ruff 等问题后重新运行 python github_upload_module.py（无需 --no-bump）")
    return False


def _version_file_relpath(readme_path: Path) -> str:
    """返回 _version.py 相对仓库根的路径（POSIX）。"""
    return readme_path.relative_to(_repo_root()).as_posix()


def _read_version_from_git_head(readme_path: Path) -> str | None:
    """从 HEAD 读取已提交的 _VERSION；无 commit 或文件不存在时返回 None。"""
    from scripts._version import _VERSION_PATTERN

    code, out, _ = run_git(
        ["show", f"HEAD:{_version_file_relpath(readme_path)}"],
        check=False,
        capture_output=True,
    )
    if code != 0 or not out.strip():
        return None
    match = _VERSION_PATTERN.search(out)
    return match.group(2) if match else None


def _sync_saved_version_with_head(readme_path: Path, meta) -> str:
    """回滚/bump 基准以 HEAD 为准，修正上次上传失败留在工作区的版本号。"""
    saved_version = meta.read_version(readme_path)
    head_version = _read_version_from_git_head(readme_path)
    if head_version and saved_version != head_version:
        print(f"[信息] 校正 _VERSION：工作区 {saved_version} → HEAD {head_version}（上次上传失败残留）")
        meta.write_version(readme_path, head_version)
        return head_version
    return saved_version


def _should_merge_to_release(*, was_minor: bool) -> bool:
    """次版本号上传时自动同步 develop → main。"""
    if not was_minor:
        print(f"[信息] 非次版本上传，仅推送 {WORK_BRANCH}")
        return False
    release_ref = _remote_release_ref()
    code, _, _ = run_git(["rev-parse", "--verify", release_ref], check=False, capture_output=True)
    if code != 0:
        print(f"[信息] 远程尚无 {RELEASE_BRANCH}，跳过合并")
        return False
    print(f"[信息] 次版本上传 → 合并 {WORK_BRANCH} → {RELEASE_BRANCH}")
    return True


def _merge_work_into_release(*, meta, readme_path: Path, push_tag: bool) -> None:
    """将 develop 合并进 main 并推送；可选打 release 标签。"""
    _, saved_out, _ = run_git(["branch", "--show-current"], capture_output=True)
    saved_branch = saved_out.strip()
    try:
        _fetch_all_origin_branches()
        code, _, _ = run_git(["checkout", RELEASE_BRANCH], check=False, capture_output=True)
        if code != 0:
            _, branches, _ = run_git(["branch"], capture_output=True)
            if RELEASE_BRANCH in branches:
                print(f"[错误] 无法切换到 {RELEASE_BRANCH}，合并取消")
                return
            run_git(["checkout", "-b", RELEASE_BRANCH, _remote_release_ref()])
        run_git(["pull", "--rebase", "origin", RELEASE_BRANCH], timeout=300)
        run_git(
            [
                "merge",
                "--no-ff",
                WORK_BRANCH,
                "-m",
                f"release: merge {WORK_BRANCH} into {RELEASE_BRANCH}",
            ],
            timeout=120,
        )
        run_git(["push", "origin", RELEASE_BRANCH], timeout=300)
        print(f"[成功] 已合并 {WORK_BRANCH} → {RELEASE_BRANCH} 并推送")
        if push_tag:
            _push_tag(meta.read_exe_version(readme_path))
    finally:
        if saved_branch:
            run_git(["checkout", saved_branch], check=False)


def _rollback_upload_draft(
    readme_path,
    meta,
    *,
    saved_version: str,
    restore_version: bool,
) -> None:
    """上传在 commit 前失败时撤销总结块与（可选）已写入的版本号。"""
    meta.remove_summary_block(readme_path)
    if restore_version:
        meta.write_version(readme_path, saved_version)
        print(f"[信息] 已回滚 _VERSION → {saved_version}")
    print("[信息] 已移除 _version.py 底部 UPLOAD_SUMMARY 块")


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
            print("[提示] 若有 Unstaged files / Stashed changes conflicted：确认 docs 等已保存后重新运行上传脚本")
        raise exc

    finally:
        if os.path.isfile(msg_path):
            os.remove(msg_path)


def _push_to_remote() -> bool:
    """将 develop 推送到 origin；远程无 develop 时使用 -u。"""
    remote_ref = _remote_branch_ref()
    code, _, _ = run_git(["rev-parse", "--verify", remote_ref], check=False, capture_output=True)
    push_args = ["push", "origin", WORK_BRANCH]
    if code != 0:
        push_args = ["push", "-u", "origin", WORK_BRANCH]
        print(f"[信息] 首次推送 {WORK_BRANCH} 分支")
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
        run_git(["pull", "--rebase", "origin", WORK_BRANCH], timeout=300)
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
    dry_run: bool = False,
) -> None:
    """执行 git 提交与推送流程（含版本管理和总结块管理）。

    参数:
        dry_run: 预览模式，展示操作计划但不实际修改或推送。
    """
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
        ["ls-remote", "--heads", "origin", WORK_BRANCH],
        check=False,
        capture_output=True,
    )

    remote_exists = bool(remote_heads.strip())

    has_unpushed = False

    if remote_exists:
        code, ahead, _ = run_git(
            ["rev-list", "--count", f"origin/{WORK_BRANCH}..{WORK_BRANCH}"],
            check=False,
            capture_output=True,
        )

        if code == 0 and ahead.strip().isdigit():
            has_unpushed = int(ahead.strip()) > 0

            if has_unpushed:
                print(f"[信息] 已有 {ahead.strip()} 个提交未推送（不 bump 版本）")

    created_commit = False
    was_minor = False  # 是否次版本上传（用于合并到 main）

    push_succeeded = False

    # 必须在分支外初始化，否则补推 (has_unpushed) 时变量不存在
    saved_version = ""
    version_planned_bump = False

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

        saved_version = _sync_saved_version_with_head(readme_path, meta)
        version_for_msg = saved_version
        version_planned_bump = False

        if business and not no_bump:
            kind = _ask_bump_kind(minor_flag=minor, no_bump=False)

            if kind == "minor":
                was_minor = True
                _maybe_backup_git_for_minor(
                    current_version=saved_version,
                    skip=skip_git_backup,
                )

                version_for_msg = meta.bump_minor(saved_version)

                print(f"[信息] 版本 minor: {saved_version} → {version_for_msg}（pre-commit 通过后再写入 _version.py）")

            else:
                version_for_msg = meta.bump_patch(saved_version)

                print(f"[信息] 版本 patch: {saved_version} → {version_for_msg}（pre-commit 通过后再写入 _version.py）")

            version_planned_bump = True

        # ============ DryRun 预览模式 ============
        if dry_run:
            print("")
            print("=" * 60)
            print("  [DryRun] 预览模式 — 不修改任何文件，不推送")
            print("=" * 60)
            print(f"  当前版本:     {saved_version}")
            if version_planned_bump:
                print(f"  目标版本:     {version_for_msg}")
                print(f"  递增类型:     {'Minor' if was_minor else 'Patch'}")
            else:
                print("  版本递增:     跳过")
            print(f"  分支:         {WORK_BRANCH}")
            print(f"  目标目录:     {TARGET_DIR}")
            print(f"  变更文件:     {len(change_paths)} 个")
            for p in sorted(change_paths):
                print(f"    - {p}")
            if was_minor:
                print(f"  Minor 操作:   合并 {WORK_BRANCH} → {RELEASE_BRANCH}")
            if push_tag:
                print(f"  标签:         v{version_for_msg if version_planned_bump else saved_version}")
            print("=" * 60)
            print("  [DryRun] 完成 — 实际执行请去掉 --dry-run")
            print("=" * 60)
            return

        title, bullets = meta.summarize_changes(change_paths)

        meta.write_summary_block(readme_path, title, bullets)

        print(f"[信息] 已写入上传总结至 {readme_path.name} 底部")

        from scripts._version import ensure_summary_marker_assignments

        if ensure_summary_marker_assignments(readme_path):
            print("[信息] 已修复 _version.py 内 SUMMARY_BEGIN/SUMMARY_END 常量")

        _stage_upload_changes(change_paths, readme_path)

        if not _run_pre_commit_on_staged():
            _rollback_upload_draft(
                readme_path,
                meta,
                saved_version=saved_version,
                restore_version=False,
            )
            sys.exit(1)

        if version_planned_bump:
            meta.write_version(readme_path, version_for_msg)

        _refresh_staging_for_commit(change_paths, readme_path)

        print("[信息] commit 前 pre-commit（含版本号写入 / 未暂存改动同步后）…")
        if not _run_pre_commit_on_staged():
            _rollback_upload_draft(
                readme_path,
                meta,
                saved_version=saved_version,
                restore_version=version_planned_bump,
            )
            sys.exit(1)

        title_read, bullets_read = meta.read_summary_for_commit(readme_path)

        commit_msg = meta.build_commit_message(version_for_msg, title_read, bullets_read)

        # 摘要已读入 commit 消息，从磁盘删除并重新暂存以免进入仓库历史
        meta.remove_summary_block(readme_path)
        print(f"[信息] 已删除 {readme_path.name} 底部 UPLOAD_SUMMARY 块")
        run_git(["add", _version_file_relpath(readme_path)])

        # 删块后可能触发换行符修正，再跑一轮 pre-commit
        print("[信息] 删块后 pre-commit（修换行符）…")
        if not _run_pre_commit_on_staged(rounds=2):
            _rollback_upload_draft(
                readme_path,
                meta,
                saved_version=saved_version,
                restore_version=version_planned_bump,
            )
            sys.exit(1)

        print(signing_status_message(resolve_signing_config()))

        print(f"[信息] git commit:\n{commit_msg.splitlines()[0]} ...")

        try:
            _commit_with_message(commit_msg)
        except subprocess.CalledProcessError:
            _rollback_upload_draft(
                readme_path,
                meta,
                saved_version=saved_version,
                restore_version=version_planned_bump,
            )
            sys.exit(1)

        created_commit = True

    else:
        # 补推已有 commit：从 HEAD 读取版本号，若末尾 .0 则为次版本 bump，应合并并打标签
        head_version = _read_version_from_git_head(readme_path)
        if head_version and re.match(r"^\d+\.\d+\.0$", head_version):
            was_minor = True
            print(f"[信息] 检测到 HEAD 次版本 {head_version}，补推后自动合并 {RELEASE_BRANCH}")
        print("[信息] 跳过新版本 commit，仅推送已有提交")

    try:
        push_succeeded = _push_to_remote()

    except subprocess.CalledProcessError:
        push_succeeded = False

        # 推送失败：回滚已写入的版本号（如果版本被递增了）
        if version_planned_bump and created_commit:
            print("[信息] 推送失败，回滚 _VERSION 到推送前状态…")
            meta.write_version(readme_path, saved_version)
            print(f"[信息] 已回滚 _VERSION → {saved_version}")
            print("[信息] 版本号已恢复到推送前值，修复后可重新运行上传脚本")

        print("[警告] 推送未成功；本地 commit 已保留，修复后请 python github_upload_module.py --no-bump 仅补推")

        raise

    if push_succeeded:
        try:
            if _should_merge_to_release(was_minor=was_minor):
                _merge_work_into_release(
                    meta=meta,
                    readme_path=readme_path,
                    push_tag=push_tag,
                )
            elif push_tag:
                print("[信息] --tag 已跳过：仅次版本上传时合并并打标签，请使用 --minor 或输入 M")
        except subprocess.CalledProcessError:
            print(f"[警告] {WORK_BRANCH} 已推送，但合并 {RELEASE_BRANCH} 失败，请人工处理 merge")
            raise

    if push_succeeded and created_commit:
        print(
            f"[信息] 当前 _VERSION = {meta.read_version(readme_path)}"
            f"（_EXE_VERSION = {meta.read_exe_version(readme_path)}）"
        )


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
        help="本次不递增 _VERSION（已有未推送 commit 或显式跳过 bump 时使用）",
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

    parser.add_argument(
        "--check",
        action="store_true",
        help="仅自检仓库状态，不 pull/commit/push",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式：展示将要执行的操作，不实际修改任何文件或推送",
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

        if not preflight_upload(check_only=args.check):
            sys.exit(1)

        if args.check:
            sys.exit(0)

        # DryRun: 跳过 sync_with_remote（仅展示本地状态）
        if not args.dry_run:
            if not sync_with_remote(skip_pull=args.skip_pull):
                print("[中止] 同步远程失败，未推送")

                sys.exit(1)

        commit_and_push(
            minor=args.minor,
            no_bump=args.no_bump,
            push_tag=args.tag,
            skip_git_backup=args.no_git_backup,
            dry_run=args.dry_run,
        )

        print("=" * 60)

        print("[完成]")

        print("=" * 60)

    except Exception as exc:
        print(f"\n[错误] {exc}")

        sys.exit(1)


if __name__ == "__main__":
    main()
