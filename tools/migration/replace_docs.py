#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Replace calc_engine/endfield and games.endfield in .md docs with calc-engine equivalents."""

import os


def main():
    """替换 .md 文档中的 calc_engine/endfield/ 为 calc-engine/endfield/。

    Returns:
        被修改的文件路径列表
    """
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    count = 0
    modified_files = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            d for d in dirs if d not in {".venv", "__pycache__", ".git", ".trae", "node_modules", "dist", "build"}
        ]
        for f in files:
            if not f.endswith(".md"):
                continue
            fpath = os.path.join(root, f)
            with open(fpath, encoding="utf-8") as fh:
                content = fh.read()

            original = content
            content = content.replace("calc_engine/endfield/", "calc-engine/endfield/")
            content = content.replace("games.endfield", "games.endfield")

            if content != original:
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write(content)
                count += 1
                rel_path = os.path.relpath(fpath, repo_root)
                modified_files.append(rel_path)
                print(f"  MODIFIED: {rel_path}")

    print(f"\nTotal .md files modified: {count}")
    return modified_files


if __name__ == "__main__":
    main()
