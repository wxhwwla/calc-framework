#!/usr/bin/env python3
""".calcpack 导出器 — 将内存中的适配包数据打包为 ZIP 文件。

用法::

    from tools.designer.exporter import export_calcpack

    export_calcpack(
        output_path="终末地.calcpack",
        meta={...},
        dag={...},
        layout={...},
        theme={...},
        data_files={"characters": [...], "weapons": [...]},
    )
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any


def export_calcpack(
    output_path: str | Path,
    meta: dict[str, Any],
    dag: dict[str, Any],
    layout: dict[str, Any],
    *,
    theme: dict[str, Any] | None = None,
    data_files: dict[str, list[dict[str, Any]]] | None = None,
) -> str:
    """将适配包数据导出为 .calcpack 文件。

    Args:
        output_path: 输出路径（自动补 .calcpack 后缀）
        meta: meta.json 内容
        dag: 主 DAG 公式图
        layout: layout.json 内容
        theme: 可选 theme.json
        data_files: 数据文件映射，key 为文件名（不含路径），
                    value 为实体列表。如 ``{"characters": [...], "weapons": [...]}``

    Returns:
        实际写入的路径
    """
    path = Path(output_path)
    if path.suffix.lower() not in (".calcpack", ".zip"):
        path = path.with_suffix(".calcpack")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        _write_json_in_zip(zf, "meta.json", meta)
        _write_json_in_zip(zf, "dag/formula.dag.json", dag)
        _write_json_in_zip(zf, "ui/layout.json", layout)

        if theme:
            _write_json_in_zip(zf, "ui/theme.json", theme)

        if data_files:
            for key, records in data_files.items():
                _write_json_in_zip(zf, f"data/{key}.json", records)

    return str(path)


def _write_json_in_zip(
    zf: zipfile.ZipFile,
    arcname: str,
    data: Any,
) -> None:
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    zf.writestr(arcname, content)
