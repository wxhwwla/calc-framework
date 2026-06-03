#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""
项目版本号与上传元数据 — 版本信息唯一源头。

此文件是 `_VERSION` 和 `_EXE_VERSION` 的唯一定义处。
`scripts/please_read_me.py` / `upload_meta.py` / `version.py` 均从此模块导入。
"""

from __future__ import annotations

import re
from pathlib import Path

# ==================== 版本常量（唯一源头） ====================

_VERSION = "3.20.5"
"""项目与 pip 包版本（pyproject.toml 通过 dynamic 读取）。

上传脚本在有「业务改动」并 push 成功时自动递增（默认第三位 +1）。
第一位 MAJOR 永远只在下方手动修改，脚本不会动。"""

_EXE_VERSION = "0.6.0-beta"
"""窗口标题与 dist/*.exe 用户可见版本。

仅手动修改；改后须重新打包（main_build.py）。"""

# ==============================================================

SUMMARY_BEGIN = ""

_VERSION_PATTERN = re.compile(
    r'^(_VERSION\s*=\s*["\'])([^"\']+)(["\'])',
    re.MULTILINE,
)

_EXE_VERSION_PATTERN = re.compile(
    r'^(_EXE_VERSION\s*=\s*["\'])([^"\']+)(["\'])',
    re.MULTILINE,
)

__all__ = [
    "_EXE_VERSION",
    "_EXE_VERSION_PATTERN",
    "_VERSION",
    "_VERSION_PATTERN",
    "SUMMARY_BEGIN",
    "SUMMARY_END",
    "build_commit_message",
    "bump_minor",
    "bump_patch",
    "classify_changed_paths",
    "format_semver",
    "get_exe_version",
    "get_version",
    "parse_semver",
    "please_read_me_path",
    "read_exe_version",
    "read_summary_for_commit",
    "read_version",
    "remove_summary_block",
    "strip_summary_block",
    "summarize_changes",
    "write_summary_block",
    "write_version",
]


def please_read_me_path(repo_root: Path | None = None) -> Path:
    """返回 _version.py 的路径（版本唯一源头）。

    历史说明：旧名为 `please_read_me_path`，因版本常量原在
    `please_read_me.py` 中。现常量已迁移到此文件，但函数名
    保留以保持调用兼容。
    """
    root = repo_root or Path(__file__).resolve().parent
    return root / "_version.py"


def parse_semver(version: str) -> tuple[int, int, int]:
    """解析语义化版本字符串为三元组。"""
    parts = version.strip().split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"无效语义化版本: {version!r}（需要 MAJOR.MINOR.PATCH）")
    return int(parts[0]), int(parts[1]), int(parts[2])


def format_semver(major: int, minor: int, patch: int) -> str:
    """将整数三元组格式化为语义化版本字符串。"""
    return f"{major}.{minor}.{patch}"


def read_version(path: Path | None = None) -> str:
    """从 _version.py 读取 _VERSION。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    match = _VERSION_PATTERN.search(text)
    if not match:
        raise ValueError(f"未在 {path} 中找到 _VERSION")
    return match.group(2)


def read_exe_version(path: Path | None = None) -> str:
    """从 _version.py 读取 _EXE_VERSION。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    match = _EXE_VERSION_PATTERN.search(text)
    if not match:
        raise ValueError(f"未在 {path} 中找到 _EXE_VERSION")
    return match.group(2)


def write_version(path: Path | None, new_version: str) -> None:
    """将新版本号写入 _version.py 的 _VERSION。"""
    path = path or please_read_me_path()
    text = path.read_text(encoding="utf-8")
    if not _VERSION_PATTERN.search(text):
        raise ValueError(f"未在 {path} 中找到 _VERSION")
    updated = _VERSION_PATTERN.sub(
        rf"\g<1>{new_version}\g<3>",
        text,
        count=1,
    )
    path.write_text(updated, encoding="utf-8")


def bump_patch(version: str) -> str:
    """版本号第三位 +1。"""
    major, minor, patch = parse_semver(version)
    return format_semver(major, minor, patch + 1)


def bump_minor(version: str) -> str:
    """版本号第二位 +1，第三位置零。"""
    major, minor, _patch = parse_semver(version)
    return format_semver(major, minor + 1, 0)


def strip_summary_block(text: str) -> str:
    """从文本中移除 UPLOAD_SUMMARY 标记块。"""
    begin = text.rfind(SUMMARY_BEGIN)
    if begin == -1:
        return text.rstrip() + "\n"
    end = text.find(SUMMARY_END, begin)
    if end == -1:
        return text.rstrip() + "\n"
    end += len(SUMMARY_END)
    return (text[:begin] + text[end:]).rstrip() + "\n"


def write_summary_block(path: Path, title: str, bullets: list[str]) -> None:
    """将上传总结写入 _version.py 底部。"""
    text = strip_summary_block(path.read_text(encoding="utf-8"))
    lines = [
        "",
        SUMMARY_BEGIN,
        f"# TITLE: {title}",
        "# BODY:",
    ]
    for item in bullets:
        lines.append(f"# - {item}")
    lines.append(SUMMARY_END)
    lines.append("")
    path.write_text(text + "\n".join(lines), encoding="utf-8")


def remove_summary_block(path: Path) -> None:
    """从 _version.py 中移除 UPLOAD_SUMMARY 标记块。"""
    text = path.read_text(encoding="utf-8")
    path.write_text(strip_summary_block(text), encoding="utf-8")


def read_summary_for_commit(path: Path) -> tuple[str, list[str]]:
    """从 _version.py 解析 UPLOAD_SUMMARY 块的内容。"""
    text = path.read_text(encoding="utf-8")
    begin = text.rfind(SUMMARY_BEGIN)
    end = text.find(SUMMARY_END, begin)
    if begin == -1 or end == -1:
        raise ValueError("_version.py 中缺少 UPLOAD_SUMMARY 标记块")
    block = text[begin:end]
    title = "Update"
    bullets: list[str] = []
    in_body = False
    for raw in block.splitlines():
        line = raw.strip()
        if line.startswith("# TITLE:"):
            title = line[len("# TITLE:"):].strip()
        elif line.startswith("# BODY:"):
            in_body = True
        elif in_body and line.startswith("# -"):
            bullets.append(line[3:].strip())
        elif in_body and line.startswith("#") and not line.startswith("# ---"):
            bullets.append(line.lstrip("# ").strip())
    return title, bullets


def build_commit_message(version: str, title: str, bullets: list[str]) -> str:
    """构建 git commit 消息字符串。"""
    first = f"v{version}: {title}"
    if not bullets:
        return first
    return first + "\n\n" + "\n".join(f"- {b}" for b in bullets)


def classify_changed_paths(paths: list[str], package_dir_name: str = "games/endfield") -> bool:
    """判断变更路径列表中是否包含业务代码改动（非 _version.py 自身）。"""
    prefix = f"{package_dir_name}/"
    readme_names = {
        f"{prefix}_version.py",
        "_version.py",
        f"{prefix}please_read_me.py",
        "please_read_me.py",
    }
    for raw in paths:
        norm = raw.replace("\\", "/").strip()
        if " -> " in norm:
            norm = norm.split(" -> ")[-1].strip()
        if norm in readme_names:
            continue
        if norm and norm != prefix.rstrip("/"):
            return True
    return False


def summarize_changes(paths: list[str]) -> tuple[str, list[str]]:
    """生成变更摘要信息（标题 + 更改列表）。"""
    unique = sorted({p.replace("\\", "/") for p in paths if p.strip()})
    if not unique:
        return "维护性更新", ["无文件列表（请检查 git status）"]

    bullets: list[str] = []
    for p in unique:
        if p.endswith("weapons.json"):
            bullets.append("更新 weapons.json 武器数据")
        elif p.endswith("characters.json"):
            bullets.append("更新 characters.json 角色数据")
        elif "multiplicative_zones" in p:
            bullets.append(f"调整乘区逻辑 {p}")
        elif p.endswith(".py"):
            bullets.append(f"修改 {p}")
        elif p.endswith(".md"):
            bullets.append(f"更新文档 {p}")
        else:
            bullets.append(f"变更 {p}")

    if len(bullets) == 1:
        title = bullets[0]
    else:
        title = f"更新 {len(unique)} 处文件"
    return title, bullets


def get_version() -> str:
    """获取项目版本号。"""
    return _VERSION


def get_exe_version() -> str:
    """获取 EXE 版本号。"""
    return _EXE_VERSION

# --- BEGIN UPLOAD_SUMMARY ---
# TITLE: 更新 15 处文件
# BODY:
# - 变更 "docs//344/273/243/347/240/201/347/273/223/346/236/204/350/247/204/350/214/203.md"
# - 变更 "docs//344/274/232/350/257/235/346/216/245/347/273/255/346/211/213/345/206/214.md"
# - 修改 games/endfield/tests/tools/test_github_upload_signing.py
# - 修改 scripts/_version.py
# - 修改 scripts/deploy_pythonanywhere.py
# - 修改 scripts/devtool.py
# - 修改 scripts/github_download_module.py
# - 修改 scripts/github_upload_module.py
# - 修改 scripts/import_calcpack.py
# - 修改 scripts/tools/__init__.py
# - 修改 scripts/tools/deploy_pythonanywhere.py
# - 修改 scripts/tools/devtool.py
# - 修改 scripts/tools/github_download_module.py
# - 修改 scripts/tools/github_upload_module.py
# - 修改 scripts/tools/import_calcpack.py
# --- END UPLOAD_SUMMARY ---
