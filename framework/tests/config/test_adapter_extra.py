# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
import json
from pathlib import Path

from calc_framework.config.adapter import AdapterPackage


def _write_meta(adapter_dir: Path, meta: dict) -> Path:
    meta_path = adapter_dir / "meta.json"

    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    return meta_path


def _write_dag(adapter_dir: Path, relative_path: str) -> Path:
    dag_path = adapter_dir / relative_path

    dag_path.parent.mkdir(parents=True, exist_ok=True)

    dag_path.write_text(
        json.dumps(
            {
                "schema_version": "dag-v1",
                "name": "test",
                "variables": {},
                "nodes": {
                    "c": {"type": "const", "value": 42},
                },
                "outputs": {"answer": {"node": "c", "label": "Answer"}},
            }
        ),
        encoding="utf-8",
    )

    return dag_path


def _write_fn_file(adapter_dir: Path, relative_path: str, content: str) -> Path:
    fn_path = adapter_dir / relative_path

    fn_path.parent.mkdir(parents=True, exist_ok=True)

    fn_path.write_text(content, encoding="utf-8")

    return fn_path


class TestAdapterPackageExtra:
    def test_register_function(self, tmp_path: Path):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "dag/formula.dag.json",
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        pkg = AdapterPackage(tmp_path)

        pkg.register_function("triple", lambda x: x * 3)

        dag_data = {
            "schema_version": "dag-v1",
            "name": "custom_fn_test",
            "variables": {},
            "nodes": {
                "result": {"type": "expr", "expr": "triple(5)"},
            },
            "outputs": {"answer": {"node": "result", "label": "Answer"}},
        }

        from calc_framework.dag.service import DAGService

        svc = DAGService.from_dict(dag_data)

        result = svc.evaluate({})

        assert result.outputs["answer"] == 15.0

    def test_attr_schema_file_not_found_warns(self, tmp_path: Path, caplog):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "dag/formula.dag.json",
                "attr_schema": "nonexistent_schema.json",
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        pkg = AdapterPackage(tmp_path)

        assert "attr_schema 文件未找到" in caplog.text

        assert pkg.attr_schema is None

    def test_attr_schema_load_exception_warns(self, tmp_path: Path, caplog):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "dag/formula.dag.json",
                "attr_schema": "bad_schema.json",
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        bad_schema = tmp_path / "bad_schema.json"

        bad_schema.write_text("{invalid json content", encoding="utf-8")

        AdapterPackage(tmp_path)

        assert "加载 attr_schema 失败" in caplog.text

    def test_load_function_file_not_found_warns(self, tmp_path: Path, caplog):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "dag/formula.dag.json",
                "functions": {"my_func": "nonexistent.py"},
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        AdapterPackage(tmp_path)

        assert "加载自定义函数失败" in caplog.text

        assert "文件未找到" in caplog.text

    def test_load_function_file_import_error_warns(self, tmp_path: Path, caplog):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "dag/formula.dag.json",
                "functions": {"my_func": "functions.py"},
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        _write_fn_file(tmp_path, "functions.py", "def my_func(:\n    pass\n")

        AdapterPackage(tmp_path)

        assert "加载自定义函数失败" in caplog.text

    def test_load_function_file_non_callable_warns(self, tmp_path: Path, caplog):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "dag/formula.dag.json",
                "functions": {"my_func": "functions.py"},
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        _write_fn_file(tmp_path, "functions.py", "my_func = 42\n")

        AdapterPackage(tmp_path)

        assert "加载自定义函数失败" in caplog.text
