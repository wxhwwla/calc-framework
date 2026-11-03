# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配器生成与脚手架。"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from calc_framework.config.scaffold import AdapterScaffoldConfig, scaffold_adapter_directory
from calc_framework.dag.serializer import dag_from_dict, dag_to_dict

from tools.generator.engine import GeneratorEngine

from .safety import ProjectScope, ScopeError
from .spec import normalize_spec


class BuildError(ValueError):
    """适配器生成/脚手架错误。"""


def generate_adapter(
    scope: ProjectScope,
    *,
    adapter_id: str,
    display_name: str = "",
    game: str = "",
    template_id: str | None = None,
    variables: list[dict[str, Any]] | None = None,
    formula_steps: list[dict[str, Any]] | None = None,
    outputs: list[dict[str, Any]] | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """用声明式规格生成适配器包。

    Args:
        scope: 项目作用域。
        adapter_id: 适配器目录名。
        display_name: 显示名称。
        game: 游戏名称。
        template_id: 可选模板目录名。
        variables: 变量声明。
        formula_steps: 公式步骤。
        outputs: 输出声明。
        dry_run: 为 True 时只返回文件内容，不写盘。
        overwrite: 是否允许覆盖已存在目录中的文件。

    Returns:
        ``{ok, adapter_id, files, warnings, dry_run, adapter_dir}``。

    Raises:
        BuildError: 规格非法、模板不存在或目标已存在。
    """
    target = scope.adapter_dir(adapter_id)
    _check_target(target, overwrite)

    spec = normalize_spec(variables=variables, formula_steps=formula_steps, outputs=outputs)
    engine = GeneratorEngine(adapters_dir=scope.adapters_dir)
    try:
        files = engine.generate(
            template_id,
            adapter_id,
            variables=[item.to_generator_dict() for item in spec.variables],
            formula_steps=[item.to_generator_dict() for item in spec.steps],
            outputs=[item.to_generator_dict() for item in spec.outputs],
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise BuildError(f"生成失败: {exc}") from exc

    if not files:
        raise BuildError("生成器未返回任何文件（请检查公式步骤）")

    files = _patch_display_names(files, display_name=display_name or adapter_id, game=game)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "adapter_id": adapter_id,
            "files": dict(files),
            "warnings": list(spec.warnings),
        }

    _write_files(scope, target, files, overwrite=overwrite)
    return {
        "ok": True,
        "dry_run": False,
        "adapter_id": adapter_id,
        "adapter_dir": _relative(scope, target),
        "files": sorted(files),
        "warnings": list(spec.warnings),
    }


def scaffold_adapter(
    scope: ProjectScope,
    *,
    adapter_id: str,
    display_name: str = "",
    game: str = "",
    description: str = "",
    dag: dict[str, Any],
    overwrite: bool = False,
) -> dict[str, Any]:
    """用完整 DAG JSON 创建适配器包。

    Args:
        scope: 项目作用域。
        adapter_id: 适配器目录名。
        display_name: 显示名称。
        game: 游戏名称。
        description: 适配器描述。
        dag: 完整 DAG JSON 字典。
        overwrite: 是否允许覆盖已存在目录中的文件。

    Returns:
        ``{ok, adapter_id, adapter_dir, files}``。

    Raises:
        BuildError: DAG 非法或目标已存在。
    """
    target = scope.adapter_dir(adapter_id)
    _check_target(target, overwrite)

    try:
        graph = dag_from_dict(dag)
    except Exception as exc:
        raise BuildError(f"DAG 校验失败: {exc}") from exc

    tmp_dir = scope.resolve(".calc-mcp/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_dag = tmp_dir / f"{uuid.uuid4().hex}.dag.json"
    tmp_dag.write_text(json.dumps(dag_to_dict(graph), ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        result = scaffold_adapter_directory(
            AdapterScaffoldConfig(
                name=display_name or adapter_id,
                adapter_id=adapter_id,
                game=game or display_name or adapter_id,
                description=description,
                dag_file=tmp_dag,
                output_root=scope.adapters_dir,
            )
        )
    finally:
        tmp_dag.unlink(missing_ok=True)

    if not result.success:
        raise BuildError(f"脚手架失败: {result.error}")

    prefix = adapter_id + "/"
    files = sorted(item[len(prefix) :] if item.startswith(prefix) else item for item in result.files)
    return {
        "ok": True,
        "adapter_id": adapter_id,
        "adapter_dir": _relative(scope, target),
        "files": files,
    }


def _patch_display_names(files: dict[str, str], *, display_name: str, game: str) -> dict[str, str]:
    patched = dict(files)

    if "meta.json" in patched:
        meta = json.loads(patched["meta.json"])
        meta["name"] = display_name
        meta["game"] = game or display_name
        meta["description"] = f"自动生成的计算器: {display_name}"
        patched["meta.json"] = json.dumps(meta, ensure_ascii=False, indent=2)

    dag_key = next((key for key in patched if key.endswith(".dag.json")), "")
    if dag_key:
        dag = json.loads(patched[dag_key])
        dag["name"] = display_name
        dag["description"] = f"自动生成的 {display_name} 伤害公式"
        patched[dag_key] = json.dumps(dag, ensure_ascii=False, indent=2)

    if "ui/layout.json" in patched:
        layout = json.loads(patched["ui/layout.json"])
        layout["name"] = f"{display_name}计算表"
        patched["ui/layout.json"] = json.dumps(layout, ensure_ascii=False, indent=2)

    return patched


def _write_files(scope: ProjectScope, target: Path, files: dict[str, str], *, overwrite: bool) -> None:
    for rel, content in files.items():
        candidate = (target / rel).resolve()
        if not candidate.is_relative_to(target):
            raise ScopeError(f"生成文件路径越界: {rel!r}")
        scope.write_text(candidate, content, overwrite=overwrite)


def _check_target(target: Path, overwrite: bool) -> None:
    if target.exists() and any(target.iterdir()) and not overwrite:
        raise BuildError(f"适配器目录已存在（如需覆盖请设置 overwrite=true）: {target.name}")


def _relative(scope: ProjectScope, path: Path) -> str:
    return path.resolve().relative_to(scope.root).as_posix()
