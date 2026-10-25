# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki 数据提取基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ExtractedData:
    """爬虫提取出的标准化数据。"""

    game_name: str = ""
    source: str = ""
    characters: list[dict[str, Any]] = field(default_factory=list)
    weapons: list[dict[str, Any]] = field(default_factory=list)
    equipments: list[dict[str, Any]] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    formula_hints: list[str] = field(default_factory=list)
    raw_pages: list[str] = field(default_factory=list)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class BaseExtractor(ABC):
    """Wiki 数据提取器基类。

    子类实现具体的提取逻辑（BWIKI 的 infobox 解析、Fandom 的表格解析等）。
    """

    def __init__(self, wiki_url: str) -> None:
        self.wiki_url = wiki_url
        self.data = ExtractedData(source=wiki_url)

    @abstractmethod
    def extract(self) -> ExtractedData:
        """执行提取，返回结构化数据。"""
        ...
