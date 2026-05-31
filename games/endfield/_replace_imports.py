# SPDX-License-Identifier: AGPL-3.0
"""Replace adapters.endfield -> games.endfield in calc_engine/endfield/ .py files."""
import os


def replace_in_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Replace import statements
    content = content.replace("from games.endfield", "from games.endfield")
    content = content.replace("import games.endfield", "import games.endfield")

    # Replace string-based references (in patch(), import_module(), etc.)
    content = content.replace('"games.endfield.', '"games.endfield.')
    content = content.replace("'games.endfield.", "'games.endfield.")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    return False


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    count = 0
    modified_files = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py") and f != "_replace_imports.py":
                fpath = os.path.join(root, f)
                if replace_in_file(fpath):
                    count += 1
                    rel_path = os.path.relpath(fpath, base)
                    modified_files.append(rel_path)
                    print(f"  MODIFIED: {rel_path}")

    print(f"\nTotal files modified: {count}")
    return modified_files


if __name__ == "__main__":
    main()
