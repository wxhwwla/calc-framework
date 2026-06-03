# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout — 通用 Wiki 数据采集工具。

用法:
    from tools.wiki_scout import MediaWikiClient, detect_wiki_type, get_api_url
    from tools.wiki_scout.providers import BWIKIExtractor

    # 检测 Wiki 类型
    wiki_type = detect_wiki_type("https://wiki.biligame.com/arknights/")

    # 提取数据
    extractor = BWIKIExtractor("https://wiki.biligame.com/arknights/")
    data = extractor.extract()
    print(data.to_json())
"""

from .client import MediaWikiClient, detect_wiki_type, get_api_url

__all__ = [
    "MediaWikiClient",
    "detect_wiki_type",
    "get_api_url",
]
