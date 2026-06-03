#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""github_upload_module 提交签名行为测试。"""

import unittest
from unittest.mock import patch

from scripts.tools import github_upload_module as upload


class TestCommitSigningConfig(unittest.TestCase):
    def test_gpgsign_true_does_not_need_dash_s(self):
        cfg = upload.SigningConfig(gpgsign="true", signingkey="ABCD", gpg_format="ssh")
        self.assertEqual(upload.commit_extra_args(cfg), [])

    def test_signingkey_without_gpgsign_uses_dash_s(self):
        cfg = upload.SigningConfig(gpgsign=None, signingkey="key.pub", gpg_format="ssh")
        self.assertEqual(upload.commit_extra_args(cfg), ["-S"])

    def test_unconfigured_has_no_extra_args(self):
        cfg = upload.SigningConfig(gpgsign=None, signingkey=None, gpg_format=None)
        self.assertEqual(upload.commit_extra_args(cfg), [])
        self.assertFalse(upload.is_signing_configured(cfg))

    def test_status_message_mentions_verified_when_configured(self):
        cfg = upload.SigningConfig(gpgsign="true", signingkey="k", gpg_format="ssh")
        self.assertIn("Verified", upload.signing_status_message(cfg))

    def test_status_message_hints_setup_when_unconfigured(self):
        cfg = upload.SigningConfig(gpgsign=None, signingkey=None, gpg_format=None)
        self.assertIn("commit.gpgsign", upload.signing_status_message(cfg))


class TestCommitWithMessage(unittest.TestCase):
    def test_commit_passes_dash_s_when_signingkey_configured(self):
        cfg = upload.SigningConfig(gpgsign=None, signingkey="~/.ssh/id_ed25519.pub", gpg_format="ssh")

        with patch.object(upload, "run_git") as mock_git:
            with patch.object(upload, "resolve_signing_config", return_value=cfg):
                upload._commit_with_message("v1.0.0: test")

        mock_git.assert_called_once()
        args = mock_git.call_args[0][0]
        self.assertEqual(args[:2], ["commit", "-S"])


class TestPreflightUpload(unittest.TestCase):
    def test_rebase_in_progress_fails_check(self):
        mock_path = unittest.mock.MagicMock()
        mock_path.is_dir.return_value = True
        with patch.object(upload, "_repo_root", return_value="."):
            with patch.object(upload, "_git_dir", return_value=mock_path):
                with patch.object(upload, "_is_rebase_in_progress", return_value=True):
                    with patch.object(upload, "_is_merge_in_progress", return_value=False):
                        self.assertFalse(upload.preflight_upload(check_only=True))


class TestPreCommitLintDetection(unittest.TestCase):
    def test_format_failed_does_not_count_as_lint_error(self):
        output = (
            "ruff-lint................................................................Passed\n"
            "ruff-format..............................................................Failed\n"
        )
        self.assertFalse(upload._pre_commit_has_lint_errors(output))

    def test_lint_failed_is_detected(self):
        output = "ruff-lint................................................................Failed\n"
        self.assertTrue(upload._pre_commit_has_lint_errors(output))


class TestGitPathNormalization(unittest.TestCase):
    def test_unquote_octal_porcelain_path(self):
        raw = '"docs/\\344\\270\\212\\344\\274\\240\\350\\204\\232\\346\\234\\254.md"'
        self.assertEqual(
            upload._unquote_git_path(raw),
            "docs/上传脚本.md",
        )

    def test_normalize_does_not_split_octal_with_path(self):
        raw = '"docs/\\344\\274\\232\\350\\257\\235\\346\\216\\245\\347\\273\\255\\346\\211\\213\\345\\206\\214.md"'
        self.assertEqual(
            upload._normalize_change_path(raw),
            "docs/会话接续手册.md",
        )


if __name__ == "__main__":
    unittest.main()
