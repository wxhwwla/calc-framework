# SPDX-License-Identifier: AGPL-3.0
"""FileWatcher 单文件监视器单元测试。"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from calc_framework.config.file_watcher import FileWatcher


class TestFileWatcher:
    def test_start_and_stop(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            f.write(b"{}")

            tmp = Path(f.name)

        try:
            calls: list[str] = []

            watcher = FileWatcher(tmp, on_change=lambda: calls.append("x"), poll_interval=0.3)

            assert not watcher.is_running

            watcher.start()

            assert watcher.is_running

            assert watcher.path == tmp

            watcher.stop()

            assert not watcher.is_running

        finally:
            tmp.unlink(missing_ok=True)

    def test_detects_file_change(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"value": 0}, f)

            tmp = Path(f.name)

        try:
            detected = 0

            def on_change():
                nonlocal detected

                detected += 1

            watcher = FileWatcher(tmp, on_change=on_change, poll_interval=0.3)
            watcher.start()
            time.sleep(1.0)  # 等足初始轮询

            # 修改文件
            tmp.write_text(json.dumps({"value": 1}), encoding="utf-8")
            time.sleep(1.5)  # Windows mtime 精度较低，需足够等待

            try:
                assert detected >= 1, f"预期检测到变化，实际 detected={detected}"
            finally:
                watcher.stop()
        finally:
            tmp.unlink(missing_ok=True)

    def test_ignores_unchanged(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"value": 0}, f)
            tmp = Path(f.name)
        try:
            detected = 0

            def on_change():
                nonlocal detected
                detected += 1

            watcher = FileWatcher(tmp, on_change=on_change, poll_interval=0.3)
            watcher.start()
            time.sleep(1.0)  # 等足轮询周期

            try:
                assert detected == 0, f"未修改不应触发回调，实际 detected={detected}"
            finally:
                watcher.stop()

        finally:
            tmp.unlink(missing_ok=True)

    def test_multiple_changes(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"value": 0}, f)
            tmp = Path(f.name)
        try:
            detected = 0

            def on_change():
                nonlocal detected
                detected += 1

            watcher = FileWatcher(tmp, on_change=on_change, poll_interval=0.2)
            watcher.start()
            time.sleep(0.5)  # 等足初始轮询

            tmp.write_text(json.dumps({"value": 1}), encoding="utf-8")
            time.sleep(1.0)
            tmp.write_text(json.dumps({"value": 2}), encoding="utf-8")
            time.sleep(1.0)
            tmp.write_text(json.dumps({"value": 3}), encoding="utf-8")
            time.sleep(1.0)

            try:
                assert detected >= 2, f"3 次修改应触发至少 2 次，实际 detected={detected}"
            finally:
                watcher.stop()

        finally:
            tmp.unlink(missing_ok=True)

    def test_poll_interval_clamped(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)

        try:
            watcher = FileWatcher(tmp, on_change=lambda: None, poll_interval=0.1)

            assert watcher._poll_interval == 0.5  # 被 clamp 到最小值

        finally:
            tmp.unlink(missing_ok=True)

    def test_double_start_ignored(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp = Path(f.name)
        try:
            watcher = FileWatcher(tmp, on_change=lambda: None, poll_interval=0.3)
            watcher.start()
            watcher.start()  # 第二次 start 应无效果，不抛异常
            assert watcher.is_running
            watcher.stop()
        finally:
            tmp.unlink(missing_ok=True)

    def test_read_mtime_handles_missing(self):
        """不存在的文件应返回 0.0。"""
        watcher = FileWatcher(Path("nonexistent_file_xyz.json"), on_change=lambda: None)
        assert watcher._read_mtime() == 0.0
