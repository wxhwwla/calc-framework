# SPDX-License-Identifier: AGPL-3.0
"""包元数据 — 模板包标识与版本信息。

使用时全局替换 DISPLAY_NAME、VERSION、MIN_FRAMEWORK_VERSION。
"""

from __future__ import annotations

DISPLAY_NAME: str = "TEMPLATE"
"""游戏显示名称，如 '明日方舟'、'终末地'。"""

VERSION: str = "0.1.0"
"""适配包版本号，遵循 semver。"""

MIN_FRAMEWORK_VERSION: str = "0.1.0"
"""所需 calc-framework 的最低版本。"""
