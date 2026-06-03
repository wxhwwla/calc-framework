# SPDX-License-Identifier: AGPL-3.0
"""BWIKI（biligame）平台适配器。"""

from __future__ import annotations

from ..client import MediaWikiClient, get_api_url
from ..extractor import BaseExtractor, ExtractedData


class BWIKIExtractor(BaseExtractor):
    """BWIKI 平台的数据提取器。

    BWIKI 使用 MediaWiki API，页面使用 wikitext 模板（infobox）展示数据。
    """

    def __init__(self, wiki_url: str) -> None:
        super().__init__(wiki_url)
        api_url = get_api_url(wiki_url)
        self.client = MediaWikiClient(api_url)

    def extract(self) -> ExtractedData:
        """执行提取流程。"""
        # 尝试从常见分类获取页面
        for cat in ["角色", "干员", "英雄", "单位", "人物"]:
            pages = self.client.query_category(cat, limit=20)
            if pages:
                for p in pages[:10]:
                    self.data.raw_pages.append(p.get("title", ""))
                    text = self.client.get_page_text(p["title"])
                    if text:
                        # 提取 infobox 模板内容（简化版）
                        hints = self._extract_formula_hints(text)
                        self.data.formula_hints.extend(hints)
                break
        return self.data

    def _extract_formula_hints(self, wikitext: str) -> list[str]:
        """从 wikitext 中提取可能的公式线索。"""
        hints = []
        # 查找常见公式关键词
        keywords = ["伤害", "攻击", "防御", "公式", "倍率", "计算"]
        for kw in keywords:
            if kw in wikitext:
                # 提取包含关键词的行
                for line in wikitext.split("\n"):
                    if kw in line and len(line.strip()) < 200:
                        hints.append(line.strip())
        return hints[:20]
