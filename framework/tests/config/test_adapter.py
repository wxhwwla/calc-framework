# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""适配包加载器 — 单元测试。"""

import json
from pathlib import Path

import pytest

from calc_framework.config.adapter import (
    AdapterNotFoundError,
    AdapterPackage,
    InvalidMetaError,
)


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


class TestAdapterPackage:
    def test_loads_valid_adapter(self, tmp_path: Path):
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

        assert pkg.meta["name"] == "TestGame"

        assert pkg.meta["version"] == "1.0.0"

    def test_dag_service_can_evaluate(self, tmp_path: Path):
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

        result = pkg.dag_service.evaluate({})

        assert result.outputs["answer"] == 42.0

    def test_missing_meta_raises(self, tmp_path: Path):
        with pytest.raises(AdapterNotFoundError, match=r"meta\.json"):
            AdapterPackage(tmp_path)

    def test_meta_without_entry_dag_raises(self, tmp_path: Path):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "",
            },
        )

        with pytest.raises(InvalidMetaError, match="entry_dag"):
            AdapterPackage(tmp_path)

    def test_entry_dag_not_found_raises(self, tmp_path: Path):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v1",
                "entry_dag": "nonexistent.dag.json",
            },
        )

        with pytest.raises(AdapterNotFoundError, match="nonexistent"):
            AdapterPackage(tmp_path)

    def test_schema_version_mismatch_raises(self, tmp_path: Path):
        _write_meta(
            tmp_path,
            {
                "name": "TestGame",
                "game": "Test Game",
                "version": "1.0.0",
                "schema_version": "dag-v2",
                "entry_dag": "dag/formula.dag.json",
            },
        )

        _write_dag(tmp_path, "dag/formula.dag.json")

        with pytest.raises(InvalidMetaError, match="schema_version"):
            AdapterPackage(tmp_path)

    def test_strips_trailing_slash_from_path(self, tmp_path: Path):
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

        pkg = AdapterPackage(str(tmp_path) + "/")

        assert pkg.meta["name"] == "TestGame"

    def test_meta_property_is_copy_not_reference(self, tmp_path: Path):
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

        meta = pkg.meta

        meta["name"] = "modified"

        assert pkg.meta["name"] == "TestGame"
