#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""发布目录布局：exe 与游戏数据分文件，供打包脚本与 path_utils 共用约定。"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_PKG = Path(__file__).resolve().parent.parent
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))

from release_bundle.release_layout import (  # noqa: E402
    LICENSE_FILES,
    RELEASE_APP_NAME,
    RELEASE_DATA_FILES,
    stage_release_folder,
)
from data.loader import CHARACTERS_JSON_PATH, EQUIPMENTS_JSON_PATH, WEAPONS_JSON_PATH
from utils.path_utils import get_resource_path


class TestReleaseLayout(unittest.TestCase):
    def test_pypi_packaging_not_shadowed_when_project_on_path(self):
        """PyInstaller 需要 ``packaging.requirements``；本地包不得占用顶层名 packaging。"""
        import importlib.util

        _PKG = Path(__file__).resolve().parent.parent
        if str(_PKG) not in sys.path:
            sys.path.insert(0, str(_PKG))
        import release_bundle.release_layout  # noqa: F401

        spec = importlib.util.find_spec("packaging.requirements")
        self.assertIsNotNone(spec, "packaging.requirements 应解析到 PyPI packaging，而非本地目录")

    def test_release_data_files_match_loader_paths(self):
        rel_paths = {rel for rel, _ in RELEASE_DATA_FILES}
        self.assertIn(CHARACTERS_JSON_PATH, rel_paths)
        self.assertIn(WEAPONS_JSON_PATH, rel_paths)
        self.assertIn(EQUIPMENTS_JSON_PATH, rel_paths)

    def test_release_readme_mentions_search_output_and_parallel_workers(self):
        from release_bundle.release_layout import _release_readme_text

        text = _release_readme_text(exe_version="0.4.0-beta", package_version="1.17.0")
        self.assertIn("search_output", text)
        self.assertIn("并行线程", text)
        self.assertIn("EXE v0.4.0-beta", text)
        self.assertIn("build.py", text)

    def test_stage_release_folder_copies_json_and_licenses(self):
        repo_root = _PKG.parent
        with tempfile.TemporaryDirectory() as tmp:
            release_root = Path(tmp) / RELEASE_APP_NAME
            stage_release_folder(release_root, project_root=_PKG, repo_root=repo_root)
            for rel, _ in RELEASE_DATA_FILES:
                target = release_root / rel
                self.assertTrue(target.is_file(), f"缺少数据文件: {target}")
                with target.open(encoding="utf-8") as f:
                    data = json.load(f)
                self.assertIsInstance(data, list)
                self.assertGreater(len(data), 0)
            for rel, _ in LICENSE_FILES:
                self.assertTrue((release_root / rel).is_file(), f"缺少许可文件: {rel}")
            self.assertTrue((release_root / "发布说明.txt").is_file())

    def test_frozen_exe_loads_json_from_sibling_data_tree(self):
        src_chars = get_resource_path(CHARACTERS_JSON_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_exe = root / "终末地伤害计算器.exe"
            fake_exe.write_bytes(b"MZ")
            dest = root / CHARACTERS_JSON_PATH
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_chars, dest)

            with patch.object(sys, "frozen", True, create=True), patch.object(
                sys, "executable", str(fake_exe)
            ):
                resolved = get_resource_path(CHARACTERS_JSON_PATH)

            self.assertEqual(resolved, dest)
            self.assertTrue(resolved.is_file())


if __name__ == "__main__":
    unittest.main()
