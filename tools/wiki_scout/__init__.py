# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""Wiki Scout — 模块化 Wiki 数据采集工具。

用法:
    from tools.wiki_scout import Fetcher, get_provider, list_providers

    fetcher = Fetcher("tools/wiki_scout/output/.cache")
    provider = get_provider("wjdlglr")
    data = provider.run(fetcher)

旧版 MediaWiki 工具:
    from tools.wiki_scout import MediaWikiClient, detect_wiki_type, get_api_url
    from tools.wiki_scout.providers import BWIKIExtractor
"""

from . import providers
from .client import MediaWikiClient, detect_wiki_type, get_api_url
from .fetcher import DEFAULT_USER_AGENT, Fetcher, FetchError
from .providers.base import BaseProvider
from .registry import get_provider, list_providers, register_provider

__all__ = [
    "DEFAULT_USER_AGENT",
    "BaseProvider",
    "FetchError",
    "Fetcher",
    "MediaWikiClient",
    "detect_wiki_type",
    "get_api_url",
    "get_provider",
    "list_providers",
    "providers",
    "register_provider",
]
