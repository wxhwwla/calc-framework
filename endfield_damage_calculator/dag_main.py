#!/usr/bin/env python3
"""
终末地 DAG 工具 — 根入口文件

生成/调试 DAG JSON 配置文件。

使用方式：
    python dag_main.py                          # 重新生成 endfield_full.dag.json
    python dag_main.py --debug                  # 启动 DAG 分步调试器（需 calc-framework）
    python dag_main.py --debug [dag_json_path]  # 调试指定 DAG 文件

等价命令：
    python -m calculation.multiplicative_zones.dag            # DAG 生成
    calc-layout --dag path.dag.json --auto -o layout.json     # 布局生成（calc-framework CLI）
"""

import sys
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if "--debug" in sys.argv:
        # 启动 DAG 分步调试器
        try:
            from calc_framework.dag.debugger_cli import main as debug_main
        except ImportError:
            print("错误：DAG 调试器需要 calc-framework 包。")
            print("请运行: pip install -e ./framework")
            sys.exit(1)

        dag_path = args[0] if args else None
        if dag_path:
            sys.argv = [sys.argv[0], "--dag", dag_path]
        else:
            # 默认用生成的 DAG
            from calculation.multiplicative_zones.dag.config import OUTPUT_PATH

            sys.argv = [sys.argv[0], "--dag", str(OUTPUT_PATH)]
        debug_main()
        return

    # 默认：生成 DAG JSON
    from calculation.multiplicative_zones.dag.config import main as gen_main

    gen_main()


if __name__ == "__main__":
    main()
