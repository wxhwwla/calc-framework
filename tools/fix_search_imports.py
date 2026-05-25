#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 calculation/search 子包内跨目录相对 import。"""

from __future__ import annotations

from pathlib import Path

PKG = Path(__file__).resolve().parent.parent / "endfield_damage_calculator" / "calculation" / "search"

FIXES: dict[str, list[tuple[str, str]]] = {
    "plan/controller.py": [
        ("from .multi_skill import", "from ..evaluate.multi_skill import"),
    ],
    "plan/job.py": [
        ("from .multi_skill import", "from ..evaluate.multi_skill import"),
    ],
    "run/single_skill.py": [
        ("from .controller import", "from ..plan.controller import"),
        ("from .estimate import", "from ..plan.estimate import"),
        ("from .job import", "from ..plan.job import"),
    ],
    "run/session.py": [
        ("from .context import", "from ..evaluate.context import"),
        ("from .store import", "from ..persist.store import"),
    ],
    "run/runner.py": [
        ("from .context import", "from ..evaluate.context import"),
    ],
    "run/mvp.py": [
        ("from .context import", "from ..evaluate.context import"),
        ("from .task import", "from ..evaluate.task import"),
        ("from .job import", "from ..plan.job import"),
    ],
    "persist/store.py": [
        ("from .parallel import", "from ..run.parallel import"),
        ("from .cancel import", "from ..run.cancel import"),
        ("from .context import", "from ..evaluate.context import"),
    ],
    "evaluate/task.py": [
        ("from .context import", "from .context import"),  # same package OK
        ("from .job import", "from ..plan.job import"),
    ],
}


def main() -> None:
    for rel, pairs in FIXES.items():
        path = PKG / rel
        if not path.exists():
            print("missing", rel)
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old != new:
                text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        print("fixed", rel)


if __name__ == "__main__":
    main()
