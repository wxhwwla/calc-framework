"""发布/分享模块测试。"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from calc_framework.publish.catalog import build_catalog
from calc_framework.publish.schema import validate_against_schema, validate_package


class TestValidateSchema:
    def test_valid_meta_passes(self):
        data = {
            "schema_version": "adapter-v1",
            "name": "test",
            "dag_files": ["test.dag.json"],
            "description": "test adapter",
        }
        assert validate_against_schema(data) == []

    def test_missing_required(self):
        errors = validate_against_schema({"name": "test"})
        assert any("schema_version" in e for e in errors)
        assert any("dag_files" in e for e in errors)

    def test_invalid_schema_version(self):
        data = {
            "schema_version": "v2",
            "name": "test",
            "dag_files": ["test.dag.json"],
            "description": "test",
        }
        errors = validate_against_schema(data)
        assert len(errors) > 0

    def test_empty_name(self):
        data = {
            "schema_version": "adapter-v1",
            "name": "",
            "dag_files": ["test.dag.json"],
            "description": "test",
        }
        errors = validate_against_schema(data)
        assert any("name" in e for e in errors)

    def test_empty_dag_files(self):
        data = {
            "schema_version": "adapter-v1",
            "name": "test",
            "dag_files": [],
            "description": "test",
        }
        errors = validate_against_schema(data)
        assert any("dag_files" in e for e in errors)


class TestValidatePackage:
    def test_valid_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = {
                "schema_version": "adapter-v1",
                "name": "test_adapter",
                "dag_files": ["test.dag.json"],
                "description": "test",
            }
            Path(tmp, "meta.json").write_text(json.dumps(meta), encoding="utf-8")
            Path(tmp, "test.dag.json").write_text("{}", encoding="utf-8")
            errors = validate_package(tmp)
            assert errors == []

    def test_missing_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = validate_package(tmp)
            assert any("meta.json" in e for e in errors)

    def test_missing_dag_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = {
                "schema_version": "adapter-v1",
                "name": "test",
                "dag_files": ["missing.dag.json"],
                "description": "test",
            }
            Path(tmp, "meta.json").write_text(json.dumps(meta), encoding="utf-8")
            errors = validate_package(tmp)
            assert any("missing" in e for e in errors)


class TestBuildCatalog:
    def test_build_catalog_returns_html(self):
        html = build_catalog()
        assert "<!DOCTYPE html>" in html
        assert "适配器市场" in html

    def test_build_catalog_writes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_catalog(tmp)
            index = Path(tmp, "index.html")
            assert index.is_file()
            content = index.read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in content
