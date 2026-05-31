#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""仓库 .gitignore 应覆盖常见本地产物，且不含错误条目。"""

import unittest

from games.endfield.tests.conftest import REPO_ROOT

GITIGNORE = REPO_ROOT / ".gitignore"

# 必须忽略的片段（行为：这些路径不应被误提交）
REQUIRED_PATTERNS = [
    "__pycache__/",
    "tools/bwiki_scout/output/",
    ".pytest_cache/",
    "*.exe",
    "git_key.txt",
    ".git-upload-msg.txt",
    "dist/",
    "skills-lock.json",
]

# 不应出现在 .gitignore 中（无意义或误导）
FORBIDDEN_PATTERNS = [
    ".git/",
]


class TestGitignoreContract(unittest.TestCase):
    def test_gitignore_exists(self):
        self.assertTrue(GITIGNORE.is_file(), f"缺少 {GITIGNORE}")

    def test_required_ignore_patterns(self):
        text = GITIGNORE.read_text(encoding="utf-8")
        for pattern in REQUIRED_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, text, f".gitignore 应包含 {pattern!r}")

    def test_no_forbidden_patterns(self):
        text = GITIGNORE.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertNotIn(pattern, text, f".gitignore 不应包含 {pattern!r}")


if __name__ == "__main__":
    unittest.main()
