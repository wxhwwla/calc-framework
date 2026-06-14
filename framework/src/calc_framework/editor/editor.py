# SPDX-License-Identifier: AGPL-3.0
"""布局编辑器 — 编排 DAG 变量到 layout.json Section。



提供编程 API + CLI，支持从 DAG 自动推断可用变量/输出并分配到排版区。

"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from calc_framework.ui.i18n import tr

from ..dag.schema import DAGGraph, DAGSubgraph
from ..dag.serializer import load_dag
from ..ui.layout import Layout, Section, load_layout


@dataclass
class EditorState:
    """EditorState。"""

    sections: list[Section] = field(default_factory=list)

    layout_name: str = ""

    def find_section(self, section_id: str) -> Section | None:
        for s in self.sections:
            if s.id == section_id:
                return s

        return None

    def to_layout(self) -> Layout:
        return Layout(
            schema_version="ui-v1",
            name=self.layout_name or "Computed Layout",
            description="",
            sections=list(self.sections),
        )

    def to_dict(self) -> dict[str, Any]:
        layout = self.to_layout()

        return {
            "schema_version": layout.schema_version,
            "name": layout.name,
            "description": layout.description,
            "sections": [
                {
                    "id": s.id,
                    "type": s.type,
                    "title": s.title,
                    "variables": s.variables,
                    "outputs": s.outputs,
                    "columns": s.columns,
                }
                for s in layout.sections
            ],
        }


def discover_input_variables(dag: DAGGraph) -> list[str]:
    """收集所有 source 非 computed 的变量（即用户输入变量）。"""

    vars_list: list[str] = []

    for var_id, var_def in dag.variables.items():
        if var_def.source != "computed":
            vars_list.append(var_id)

    var_map: dict[str, DAGSubgraph] = dag.subgraphs if hasattr(dag, "subgraphs") else {}

    for _sg_name, subgraph in var_map.items():
        for var_id, var_def in subgraph.parameters.items():
            if var_def.source != "computed" and var_id not in vars_list:
                vars_list.append(var_id)

    return sorted(vars_list)


def discover_outputs(dag: DAGGraph) -> list[str]:
    """收集全部 output 节点的名称。"""

    result = list(dag.outputs.keys())

    var_map: dict[str, DAGSubgraph] = dag.subgraphs if hasattr(dag, "subgraphs") else {}

    for _sg_name, subgraph in var_map.items():
        for out_name in subgraph.outputs:
            if out_name not in result:
                result.append(out_name)

    return sorted(result)


class LayoutEditor:
    """LayoutEditor。"""

    def __init__(self, dag_path: Path | str | None = None, dag: DAGGraph | None = None):
        if dag is not None:
            self._dag = dag

        elif dag_path is not None:
            self._dag = load_dag(Path(dag_path))

        else:
            raise ValueError("必须提供 dag_path 或 dag")

        self._state = EditorState()

        self._available_inputs = discover_input_variables(self._dag)

        self._available_outputs = discover_outputs(self._dag)

    @property
    def dag(self) -> DAGGraph:
        """dag。"""
        return self._dag

    @property
    def state(self) -> EditorState:
        """state。"""

        return self._state

    @property
    def available_input_vars(self) -> list[str]:
        return list(self._available_inputs)

    @property
    def available_outputs(self) -> list[str]:
        return list(self._available_outputs)

    def set_name(self, name: str) -> None:
        self._state.layout_name = name

    def add_section(
        self,
        section_id: str,
        *,
        type: str = "outputs",
        title: str = "",
        variables: list[str] | None = None,
        outputs: list[str] | None = None,
        columns: int = 2,
    ) -> Section:
        section = Section(
            id=section_id,
            title=title or section_id,
            type=type,
            variables=variables or [],
            outputs=outputs or [],
            columns=columns,
        )

        self._state.sections.append(section)

        return section

    def remove_section(self, section_id: str) -> bool:
        for i, s in enumerate(self._state.sections):
            if s.id == section_id:
                self._state.sections.pop(i)

                return True

        return False

    def set_section_variables(self, section_id: str, variables: list[str]) -> Section:
        sec = self._state.find_section(section_id)

        if sec is None:
            raise KeyError(f"section {section_id} 不存在")

        sec.variables = list(variables)

        return sec

    def set_section_outputs(self, section_id: str, outputs: list[str]) -> Section:
        sec = self._state.find_section(section_id)

        if sec is None:
            raise KeyError(f"section {section_id} 不存在")

        sec.outputs = list(outputs)

        return sec

    def auto_layout(self, name: str = "Computed Layout") -> Layout:
        self._state.layout_name = name

        self._state.sections.clear()

        inputs = self._available_inputs

        if inputs:
            self.add_section("inputs", type="inputs", title=tr("desktop.editor.inputParams"), variables=list(inputs))

        root_outputs = sorted(self._dag.outputs.keys())

        if root_outputs:
            self.add_section("outputs", type="outputs", title=tr("desktop.editor.calcResults"), outputs=root_outputs)

        return self._state.to_layout()

    def export(self, path: Path | str) -> None:
        data = self._state.to_dict()

        p = Path(path)

        p.parent.mkdir(parents=True, exist_ok=True)

        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_json(self) -> str:
        return json.dumps(self._state.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_layout(cls, dag_path: Path | str, layout_path: Path | str) -> LayoutEditor:
        dag = load_dag(Path(dag_path))

        with open(layout_path, encoding="utf-8") as f:
            layout = load_layout(json.load(f))

        editor = cls(dag=dag)

        editor._state = EditorState(
            sections=list(layout.sections),
            layout_name=layout.name,
        )

        return editor
