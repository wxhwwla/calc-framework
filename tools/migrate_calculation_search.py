#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 calculation 搜索相关模块迁入 calculation/search/ 并生成 re-export stub。"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "endfield_damage_calculator" / "calculation"
SEARCH = PKG / "search"

# 旧文件名 -> search 子包内新文件名（plan / run / evaluate / persist 分组前缀）
MOVES: dict[str, str] = {
  # plan
    "search_controller.py": "plan_controller.py",
    "search_estimate.py": "plan_estimate.py",
    "single_skill_search_job.py": "plan_job.py",
  # run
    "search_runner.py": "run_runner.py",
    "search_session.py": "run_session.py",
    "single_skill_search_runner.py": "run_single_skill.py",
    "mvp_pipeline.py": "run_mvp.py",
    "parallel_search.py": "run_parallel.py",
    "search_cancel.py": "run_cancel.py",
  # evaluate
    "search_task_evaluator.py": "evaluate_task.py",
    "search_eval_context.py": "evaluate_context.py",
    "multi_skill_search_eval.py": "evaluate_multi_skill.py",
  # persist
    "search_persistence.py": "persist_store.py",
}

# 旧模块名 -> 新模块路径（用于替换 import）
OLD_TO_NEW: dict[str, str] = {
    old: f"calculation.search.{new[:-3]}"
    for old, new in MOVES.items()
}

# 修正：模块路径应含 .py 去掉后缀后的名字
OLD_TO_NEW = {
    "search_controller": "calculation.search.plan_controller",
    "search_estimate": "calculation.search.plan_estimate",
    "single_skill_search_job": "calculation.search.plan_job",
    "search_runner": "calculation.search.run_runner",
    "search_session": "calculation.search.run_session",
    "single_skill_search_runner": "calculation.search.run_single_skill",
    "mvp_pipeline": "calculation.search.run_mvp",
    "parallel_search": "calculation.search.run_parallel",
    "search_cancel": "calculation.search.run_cancel",
    "search_task_evaluator": "calculation.search.evaluate_task",
    "search_eval_context": "calculation.search.evaluate_context",
    "multi_skill_search_eval": "calculation.search.evaluate_multi_skill",
    "search_persistence": "calculation.search.persist_store",
}

STUB_TEMPLATE = '''#!/usr/bin/env python3
# -*- coding: utf-8__
"""兼容 re-export：实现位于 calculation.search.{target}。"""

from calculation.search.{target} import *  # noqa: F403
'''


def rewrite_imports(text: str) -> str:
    for old, new in OLD_TO_NEW.items():
        text = text.replace(f"from calculation.{old} import", f"from {new} import")
        text = text.replace(f"import calculation.{old}", f"import {new}")
    # search 包内相对 import
    for old, new in OLD_TO_NEW.items():
        short = new.split(".")[-1]
        text = text.replace(f"from calculation.{old} import", f"from .{short} import")
    return text


def main() -> None:
    SEARCH.mkdir(exist_ok=True)

    for old_name, new_name in MOVES.items():
        src = PKG / old_name
        if not src.exists():
            print("skip missing", old_name)
            continue
        dst = SEARCH / new_name
        content = src.read_text(encoding="utf-8")
        # 包内文件：calculation.x -> 相对 import
        for old_mod, new_path in OLD_TO_NEW.items():
            short = new_path.split(".")[-1]
            content = content.replace(
                f"from calculation.{old_mod} import",
                f"from .{short} import",
            )
        dst.write_text(content, encoding="utf-8")
        target = new_name[:-3]
        stub = STUB_TEMPLATE.replace("{target}", target).replace(
            "__", "—"
        ).replace("—", "-")
        # fix stub header typo
        stub = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容 re-export：实现位于 calculation.search.{target}。"""

from calculation.search.{target} import *  # noqa: F403
'''
        (PKG / old_name).write_text(stub, encoding="utf-8")
        print("migrated", old_name, "->", new_name)

    init = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量遍历搜索子包（plan / run / evaluate / persist）。

- plan_*：作业输入、预估、SingleSkillSearchJob
- run_*：会话执行、MVP、并行、取消
- evaluate_*：任务评估上下文与多技能评分
- persist_*：SQLite 续跑与批量 processed
"""

__all__ = [
    "evaluate_context",
    "evaluate_multi_skill",
    "evaluate_task",
    "persist_store",
    "plan_controller",
    "plan_estimate",
    "plan_job",
    "run_cancel",
    "run_mvp",
    "run_parallel",
    "run_runner",
    "run_session",
    "run_single_skill",
]
'''
    (SEARCH / "__init__.py").write_text(init, encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
