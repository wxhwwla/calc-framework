#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""github_upload_module 提交签名行为测试。"""

import unittest
from pathlib import Path
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

    def test_lint_auto_fix_only_is_not_hard_error(self):
        output = (
            "ruff-lint................................................................Failed\n"
            "- hook id: ruff\n"
            "- exit code: 1\n"
            "- files were modified by this hook\n"
            "\n"
            "Found 1 error (1 fixed, 0 remaining).\n"
        )
        self.assertFalse(upload._pre_commit_has_lint_errors(output))


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


class TestRollbackUploadDraft(unittest.TestCase):
    def test_rollback_restores_version_and_removes_summary(self):
        import tempfile

        from scripts import upload_meta as meta

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "_version.py"
            path.write_text(
                """# ==============================================================

_SUMMARY_MARKER_BEGIN = "# --- BEGIN UPLOAD_SUMMARY ---"
_SUMMARY_MARKER_END = "# --- END UPLOAD_SUMMARY ---"
_UPLOAD_SUMMARY_BEGIN = _SUMMARY_MARKER_BEGIN
_UPLOAD_SUMMARY_END = _SUMMARY_MARKER_END
SUMMARY_BEGIN = _UPLOAD_SUMMARY_BEGIN
SUMMARY_END = _UPLOAD_SUMMARY_END
_VERSION_PATTERN = re.compile(
    r'^(_VERSION\\s*=\\s*["\\'])([^"\\']+)(["\\'])',
    re.MULTILINE,
)
_VERSION = "1.0.0"
""",
                encoding="utf-8",
            )
            meta.write_version(path, "1.0.1")
            meta.write_summary_block(path, "t", ["a"])
            upload._rollback_upload_draft(
                path,
                meta,
                saved_version="1.0.0",
                restore_version=True,
            )
            self.assertEqual(meta.read_version(path), "1.0.0")
            self.assertNotIn("# TITLE: t", path.read_text(encoding="utf-8"))


class TestDualVersionReleaseMerge(unittest.TestCase):
    def setUp(self):
        from scripts.upload_meta import please_read_me_path

        self.readme = please_read_me_path()

    def test_should_merge_when_both_versions_differ(self):
        class FakeMeta:
            @staticmethod
            def read_version(_path):
                return "3.22.0"

            @staticmethod
            def read_exe_version(_path):
                return "0.7.0"

        def fake_run_git(args, **kwargs):
            if args[:2] == ["rev-parse", "--verify"]:
                return 0, "abc", ""
            if args[0] == "show":
                return 0, '_VERSION = "3.21.4"\n_EXE_VERSION = "0.6.0-beta"\n', ""
            return 1, "", ""

        with patch.object(upload, "run_git", side_effect=fake_run_git):
            self.assertTrue(upload._should_merge_to_release(FakeMeta(), self.readme))

    def test_should_not_merge_when_only_project_version_differs(self):
        class FakeMeta:
            @staticmethod
            def read_version(_path):
                return "3.22.0"

            @staticmethod
            def read_exe_version(_path):
                return "0.6.0-beta"

        def fake_run_git(args, **kwargs):
            if args[:2] == ["rev-parse", "--verify"]:
                return 0, "abc", ""
            if args[0] == "show":
                return 0, '_VERSION = "3.21.4"\n_EXE_VERSION = "0.6.0-beta"\n', ""
            return 1, "", ""

        with patch.object(upload, "run_git", side_effect=fake_run_git):
            self.assertFalse(upload._should_merge_to_release(FakeMeta(), self.readme))


if __name__ == "__main__":
    unittest.main()
