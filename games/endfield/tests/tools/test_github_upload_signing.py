#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""github_upload_module 提交签名行为测试。"""

import unittest
from unittest.mock import patch

import github_upload_module as upload


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


if __name__ == "__main__":
    unittest.main()
