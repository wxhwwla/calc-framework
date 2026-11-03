# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""MCP 适配器 .calcpack 导出与导入。"""

from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from tools.designer.exporter import export_calcpack as _export_calcpack_file

from .safety import ProjectScope, ScopeError
from .verify import validate_adapter

_MAX_PACK_BYTES = 64 * 1024 * 1024
_MAX_PACK_ENTRIES = 10_000


class PackageError(ValueError):
    """calcpack 导出/导入错误。"""


def export_calcpack(
    scope: ProjectScope,
    *,
    adapter_id: str,
    output_path: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """将适配包导出为 ``.calcpack``。

    Args:
        scope: 项目作用域。
        adapter_id: 适配器目录名。
        output_path: 输出路径（项目内相对路径），默认 ``dist/<adapter_id>.calcpack``。
        force: 校验失败时仍强制导出。

    Returns:
        ``{ok, adapter_id, path, size_bytes, files, warnings, validation}``。

    Raises:
        PackageError: 适配器无效（未设置 force）、文件缺失或路径越界。
    """
    try:
        target = scope.adapter_dir(adapter_id, must_exist=True)
        output = scope.resolve(output_path or f"dist/{adapter_id}.calcpack")
    except ScopeError as exc:
        raise PackageError(str(exc)) from exc

    if output.suffix.lower() != ".calcpack":
        output = output.with_suffix(".calcpack")

    validation = validate_adapter(scope, adapter_id)
    if not validation["valid"] and not force:
        messages = "; ".join(item["message"] for item in validation["errors"][:3])
        raise PackageError(f"适配器校验未通过（可设置 force=true 强制导出）: {messages}")

    meta = _read_json(target / "meta.json", "meta.json")
    dag_raw = _read_referenced(target, meta, "entry_dag", required=True)
    layout_raw = _read_referenced(target, meta, "ui_layout", required=True)
    attr_raw = _read_referenced(target, meta, "attr_schema", required=False)
    assert dag_raw is not None and layout_raw is not None  # required=True 已保证

    warnings: list[str] = []
    pack_meta = dict(meta)
    pack_meta["entry_dag"] = "dag/formula.dag.json"
    pack_meta["ui_layout"] = "ui/layout.json"
    if attr_raw is not None:
        pack_meta["attr_schema"] = "attr_schema.json"
    else:
        pack_meta.pop("attr_schema", None)

    if meta.get("functions"):
        warnings.append("calcpack 不包含 functions.py，导入后自定义函数将不可用")
        pack_meta.pop("functions", None)

    subgraphs = dag_raw.get("subgraphs") if isinstance(dag_raw.get("subgraphs"), dict) else None
    data_files = _read_data_files(target / "data", warnings)
    theme = _read_optional_json(target / "ui" / "theme.json", warnings)
    asset_files = _collect_assets(target, layout_raw, warnings)

    extra_json: dict[str, dict[str, Any]] = {}
    if attr_raw is not None:
        extra_json["attr_schema.json"] = attr_raw

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        _export_calcpack_file(
            output_path=output,
            meta=pack_meta,
            dag=dag_raw,
            layout=layout_raw,
            theme=theme,
            data_files=data_files or None,
            asset_files=asset_files or None,
            subgraphs=subgraphs,
            extra_json=extra_json or None,
        )
    except OSError as exc:
        raise PackageError(f"写入 .calcpack 失败: {exc}") from exc

    with zipfile.ZipFile(output) as zf:
        files = sorted(name for name in zf.namelist() if not name.endswith("/"))

    return {
        "ok": True,
        "adapter_id": adapter_id,
        "path": output.relative_to(scope.root).as_posix(),
        "size_bytes": output.stat().st_size,
        "files": files,
        "warnings": warnings,
        "validation": validation,
    }


def import_calcpack(
    scope: ProjectScope,
    *,
    calcpack_path: str,
    adapter_id: str,
) -> dict[str, Any]:
    """将 ``.calcpack`` 解压为适配器目录并自动校验。

    Args:
        scope: 项目作用域。
        calcpack_path: 包路径（项目内相对路径）。
        adapter_id: 目标适配器目录名。

    Returns:
        ``{ok, adapter_id, directory, files, validation}``。

    Raises:
        PackageError: 包不存在/损坏、包含越界条目或目标目录已存在。
    """
    try:
        source = scope.resolve(calcpack_path, must_exist=True)
        destination = scope.adapter_dir(adapter_id)
    except ScopeError as exc:
        raise PackageError(str(exc)) from exc

    if not source.is_file():
        raise PackageError(f".calcpack 不是文件: {calcpack_path}")
    if destination.exists():
        raise PackageError(f"适配器目录已存在（请换一个 adapter_id）: {adapter_id}")

    temp_root = scope.resolve(".calc-mcp/tmp")
    temp_dir = temp_root / uuid.uuid4().hex
    try:
        members = _extract_verified(source, temp_dir)
    except PackageError:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    except (OSError, zipfile.BadZipFile) as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise PackageError(f"读取 .calcpack 失败: {exc}") from exc

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(temp_dir), str(destination))

    validation = validate_adapter(scope, adapter_id)
    return {
        "ok": True,
        "adapter_id": adapter_id,
        "directory": destination.relative_to(scope.root).as_posix(),
        "files": members,
        "validation": validation,
    }


