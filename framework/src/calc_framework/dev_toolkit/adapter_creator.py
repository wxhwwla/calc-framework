# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""adapter_creator — 从 DAG 文件创建完整适配器包的纯逻辑（无 PySide6 依赖）。

从 dev_toolkit/pages.py _NewAdapterPage._create_adapter() 提取。
可被 CLI / Web / 测试直接复用。
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AdapterScaffoldConfig:
    """适配器脚手架配置。

    属性：
        name: 适配器名称
        game: 游戏名称
        description: 适配器描述
        dag_file: DAG 文件路径
        output_root: 输出根目录（默认 framework/adapters/）
    """

    name: str
    game: str = "通用游戏"
    description: str = ""
    dag_file: Path = field(default_factory=Path)
    output_root: Path = field(default_factory=Path)

    @property
    def safe_name(self) -> str:
        """文件系统安全的名称（替换空格和路径分隔符）。"""
        return self.name.replace(" ", "_").replace("/", "_").replace("\\", "_")


@dataclass
class ScaffoldResult:
    """脚手架执行结果。

    属性：
        adapter_dir: 生成的适配器目录路径
        files: 生成的文件相对路径列表
        success: 是否成功
        error: 错误信息（失败时）
    """

    adapter_dir: Path = field(default_factory=Path)
    files: list[str] = field(default_factory=list)
    success: bool = True
    error: str = ""


def scaffold_adapter_directory(config: AdapterScaffoldConfig) -> ScaffoldResult:
    """从 DAG 文件创建完整适配器包目录。

    生成 meta.json + attr_schema.json + ui/layout.json + functions.py + data/ 目录。
    从 dev_toolkit/pages.py _NewAdapterPage._create_adapter() 提取。

    参数：
        config: 适配器脚手架配置。

    返回：
        ScaffoldResult，包含生成的目录路径和文件列表。
    """
    from calc_framework.dag.serializer import load_dag

    if not config.dag_file or not config.dag_file.exists():
        return ScaffoldResult(success=False, error="DAG 文件不存在")

    if not config.name.strip():
        return ScaffoldResult(success=False, error="适配器名称不能为空")

    # 加载 DAG 验证
    try:
        dag = load_dag(config.dag_file)
    except Exception as e:
        return ScaffoldResult(success=False, error=f"DAG 加载失败: {e}")

    safe_name = config.safe_name
    adapter_dir = config.output_root / safe_name
    adapter_dir.mkdir(parents=True, exist_ok=True)
    (adapter_dir / "ui").mkdir(exist_ok=True)

    dag_filename = f"{safe_name}.dag.json"
    generated_files: list[str] = []

    # 1. 复制 DAG 文件
    shutil.copy2(config.dag_file, adapter_dir / dag_filename)
    generated_files.append(f"{safe_name}/{dag_filename}")

    # 2. 生成 meta.json
    meta = {
        "name": config.name,
        "game": config.game,
        "description": config.description or dag.description or config.name,
        "version": "1.0.0",
        "schema_version": "dag-v1",
        "entry_dag": dag_filename,
        "ui_layout": "ui/layout.json",
        "attr_schema": "attr_schema.json",
    }
    (adapter_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    generated_files.append(f"{safe_name}/meta.json")

    # 3. 生成 attr_schema.json（从 DAG 变量推断，过滤 user_input）
    valid_sources = {"character", "weapon", "equipment", "enemy", "computed"}
    attrs = []
    for var_path, var_def in dag.variables.items():
        parts = var_path.split(".")
        if len(parts) == 2:
            source = var_def.source if var_def.source in valid_sources else "computed"
            attrs.append(
                {
                    "name": parts[1],
                    "type": var_def.type if var_def.type in ("float", "int", "bool", "percent") else "float",
                    "source": source,
                    "default": var_def.default if var_def.default is not None else 0.0,
                    "description": var_def.description or parts[1],
                }
            )
    (adapter_dir / "attr_schema.json").write_text(
        json.dumps({"attributes": attrs}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    generated_files.append(f"{safe_name}/attr_schema.json")

    # 4. 创建 data/ 目录 + 空数据文件
    data_dir = adapter_dir / "data"
    data_dir.mkdir(exist_ok=True)
    source_groups: dict[str, list[str]] = {}
    for var_path, var_def in dag.variables.items():
        parts = var_path.split(".")
        if len(parts) == 2 and var_def.source in valid_sources:
            source_groups.setdefault(var_def.source, []).append(parts[1])
    for source in source_groups:
        data_file = data_dir / f"{source}s.json"
        if not data_file.exists():
            data_file.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. 生成 ui/layout.json（自动布局）
    input_vars = [k for k, v in dag.variables.items() if v.source != "computed"]
    output_names = list(dag.outputs.keys())
    sections = []
    if input_vars:
        sections.append(
            {
                "id": "inputs",
                "type": "inputs",
                "title": "输入参数",
                "variables": input_vars,
            }
        )
    if output_names:
        sections.append(
            {
                "id": "outputs",
                "type": "outputs",
                "title": "计算结果",
                "outputs": output_names,
            }
        )
    layout_data = {
        "schema_version": "ui-v1",
        "name": config.name,
        "sections": sections,
    }
    (adapter_dir / "ui" / "layout.json").write_text(json.dumps(layout_data, ensure_ascii=False, indent=2), encoding="utf-8")
    generated_files.append(f"{safe_name}/ui/layout.json")

    # 6. 生成空 functions.py
    (adapter_dir / "functions.py").write_text(
        f'# -*- coding: utf-8 -*-\n# SPDX-License-Identifier: AGPL-3.0\n"""{config.name} — 自定义函数。"""\n',
        encoding="utf-8",
    )
    generated_files.append(f"{safe_name}/functions.py")

    return ScaffoldResult(adapter_dir=adapter_dir, files=generated_files)
