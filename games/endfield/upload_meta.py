#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""

上传脚本用的版本号与临时提交说明（由 github_upload_module.py 调用）。



说明全文见 please_read_me.py 中的 UPLOAD_WORKFLOW。

"""



from __future__ import annotations

import re
from pathlib import Path

# 写在 please_read_me.py 文件末尾的标记（推送成功后删除整块）

SUMMARY_BEGIN = "# --- UPLOAD_SUMMARY ---"

SUMMARY_END = "# --- END UPLOAD_SUMMARY ---"



_VERSION_PATTERN = re.compile(

    r'^(_VERSION\s*=\s*["\'])([^"\']+)(["\'])',

    re.MULTILINE,

)





def please_read_me_path(package_root: Path | None = None) -> Path:

    """返回 please_read_me.py 路径。"""

    root = package_root or Path(__file__).resolve().parent

    return root / "please_read_me.py"





def parse_semver(version: str) -> tuple[int, int, int]:

    parts = version.strip().split(".")

    if len(parts) != 3 or not all(p.isdigit() for p in parts):

        raise ValueError(f"无效语义化版本: {version!r}（需要 MAJOR.MINOR.PATCH）")

    return int(parts[0]), int(parts[1]), int(parts[2])
    """parse semver。"""





def format_semver(major: int, minor: int, patch: int) -> str:

    return f"{major}.{minor}.{patch}"
    """format semver。"""





def read_version(path: Path) -> str:

    text = path.read_text(encoding="utf-8")

    match = _VERSION_PATTERN.search(text)

    if not match:

        raise ValueError(f"未在 {path} 中找到 _VERSION")

    return match.group(2)
    """read version。"""





def write_version(path: Path, new_version: str) -> None:

    text = path.read_text(encoding="utf-8")

    if not _VERSION_PATTERN.search(text):

        raise ValueError(f"未在 {path} 中找到 _VERSION")

    updated = _VERSION_PATTERN.sub(

        rf"\g<1>{new_version}\g<3>",

        text,

        count=1,

    )

    path.write_text(updated, encoding="utf-8")
    """write version。"""





def bump_patch(version: str) -> str:

    major, minor, patch = parse_semver(version)

    return format_semver(major, minor, patch + 1)
    """bump patch。"""





def bump_minor(version: str) -> str:

    major, minor, _patch = parse_semver(version)

    return format_semver(major, minor + 1, 0)
    """bump minor。"""





def strip_summary_block(text: str) -> str:

    """只删除文件末尾的上传总结块（避免误删 UPLOAD_WORKFLOW 文档里的同名说明文字）。"""

    begin = text.rfind(SUMMARY_BEGIN)

    if begin == -1:

        return text.rstrip() + "\n"

    end = text.find(SUMMARY_END, begin)

    if end == -1:

        return text.rstrip() + "\n"

    end += len(SUMMARY_END)

    return (text[:begin] + text[end:]).rstrip() + "\n"





def write_summary_block(path: Path, title: str, bullets: list[str]) -> None:

    """在 please_read_me.py 末尾写入临时上传总结（注释行）。"""

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

    text = path.read_text(encoding="utf-8")

    path.write_text(strip_summary_block(text), encoding="utf-8")
    """remove summary block。"""





def read_summary_for_commit(path: Path) -> tuple[str, list[str]]:

    """解析底部总结块，返回 (title, bullet_lines)。"""

    text = path.read_text(encoding="utf-8")

    begin = text.rfind(SUMMARY_BEGIN)

    end = text.find(SUMMARY_END, begin)

    if begin == -1 or end == -1:

        raise ValueError("please_read_me.py 中缺少 UPLOAD_SUMMARY 标记块")

    block = text[begin:end]

    title = "Update"

    bullets: list[str] = []

    in_body = False

    for raw in block.splitlines():

        line = raw.strip()

        if line.startswith("# TITLE:"):

            title = line[len("# TITLE:") :].strip()

        elif line.startswith("# BODY:"):

            in_body = True

        elif in_body and line.startswith("# -"):

            bullets.append(line[3:].strip())

        elif in_body and line.startswith("#") and not line.startswith("# ---"):

            bullets.append(line.lstrip("# ").strip())

    return title, bullets





def build_commit_message(version: str, title: str, bullets: list[str]) -> str:

    """生成 git commit 正文：首行 vX.Y.Z: 标题，下列表。"""

    first = f"v{version}: {title}"

    if not bullets:

        return first

    return first + "\n\n" + "\n".join(f"- {b}" for b in bullets)





def classify_changed_paths(paths: list[str], package_dir_name: str = "games/endfield") -> bool:

    """

    是否存在除 please_read_me.py 以外的业务改动路径。

    用于判断本次上传是否应 bump _VERSION。

    """

    prefix = f"{package_dir_name}/"

    readme_names = {

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

    """根据改动路径生成 (标题, 条目列表)。"""

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