def _extract_verified(source: Path, temp_dir: Path) -> list[str]:
    extracted: list[str] = []
    total_bytes = 0

    with zipfile.ZipFile(source) as zf:
        infos = [info for info in zf.infolist() if not info.is_dir()]
        if len(infos) > _MAX_PACK_ENTRIES:
            raise PackageError(f".calcpack 条目过多（上限 {_MAX_PACK_ENTRIES}）")

        for info in infos:
            _check_member_name(info.filename)
            total_bytes += info.file_size
            if total_bytes > _MAX_PACK_BYTES:
                raise PackageError(f".calcpack 解压后超过 {_MAX_PACK_BYTES // (1024 * 1024)} MiB 限制")

        if "meta.json" not in {info.filename for info in infos}:
            raise PackageError("calcpack 中缺少 meta.json")

        for info in infos:
            data = zf.read(info)
            destination = (temp_dir / info.filename).resolve()
            if not destination.is_relative_to(temp_dir.resolve()):
                raise PackageError(f"calcpack 条目越界: {info.filename!r}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            extracted.append(info.filename)

    return sorted(extracted)


def _check_member_name(name: str) -> None:
    if not name or "\x00" in name or "\\" in name:
        raise PackageError(f"calcpack 条目名非法: {name!r}")

    pure = PurePosixPath(name)
    if pure.is_absolute() or pure.drive:
        raise PackageError(f"calcpack 条目越界: {name!r}")
    if ".." in pure.parts:
        raise PackageError(f"calcpack 条目越界: {name!r}")


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"{label} 读取失败: {exc}") from exc
    if not isinstance(data, dict):
        raise PackageError(f"{label} 必须是 JSON 对象")
    return data


def _read_referenced(
    target: Path,
    meta: dict[str, Any],
    key: str,
    *,
    required: bool,
) -> dict[str, Any] | None:
    ref = meta.get(key)
    if not ref:
        if required:
            raise PackageError(f"meta.json 缺少必需的 {key}")
        return None

    try:
        path = _safe_join(target, str(ref))
    except PackageError:
        raise
    if not path.is_file():
        raise PackageError(f"{key} 文件不存在: {ref}")
    return _read_json(path, str(ref))


def _read_optional_json(path: Path, warnings: list[str]) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        warnings.append(f"跳过无法解析的文件 {path.name}: {exc}")
        return None
    return data if isinstance(data, dict) else None


def _read_data_files(data_dir: Path, warnings: list[str]) -> dict[str, list[Any]]:
    result: dict[str, list[Any]] = {}
    if not data_dir.is_dir():
        return result

    for path in sorted(data_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"跳过无法解析的数据文件 {path.name}: {exc}")
            continue
        if isinstance(payload, list):
            result[path.stem] = payload
        else:
            warnings.append(f"数据文件 {path.name} 不是数组，已跳过")
    return result


def _collect_assets(target: Path, layout: dict[str, Any], warnings: list[str]) -> dict[str, str]:
    assets: dict[str, str] = {}
    used_names: set[str] = set()

    for section in layout.get("sections", []) or []:
        if not isinstance(section, dict) or section.get("widget_type") != "donation":
            continue
        raw = str((section.get("widget_config") or {}).get("image_path", "")).strip()
        if not raw or raw.startswith(("http://", "https://")):
            continue
        try:
            source = _safe_join(target, raw)
        except PackageError:
            warnings.append(f"资产路径越界，已跳过: {raw}")
            continue
        if not source.is_file():
            warnings.append(f"资产文件不存在，已跳过: {raw}")
            continue

        name = source.name
        if name in used_names:
            name = f"{len(used_names)}_{name}"
        used_names.add(name)
        assets[str(source)] = name

    return assets


def _safe_join(base: Path, rel: str) -> Path:
    candidate = Path(rel)
    if candidate.is_absolute() or candidate.drive:
        raise PackageError(f"不允许绝对路径: {rel!r}")
    resolved = (base / candidate).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise PackageError(f"路径越界: {rel!r}")
    return resolved
