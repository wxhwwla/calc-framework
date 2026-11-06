# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""隐私披露、支持矩阵与第三方许可清单的文档契约测试。

对应审查项 R-16（AI 数据外发披露）、R-18（支持矩阵）与 R-19（许可清单）。
"""

from __future__ import annotations

import re
import unittest

from games.endfield.tests.conftest import REPO_ROOT

PRIVACY_DOC = REPO_ROOT / "docs" / "隐私与AI数据处理.md"
AI_DIALOG = REPO_ROOT / "web" / "frontend" / "src" / "components" / "calculator" / "AiRecommendDialog.tsx"
AI_BACKEND = REPO_ROOT / "web" / "backend" / "api" / "ai.py"
LOCALES = [
    REPO_ROOT / "web" / "frontend" / "src" / "i18n" / "locales" / "zh-CN.ts",
    REPO_ROOT / "web" / "frontend" / "src" / "i18n" / "locales" / "en.ts",
]
NOTICES = REPO_ROOT / "NOTICES.md"
READMES = [REPO_ROOT / "README.md", REPO_ROOT / "README_zh.md"]


class TestPrivacyDisclosure(unittest.TestCase):
    def test_privacy_doc_exists_and_covers_required_topics(self) -> None:
        self.assertTrue(PRIVACY_DOC.is_file(), "缺少 docs/隐私与AI数据处理.md")
        text = PRIVACY_DOC.read_text(encoding="utf-8")
        for keyword in ("第三方", "API Key", "保留", "删除"):
            self.assertIn(keyword, text, f"隐私文档缺少主题: {keyword}")

    def test_ai_dialog_shows_privacy_notice(self) -> None:
        source = AI_DIALOG.read_text(encoding="utf-8")
        self.assertIn("ai.privacyNotice", source)

    def test_locales_define_privacy_notice(self) -> None:
        for locale in LOCALES:
            self.assertIn("privacyNotice", locale.read_text(encoding="utf-8"), locale.name)

    def test_backend_never_logs_api_keys_or_prompts(self) -> None:
        source = AI_BACKEND.read_text(encoding="utf-8")
        logger_lines = [line for line in source.splitlines() if re.match(r"\s*logger\.", line)]
        self.assertTrue(logger_lines, "ai.py 应使用 logger 而非静默异常")
        for line in logger_lines:
            for forbidden in ("api_key", "Authorization", "messages"):
                self.assertNotIn(forbidden, line, f"日志可能泄露敏感数据: {line.strip()}")

    def test_web_readme_links_privacy_doc(self) -> None:
        readme = (REPO_ROOT / "web" / "README.md").read_text(encoding="utf-8")
        self.assertIn("隐私与AI数据处理.md", readme)


class TestSupportMatrix(unittest.TestCase):
    def test_readmes_publish_support_matrix(self) -> None:
        for readme in READMES:
            text = readme.read_text(encoding="utf-8")
            self.assertTrue(
                "支持矩阵" in text or "Support Matrix" in text,
                f"{readme.name} 缺少支持矩阵",
            )

    def test_matrix_names_all_games_and_non_goals(self) -> None:
        text = READMES[1].read_text(encoding="utf-8")
        for keyword in ("终末地", "明日方舟", "拉格朗日", "非目标"):
            self.assertIn(keyword, text, f"支持矩阵缺少: {keyword}")


class TestThirdPartyNotices(unittest.TestCase):
    def test_notices_cover_web_frontend_and_rust_dependencies(self) -> None:
        text = NOTICES.read_text(encoding="utf-8")
        for dependency in ("httpx", "httpcore", "python-multipart", "a2wsgi", "React", "MUI", "PyO3"):
            self.assertIn(dependency, text, f"NOTICES 缺少直接依赖: {dependency}")


if __name__ == "__main__":
    unittest.main()
