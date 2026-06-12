#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Replace games.endfield -> games.endfield in all .py files outside calc-engine/ (moved to tools/)."""

import os


REPLACEMENTS = [
    ("from games.endfield", "from games.endfield"),
    ("import games.endfield", "import games.endfield"),
    ('"games.endfield.', '"games.endfield.'),
    ("'games.endfield.", "'games.endfield."),
]

EXCLUDE_DIRS = {
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".trae",
    "node_modules",
    "dist",
    "build",
    "calc-engine",
    ".github",
}

EXCLUDE_FILES = {"replace_adapters_imports.py"}


def replace_in_file(filepath: str) -> bool:
    """替换单个文件中的模块导入路径。

    Args:
        filepath: 文件路径

    Returns:
        文件被修改返回 True，否则 False
    """
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    original = content
    for old, new in REPLACEMENTS:
        content = content.replace(old, new)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    """CLI 入口。"""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    count = 0
    modified_files = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for f in files:
            if not f.endswith(".py"):
                continue
            if f in EXCLUDE_FILES:
                continue

            fpath = os.path.join(root, f)
            if "calc-engine" in os.path.normpath(fpath).split(os.sep):
                continue

            if replace_in_file(fpath):
                count += 1
                rel_path = os.path.relpath(fpath, repo_root)
                modified_files.append(rel_path)
                print(f"  MODIFIED: {rel_path}")

    print(f"\nTotal files modified: {count}")
    return modified_files


if __name__ == "__main__":
    main()
