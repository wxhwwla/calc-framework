#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据录入 ETL 工具 CLI。

用法::

    # CSV → 标准 JSON
    python -m tools.data_pipeline.cli input.csv -o output.json

    # 终末地旧 characters.json → 标准 JSON
    python -m tools.data_pipeline.cli characters.json --migrate-characters -o characters_standard.json

    # 终末地旧 weapons.json → 标准 JSON
    python -m tools.data_pipeline.cli weapons.json --migrate-weapons -o weapons_standard.json

    # 校验标准 JSON
    python -m tools.data_pipeline.cli data.json --validate

    # 查看 schema 帮助
    python -m tools.data_pipeline.cli --schema-help
"""

from __future__ import annotations

import json
import sys
import os

from typing import Any, Dict, List

# 确保项目根在 sys.path 中（tools/ 是隐式 namespace package）
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tools.data_pipeline.readers.csv_reader import read_csv
from tools.data_pipeline.readers.json_reader import read_json
from tools.data_pipeline.transformers.from_legacy_endfield import from_characters, from_weapons
from tools.data_pipeline.transformers.to_standard import to_standard
from tools.data_pipeline.validators.schema_check import validate_all


def main() -> None:
    args = _parse_args()

    if args.get("schema_help"):
        _show_schema_help()
        return

    path = args["path"]
    output = args.get("output")
    do_validate = args.get("validate", False)
    migrate_chars = args.get("migrate_characters", False)
    migrate_weaps = args.get("migrate_weapons", False)
    stacked = args.get("stacked_skills", False)

    # --- 读取 ---
    try:
        if _is_csv(path):
            records = read_csv(path)
        else:
            records = read_json(path)
    except Exception as e:
        print(f"读取失败: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 转换 ---
    try:
        if migrate_chars:
            entities = from_characters([dict(r) for r in records])
        elif migrate_weaps:
            entities = from_weapons([dict(r) for r in records])
        else:
            entities = to_standard(records)
    except Exception as e:
        print(f"转换失败: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 校验 ---
    if do_validate:
        _run_validation(entities)

    # --- 输出 ---
    if output:
        _write_json(entities, output)
        print(f"已写入 {output} ({len(entities)} 条)")
    else:
        print(json.dumps(entities, ensure_ascii=False, indent=2))


def _parse_args() -> Dict[str, Any]:
    args = sys.argv[1:]
    result: Dict[str, Any] = {}

    if "--schema-help" in args:
        result["schema_help"] = True
        return result

    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    result["path"] = args[0]

    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "-o" and i + 1 < len(args):
            result["output"] = args[i + 1]
            i += 2
        elif arg == "--validate":
            result["validate"] = True
            i += 1
        elif arg == "--migrate-characters":
            result["migrate_characters"] = True
            i += 1
        elif arg == "--migrate-weapons":
            result["migrate_weapons"] = True
            i += 1
        elif arg == "--stacked-skills":
            result["stacked_skills"] = True
            i += 1
        else:
            print(f"未知参数: {arg}", file=sys.stderr)
            sys.exit(1)

    return result


def _is_csv(path: str) -> bool:
    return path.lower().endswith(".csv")


def _run_validation(entities: List[Dict[str, Any]]) -> None:


    errors = validate_all(entities)
    has_errors = False
    for idx, errs in errors:
        if errs:
            name = entities[idx].get("名称", f"[{idx}]")
            print(f"校验失败: {name}")
            for e in errs:
                print(f"  - {e}")
            has_errors = True
    if has_errors:
        print("校验未通过，仍继续输出")
    else:
        print(f"校验通过: {len(entities)} 条")


def _write_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _show_schema_help() -> None:
    print("""
标准数据契约 — tools/data_pipeline/schema.py

四层架构：

1. 实体层（EntitySchema）
   必填: 名称 (str)
   可选: _entity_type (str) — "character"/"weapon"/"equipment"/"mount"


2. 属性筛选层
   自由定义，框架不约束。例如:
     "星级": int, "类型": str, "属性": str, "武器": str, ...

3. 技能层（SkillSchema）
   - 名称 (str): 技能名 / 筛选 key（"战技"、"主能力值+"）
   - 标签 (str): "主动" 或 "被动"
   - 百分比 (bool): 倍率整数是否需 ÷100
   - 技能类型 (str, 可选): 默认伤害类型
   - 段 (list[SegmentSchema])

4. 数值层（SegmentSchema）
   - 倍率 (list[int]): 各等级的值，索引语义由适配器决定
   - 伤害类型 (str, 可选): 可覆盖技能级的类型

示例:
{
  "名称": "陈千语",
  "星级": 5,
  "类型": "近卫",
  "技能": [
    {
      "名称": "战技",
      "标签": "主动",
      "百分比": true,
      "段": [
        {"倍率": [169, 186, 203], "伤害类型": "物理"}
      ]
    }
  ]
}
""")


if __name__ == "__main__":
    main()
