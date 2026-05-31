#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""Replace calc-engine/ -> calc_engine/ in all text files (skip temp scripts and calc_engine/ dir itself)."""
import os


EXCLUDE_DIRS = {".venv", "__pycache__", ".pytest_cache", ".git", ".trae", "node_modules", "dist", "build"}
SELF_FILES = {"replace_adapters_imports.py", "replace_docs.py", "replace_paths.py", "rename_pkg.py"}


def is_text_file(filepath):
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
        chunk.decode("utf-8")
        return b"\x00" not in chunk
    except (UnicodeDecodeError, OSError):
        return False


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    count = 0
    modified_files = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for f in files:
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, repo_root)

            if f in SELF_FILES:
                continue
            if not is_text_file(fpath):
                continue

            with open(fpath, "r", encoding="utf-8") as fh:
                content = fh.read()

            original = content
            content = content.replace("calc-engine/", "calc_engine/")

            if content != original:
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write(content)
                count += 1
                modified_files.append(rel)
                print(f"  MODIFIED: {rel}")

    print(f"\nTotal files modified: {count}")
    return modified_files


if __name__ == "__main__":
    main()
