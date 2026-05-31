# SPDX-License-Identifier: AGPL-3.0
"""Replace calc_engine/endfield/ filesystem paths in non-.md files (excluding adapters/ dir)."""
import os


EXCLUDE_DIRS = {".venv", "__pycache__", ".pytest_cache", ".git", ".trae", "node_modules", "dist", "build"}
SELF_FILES = {"_replace_adapters_imports.py", "_replace_docs.py", "_replace_paths.py"}


def is_text_file(filepath):
    """Check if a file is likely text by reading a small chunk."""
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(8192)
        # If no null bytes and valid UTF-8 decodable, it's text
        chunk.decode("utf-8")
        return b"\x00" not in chunk
    except (UnicodeDecodeError, OSError):
        return False


def main():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    count = 0
    modified_files = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for f in files:
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, repo_root)

            # Skip adapters/ dir (will be deleted), temp scripts
            if rel.split(os.sep)[0] in {"adapters"}:
                continue
            if f in SELF_FILES or f == "_replace_imports.py":
                continue
            if f.endswith(".md"):
                continue
            if not is_text_file(fpath):
                continue

            with open(fpath, "r", encoding="utf-8") as fh:
                content = fh.read()

            original = content
            content = content.replace("calc_engine/endfield/", "calc-engine/endfield/")

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
