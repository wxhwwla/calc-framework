#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: AGPL-3.0
"""CSV 读取器：将 CSV 文件解析为 RawRecord 列表。



CSV 格式约定（两套模式）：



**宽表模式**（默认）：

每行一个实体（角色/武器），列包含所有字段。



示例（角色）：

```

名称,星级,类型,武器,主能力,副能力,技能名称1,技能标签1,技能百分比1,技能类型1,段1倍率,段1类型,段2倍率,段2类型

陈千语,5,近卫,单手剑,敏捷,力量,战技,主动,true,物理,"169,186,203,...",物理,,

```



**技能堆叠模式**（``--stacked-skills``）：

技能名称、标签、百分比、倍率等拆到多行，用 ``技能序号`` 关联。

每行一个技能段，同名实体合并。

"""

from __future__ import annotations


import csv


from pathlib import Path

from typing import Any, List


from ..schema import RawRecord


def read_csv(
    path: str | Path,
    *,
    encoding: str = "utf-8-sig",
    delimiter: str = ",",
) -> List[RawRecord]:
    """读取 CSV 返回原始记录列表。



    Args:

        path: CSV 文件路径

        encoding: 编码，默认 utf-8-sig（兼容 Excel BOM）

        delimiter: 分隔符，默认逗号



    Returns:

        RawRecord 列表，每行一个字典

    """

    records: List[RawRecord] = []

    with open(path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            cleaned = {k.strip(): _clean_value(v) for k, v in row.items() if k}

            records.append(cleaned)

    return records


def _clean_value(value: str | None) -> Any:
    """_clean_value 实现。"""
    if value is None:
        return None

    stripped = value.strip()

    if stripped == "" or stripped == "-":
        return None

    return stripped


def parse_comma_list(text: str | None) -> List[str]:
    """解析逗号分隔的字符串为列表。"""

    if not text:
        return []

    return [s.strip() for s in text.split(",") if s.strip()]


def parse_int_list(text: str | None) -> List[int]:
    """解析逗号分隔的整数列表。"""

    if not text:
        return []

    result: List[int] = []

    for s in text.split(","):
        s = s.strip()

        if s:
            try:
                result.append(int(s))

            except ValueError:
                pass

    return result


def parse_float_list(text: str | None) -> List[float]:
    """解析逗号分隔的浮点数列表。"""

    if not text:
        return []

    result: List[float] = []

    for s in text.split(","):
        s = s.strip()

        if s:
            try:
                result.append(float(s))

            except ValueError:
                pass

    return result
