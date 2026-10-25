# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""批量为缺少编码声明的 .py 文件添加 # -*- coding: utf-8 -*-。"""

from __future__ import annotations

from pathlib import Path

ENCODING_LINE = "# -*- coding: utf-8 -*-\n"
SKIP_DIRS = {"__pycache__", ".venv", ".tmp-audit-venv", "dist", "node_modules", ".git"}


def needs_encoding_declaration(path: Path) -> bool:
    """检查文件是否缺少编码声明（检查前3行）。"""
    try:
        with open(path, encoding="utf-8") as f:
            for _ in range(3):
                line = f.readline()
                if not line:
                    break
                if "coding:" in line or "coding=" in line:
                    return False
        return True
    except (UnicodeDecodeError, OSError):
        return False


def add_encoding_declaration(path: Path) -> bool:
    """为文件添加编码声明。返回是否修改。"""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False

    lines = text.split("\n")
    insert_pos = 0

    # 如果第一行是 shebang，插入到 shebang 之后
    if lines and lines[0].startswith("#!"):
        insert_pos = 1

    # 插入编码声明
    lines.insert(insert_pos, ENCODING_LINE.rstrip("\n"))
    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def main() -> None:
    """扫描并添加编码声明。"""
    repo_root = Path(__file__).resolve().parents[2]
    dirs_to_scan = ["games", "framework/src", "web/backend", "scripts", "tools"]
    modified = 0
    skipped = 0

    for dir_name in dirs_to_scan:
        dir_path = repo_root / dir_name
        if not dir_path.is_dir():
            continue
        for py_file in dir_path.rglob("*.py"):
            # 跳过特殊目录
            parts = py_file.relative_to(repo_root).parts
            if any(s in parts for s in SKIP_DIRS):
                continue
            if needs_encoding_declaration(py_file):
                if add_encoding_declaration(py_file):
                    modified += 1
                    if modified % 50 == 0:
                        print(f"  已处理 {modified} 个文件...")
                else:
                    skipped += 1

    print(f"\n完成：修改 {modified} 个文件，跳过 {skipped} 个文件")


if __name__ == "__main__":
    main()
