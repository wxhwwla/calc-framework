#!/usr/bin/env python3
"""
公式计算图编辑器 — 根入口文件

启动可视化公式图编辑器。

使用方式：
    python graph_editor_main.py               # 启动编辑器
    python graph_editor_main.py path/to.json  # 打开已有文件
    python -m calc_framework.graph_editor      # 等价
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_PKG_DIR = Path(__file__).resolve().parent
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))


def main() -> None:
    from PySide6.QtWidgets import QApplication

    from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget
    from calc_framework.graph_editor.serializer import document_from_json

    app = QApplication(sys.argv)
    widget = GraphEditorWidget()
    widget.setWindowTitle("公式计算图编辑器")
    widget.resize(1200, 800)

    # 如果提供了 JSON 文件路径，加载它
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        filepath = Path(args[0])
        if filepath.exists():
            from calc_framework.graph_editor.schema import validate, GraphDocument
            import json
            with open(filepath, encoding="utf-8") as f:
                doc = document_from_json(json.load(f))
            validate(doc)
            for node in doc.nodes:
                widget.add_graph_node(node)

    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
