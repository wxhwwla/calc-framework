"""品类模板管理器 — 发现、列举、加载适配器模板。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

ADAPTERS_DIR = Path(__file__).resolve().parents[2] / "framework" / "adapters"

# 已知品类模板列表（带品类标签）
CATEGORY_TEMPLATES: dict[str, dict[str, str]] = {
    "simple": {
        "name": "简单伤害计算",
        "category": "通用",
        "description": "最简模板：ATK×倍率−DEF，含暴击分支，适合入门",
    },
    "card_rpg": {
        "name": "卡牌RPG伤害计算",
        "category": "卡牌RPG",
        "description": "减法公式+暴击，适合回合制/卡牌游戏",
    },
    "fps": {
        "name": "FPS武器伤害计算",
        "category": "射击",
        "description": "距离衰减+部位倍率+护甲减伤+DPS，适合射击游戏",
    },
    "moba": {
        "name": "MOBA英雄伤害计算",
        "category": "MOBA",
        "description": "双抗双减伤+暴击+CDR，适合MOBA游戏",
    },
    "multi-zone": {
        "name": "多乘区伤害计算",
        "category": "多乘区RPG",
        "description": "多乘区叠乘（子图模式），适合复杂RPG",
    },
}


def list_templates() -> dict[str, dict[str, str]]:
    """返回所有可用模板的元信息。"""
    available = {}
    for tid, info in CATEGORY_TEMPLATES.items():
        template_dir = ADAPTERS_DIR / tid
        if template_dir.is_dir():
            available[tid] = info
    return available


def load_template(template_id: str) -> dict[str, Any]:
    """加载模板的所有文件内容。

    Returns:
        {"meta.json": {...}, "dag.json": {...}, "attr_schema.json": {...}, ...}
    """
    template_dir = ADAPTERS_DIR / template_id
    if not template_dir.is_dir():
        raise ValueError(f"模板不存在: {template_id}")

    files = {}
    # 加载根目录 JSON 文件（non-dag 的 meta/attr_schema 等）
    for f in template_dir.glob("*.json"):
        if f.name.endswith(".dag.json"):
            files["dag"] = json.loads(f.read_text(encoding="utf-8"))
        else:
            files[f.stem] = json.loads(f.read_text(encoding="utf-8"))

    # 加载 functions.py（如有）
    func_file = template_dir / "functions.py"
    if func_file.exists():
        files["functions.py"] = func_file.read_text(encoding="utf-8")

    # 加载 ui/layout.json（如有）
    ui_file = template_dir / "ui" / "layout.json"
    if ui_file.exists():
        files["ui_layout"] = json.loads(ui_file.read_text(encoding="utf-8"))

    # 加载 dag/*.dag.json（入口 DAG）
    dag_dir = template_dir / "dag"
    if dag_dir.is_dir():
        for dag_file in dag_dir.glob("*.dag.json"):
            files["dag"] = json.loads(dag_file.read_text(encoding="utf-8"))
    else:
        # 直接放在根目录的 .dag.json
        for dag_file in template_dir.glob("*.dag.json"):
            files["dag"] = json.loads(dag_file.read_text(encoding="utf-8"))

    return files
