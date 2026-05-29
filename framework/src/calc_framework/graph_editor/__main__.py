#!/usr/bin/env python3
"""graph_editor 包入口 — 启动可视化公式图编辑器。"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    from PySide6.QtWidgets import QApplication

    from calc_framework.graph_editor.graph_editor_widget import GraphEditorWidget

    app = QApplication(sys.argv)
    widget = GraphEditorWidget()
    widget.setWindowTitle("公式计算图编辑器")
    widget.resize(1200, 800)
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
