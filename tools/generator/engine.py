"""生成主引擎 — 协调模板加载、DAG 构建、文件生成。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .templates import list_templates, load_template
from .dag_builder import build_simple_formula, dag_to_json
from .schema_builder import build_attr_schema, attr_schema_to_json
from .layout_builder import build_layout, layout_to_json
from .validators import validate_adapter


class GeneratorEngine:
    """计算器生成引擎。

    用法:
        engine = GeneratorEngine()
        # 列出模板
        engine.list_templates()
        # 从模板 + 用户描述生成适配器
        result = engine.generate("simple", game_name="我的游戏", ...)
    """

    def list_templates(self) -> dict[str, dict[str, str]]:
        """列出所有可用模板。"""
        return list_templates()

    def generate(
        self,
        template_id: str,
        game_name: str,
        *,
        variables: list[dict[str, Any]] | None = None,
        formula_steps: list[dict[str, Any]] | None = None,
        outputs: list[dict[str, str]] | None = None,
        output_dir: str | Path | None = None,
    ) -> dict[str, str]:
        """从模板生成完整的适配器包。

        Args:
            template_id: 模板 ID（如 "simple", "fps"）
            game_name: 游戏名称
            variables: 变量列表（覆盖模板默认值）
            formula_steps: 公式步骤（覆盖模板默认 DAG）
            outputs: 输出列表（覆盖模板默认输出）
            output_dir: 输出目录（None = 只返回文件内容不写盘）

        Returns:
            {文件名: 文件内容} 的字典
        """
        # 1. 加载模板
        template = load_template(template_id)
        meta = dict(template.get("meta", {}))
        dag = dict(template.get("dag", {})) if "dag" in template else {}
        attr_schema = dict(template.get("attr_schema", {})) if "attr_schema" in template else {"attributes": []}
        ui_layout = dict(template.get("ui_layout", {})) if "ui_layout" in template else {}
        functions_py = template.get("functions.py", "")

        # 2. 更新 meta
        game_id = game_name.lower().replace(" ", "_").replace("：", "").replace(":", "")
        meta["name"] = game_name
        meta["game"] = game_name
        if "entry_dag" in meta:
            meta["entry_dag"] = f"{game_id}.dag.json"

        # 3. 如果有自定义 variables/steps/outputs，重新构建 DAG
        if variables and formula_steps and outputs:
            dag = build_simple_formula(variables, formula_steps, outputs)
            dag["name"] = f"{game_name}伤害公式"
        elif dag:
            dag = dict(dag)  # 复制，避免修改模板

        # 4. 构建 attr_schema（如果提供了自定义变量）
        if variables and not attr_schema.get("attributes"):
            attr_schema = build_attr_schema(variables)

        # 5. 构建 layout（如果提供了自定义变量/输出）
        if outputs and not ui_layout.get("sections"):
            input_vars = [v["name"] for v in (variables or []) if v.get("source") == "user_input"]
            output_names = [o["name"] for o in outputs]
            ui_layout = build_layout(f"{game_name}计算表", input_vars, output_names)

        # 6. 验证
        dag_outputs = dag.get("outputs", {}) if dag else {}
        validation = validate_adapter(meta, dag, attr_schema, ui_layout)

        # 7. 组装输出文件
        files: dict[str, str] = {}
        files["meta.json"] = json.dumps(meta, ensure_ascii=False, indent=2)
        if dag:
            files[f"{game_id}.dag.json"] = json.dumps(dag, ensure_ascii=False, indent=2)
        files["attr_schema.json"] = json.dumps(attr_schema, ensure_ascii=False, indent=2)
        if ui_layout:
            files["ui/layout.json"] = json.dumps(ui_layout, ensure_ascii=False, indent=2)
        if functions_py:
            files["functions.py"] = functions_py

        # 8. 写盘
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            for filepath, content in files.items():
                fp = out_path / filepath
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")

        return files
