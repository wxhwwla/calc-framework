#!/usr/bin/env python3

# SPDX-License-Identifier: AGPL-3.0
"""RawRecord → 标准 EntitySchema 转换器。



处理来自 CSV 或干净 JSON 的输入。依赖输入数据的 key 命名约定：



CSV 宽表模式（skills 列以 ``技能名称1``、``技能名称2`` 等为前缀）：



+------------------+------------------+--------------------------+

| CSV 列           | 映射到           | 类型                     |

+------------------+------------------+--------------------------+

| 名称             | EntitySchema.名称 | str                      |

| 星级             | EntitySchema.星级 | int                      |

| 类型             | EntitySchema.类型 | str                      |

| … 任意筛选字段    | 透传             | 自动推断                  |

| 技能名称1         | SkillSchema.名称 | str                      |

| 技能标签1         | SkillSchema.标签 | str                      |

| 技能百分比1       | SkillSchema.百分比 | bool                    |

| 技能类型1         | SkillSchema.技能类型 | str（可空）            |

| 段1倍率1          | SegmentSchema.倍率| 逗号分隔 int 列表        |

| 段1类型1          | SegmentSchema.伤害类型 | str（可空）         |

| 段2倍率1          | 第二段的倍率      | 逗号分隔 int 列表        |

| …                |                  |                          |

+------------------+------------------+--------------------------+



技能序号 + 段序号从 1 开始，框架自动收集到 ``技能[N]`` 的 ``段[M]``。

"""

from __future__ import annotations


import re

from typing import Any, Dict, List, Tuple


from ..readers.csv_reader import parse_int_list

from ..schema import EntitySchema, RawRecord, SkillSchema, SegmentSchema


def to_standard(records: List[RawRecord]) -> List[EntitySchema]:
    """将 RawRecord 列表转换为标准 EntitySchema 列表。



    Args:

        records: 读取阶段的原始记录（每行一个字典）



    Returns:

        标准化的实体列表

    """

    return [_transform_one(r) for r in records]


def _transform_one(record: RawRecord) -> EntitySchema:
    """_transform_one 实现。"""
    entity: EntitySchema = {"名称": str(record.get("名称", "")), "技能": []}

    has_entity_type = record.get("_entity_type")

    if has_entity_type:
        entity["_entity_type"] = str(has_entity_type)

    _collect_skills(record, entity)

    for key, value in record.items():
        if key in ("名称", "_entity_type"):
            continue

        if _is_skill_column(key):
            continue

        if key == "技能":
            continue

        entity[key] = _typed(value)

    return entity


def _is_skill_column(key: str) -> bool:
    """_is_skill_column 实现。"""
    return bool(re.match(r"^技能(名称|标签|百分比|类型)", key)) or bool(re.match(r"^段\d+(倍率|类型)", key))


_SKILL_COL_PATTERNS: Dict[str, str] = {
    r"技能名称(\d+)": "名称",
    r"技能标签(\d+)": "标签",
    r"技能百分比(\d+)": "百分比",
    r"技能类型(\d+)": "技能类型",
    r"段(\d+)倍率(\d+)": "segment_rate",
    r"段(\d+)类型(\d+)": "segment_type",
}


def _collect_skills(record: RawRecord, entity: EntitySchema) -> None:
    """_collect_skills 实现。"""
    skill_indices: Dict[int, SkillSchema] = {}

    segment_indices: Dict[Tuple[int, int], SegmentSchema] = {}

    for key, value in record.items():
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue

        for pattern, target in _SKILL_COL_PATTERNS.items():
            m = re.match(pattern, key)

            if not m:
                continue

            if target == "segment_rate":
                skill_idx = int(m.group(2))

                seg_idx = int(m.group(1))

                rates = _parse_int_list(value)

                if rates:
                    seg = segment_indices.setdefault((skill_idx, seg_idx), {"倍率": []})

                    seg["倍率"] = rates

            elif target == "segment_type":
                skill_idx = int(m.group(2))

                seg_idx = int(m.group(1))

                raw = str(value).strip()

                if raw and raw != "-":
                    seg = segment_indices.setdefault((skill_idx, seg_idx), {})

                    seg["伤害类型"] = raw

            else:
                skill_idx = int(m.group(1))

                skill = skill_indices.setdefault(skill_idx, {"名称": "", "标签": "主动", "百分比": True, "段": []})

                if target == "名称":
                    skill["名称"] = str(value)

                elif target == "标签":
                    skill["标签"] = str(value)

                elif target == "百分比":
                    skill["百分比"] = _parse_bool(value)

                elif target == "技能类型" and str(value).strip():
                    skill["技能类型"] = str(value).strip()

            break

    sorted_skill_ids = sorted(skill_indices.keys())

    for skill_id in sorted_skill_ids:
        skill = skill_indices[skill_id]

        seg_ids = sorted(
            [k for k in segment_indices if k[0] == skill_id],
            key=lambda x: x[1],
        )

        skill["段"] = [segment_indices[sid] for sid in seg_ids]

        entity.setdefault("技能", []).append(skill)


def _typed(value: Any) -> Any:
    """_typed 实现。"""
    if isinstance(value, int | float | bool):
        return value

    s = str(value).strip()

    if s.lower() in ("true", "yes", "1"):
        return True

    if s.lower() in ("false", "no", "0"):
        return False

    try:
        if "." in s or "e" in s.lower():
            return float(s)

        return int(s)

    except (ValueError, TypeError):
        return s


def _parse_bool(value: Any) -> bool:
    """_parse_bool 实现。"""
    if isinstance(value, bool):
        return value

    if isinstance(value, int | float):
        return value != 0

    s = str(value).strip().lower()

    return s in ("true", "yes", "1")


def _parse_int_list(value: Any) -> List[int]:
    """_parse_int_list 实现。"""
    if isinstance(value, list):
        return [int(x) for x in value if x is not None]

    if isinstance(value, str):
        return parse_int_list(value)

    return []
