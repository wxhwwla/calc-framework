#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""发布目录布局：exe 与游戏数据分文件，供打包脚本和 path_utils 共用约定。"""


import shutilimport sysimport tempfileimport unittestfrom pathlib import Pathfrom unittest.mock import patchfrom games.endfield.data_loading.loader import CHARACTERS_JSON_PATH, EQUIPMENTS_JSON_PATH, WEAPONS_JSON_PATHfrom games.endfield.tests.conftest import GAMES_END, REPO_ROOTfrom release_bundle.release_layout import (    LICENSE_FILES,    RELEASE_DATA_FILES,    release_dir_from_dist,    stage_release_folder,    target_app_name,)from utils.path_utils import get_resource_pathclass TestReleaseLayout(unittest.TestCase):
    def test_pypi_packaging_not_shadowed_when_project_on_path(self):
        import importlib.util
        _PKG = GAMES_END
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

    def test_target_app_names(self):
        self.assertEqual(target_app_name("calculator"), "终末地伤害计算器")
        self.assertEqual(target_app_name("designer"), "数据设计器")

    def test_stage_release_folder_copies_json_and_licenses_calculator(self):
        repo_root = REPO_ROOT
        app_name = target_app_name("calculator")
        with tempfile.TemporaryDirectory() as tmp:
            release_root = Path(tmp) / app_name
            stage_release_folder(release_root, project_root=REPO_ROOT, repo_root=repo_root, target="calculator")
            for rel, _ in RELEASE_DATA_FILES:
                target = release_root / rel
                self.assertTrue(target.is_file(), f"缺少数据文件: {target}")
            for rel, _ in LICENSE_FILES:
                self.assertTrue((release_root / rel).is_file(), f"缺少许可文件: {rel}")

    def test_stage_release_folder_copies_json_and_licenses_designer(self):
        repo_root = REPO_ROOT
        app_name = target_app_name("designer")
        with tempfile.TemporaryDirectory() as tmp:
            release_root = Path(tmp) / app_name
            stage_release_folder(release_root, project_root=REPO_ROOT, repo_root=repo_root, target="designer")
            for rel, _ in RELEASE_DATA_FILES:
                target = release_root / rel
                self.assertTrue(target.is_file(), f"缺少数据文件: {target}")
            for rel, _ in LICENSE_FILES:
                self.assertTrue((release_root / rel).is_file(), f"缺少许可文件: {rel}")

    def test_release_dir_from_dist(self):
        dist_dir = Path("/fake/dist")
        self.assertEqual(
            release_dir_from_dist(dist_dir, target="calculator"),
            dist_dir / "终末地伤害计算器",
        )
        self.assertEqual(
            release_dir_from_dist(dist_dir, target="designer"),
            dist_dir / "数据设计器",
        )

    def test_frozen_exe_loads_json_from_sibling_data_tree(self):
        src_chars = get_resource_path(CHARACTERS_JSON_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_exe = root / "终末地伤害计算器.exe"
            fake_exe.write_bytes(b"MZ")
            dest = root / CHARACTERS_JSON_PATH
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_chars, dest)
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(fake_exe)):
                resolved = get_resource_path(CHARACTERS_JSON_PATH)
            self.assertEqual(resolved, dest)
            self.assertTrue(resolved.is_file())


if __name__ == "__main__":
    unittest.main()
