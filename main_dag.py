#!/usr/bin/env python3
"""
DAG 工具 — 根入口

生成/调试 DAG JSON 配置文件。

使用方式：
    python main_dag.py                          # 重新生成 endfield_full.dag.json
    python main_dag.py --debug                  # 启动 DAG 分步调试器（需 calc-framework）
    python main_dag.py --debug [dag_json_path]  # 调试指定 DAG 文件
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if "--debug" in sys.argv:
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
            from adapters.endfield.calc.multiplicative_zones.dag.config import OUTPUT_PATH

            sys.argv = [sys.argv[0], "--dag", str(OUTPUT_PATH)]
        debug_main()
        return

    from adapters.endfield.calc.multiplicative_zones.dag.config import main as gen_main

    gen_main()


if __name__ == "__main__":
    main()
