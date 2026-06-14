# SPDX-License-Identifier: AGPL-3.0
"""AdapterWatcher 热加载单元测试。"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

from calc_framework.config.manager import AdapterManager
from calc_framework.config.watcher import AdapterWatcher


@pytest.fixture
def temp_adapter():
    """创建一个临时适配包目录。"""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "test_hot_reload"
        base.mkdir()
        meta = {
            "schema_version": "dag-v1",
            "name": "test_hot_reload",
            "entry_dag": "test.dag.json",
            "description": "热加载测试",
        }
        dag = {
            "schema_version": "dag-v1",
            "name": "test",
            "nodes": {"dummy": {"type": "const", "value": 0}},
            "outputs": {"dummy": {"node": "dummy", "label": "dummy"}},
        }
        (base / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        (base / "test.dag.json").write_text(json.dumps(dag), encoding="utf-8")
        yield base


class TestAdapterWatcher:
    def test_watcher_starts_and_stops(self):
        mgr = AdapterManager()
        watcher = AdapterWatcher(mgr, poll_interval=0.5)
        assert not watcher.is_running
        watcher.start()
        assert watcher.is_running
        watcher.stop()
        assert not watcher.is_running

    def test_watcher_detects_file_change(self, temp_adapter: Path):
        mgr = AdapterManager(adapters_dir=temp_adapter.parent)
        reloaded: list[str] = []

        def on_reload(name, pkg):
            reloaded.append(name)

        watcher = AdapterWatcher(mgr, on_reload=on_reload, poll_interval=0.3)
        watcher.start()

        # 初始快照
        time.sleep(0.5)
        watcher._check_adapters()
        before = len(reloaded)

        # 修改文件
        dag_path = temp_adapter / "test.dag.json"
        dag = json.loads(dag_path.read_text(encoding="utf-8"))
        dag["nodes"]["dummy"]["value"] = 42
        dag_path.write_text(json.dumps(dag), encoding="utf-8")
        # 等待文件系统刷新
        time.sleep(0.3)

        try:
            watcher._check_adapters()
            assert len(reloaded) > before
        finally:
            watcher.stop()

    def test_watcher_ignores_unchanged(self, temp_adapter: Path):
        mgr = AdapterManager(adapters_dir=temp_adapter.parent)
        reloaded: list[str] = []

        def on_reload(name, pkg):
            reloaded.append(name)

        watcher = AdapterWatcher(mgr, on_reload=on_reload, poll_interval=0.3)
        watcher.start()
        time.sleep(0.5)
        watcher._check_adapters()
        before = len(reloaded)

        try:
            # 不修改文件，不应触发重载
            watcher._check_adapters()
            assert len(reloaded) == before
        finally:
            watcher.stop()

    def test_watcher_detects_new_file(self, temp_adapter: Path):
        mgr = AdapterManager(adapters_dir=temp_adapter.parent)
        reloaded: list[str] = []

        def on_reload(name, pkg):
            reloaded.append(name)

        watcher = AdapterWatcher(mgr, on_reload=on_reload, poll_interval=0.3)
        watcher.start()
        time.sleep(0.5)
        watcher._check_adapters()
        before = len(reloaded)

        # 新增文件
        (temp_adapter / "new_func.py").write_text("def new_func(): pass\n", encoding="utf-8")
        time.sleep(0.3)

        try:
            watcher._check_adapters()
            assert len(reloaded) > before
        finally:
            watcher.stop()

    def test_watcher_reloads_adapter_in_manager(self, temp_adapter: Path):
        """验证热加载后 AdapterManager 返回新版适配包。"""
        mgr = AdapterManager(adapters_dir=temp_adapter.parent)

        # 根据 meta.json 中的 name
        pkg_name = "test_hot_reload" if "test_hot_reload" in mgr.names else mgr.names[0]
        pkg_name = mgr.names[0]

        watcher = AdapterWatcher(mgr, poll_interval=0.3)
        watcher.start()
        time.sleep(0.5)
        watcher._check_adapters()

        # 修改 DAG
        dag_path = temp_adapter / "test.dag.json"
        dag = json.loads(dag_path.read_text(encoding="utf-8"))
        dag["name"] = "modified_dag"
        dag_path.write_text(json.dumps(dag), encoding="utf-8")
        time.sleep(0.3)

        try:
            watcher._check_adapters()
            # 重载后读取
            pkg = mgr.reload(pkg_name)
            assert pkg.dag_service.dag.name == "modified_dag"
        finally:
            watcher.stop()
