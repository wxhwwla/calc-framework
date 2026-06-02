# SPDX-License-Identifier: AGPL-3.0
"""layout.json 加载与校验 — ComputeSheet 排版描述。



Schema 版本：ui-v1

"""



from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from calc_framework.errors import CalcFrameworkError


class LayoutValidationError(CalcFrameworkError):
    """layout.json 校验失败。"""





VALID_SECTION_TYPES = ("inputs", "outputs", "widget")

VALID_WIDGET_TYPES = ("donation",)





@dataclass

class Section:

    """Section。"""
    id: str

    title: str

    type: str

    variables: list[str] = field(default_factory=list)

    outputs: list[str] = field(default_factory=list)

    columns: int = 2

    widget_type: str = ""

    widget_config: dict[str, Any] = field(default_factory=dict)





@dataclass

class Layout:
    """Layout。"""

    schema_version: str

    name: str

    sections: list[Section]

    description: str = ""



    def find_section(self, section_id: str) -> Section | None:

        for s in self.sections:

            if s.id == section_id:

                return s

        return None





def load_layout(data: dict[str, Any]) -> Layout:

    _validate(data)

    sections = _build_sections(data["sections"])

    return Layout(

        schema_version=data["schema_version"],

        name=data["name"],

        description=data.get("description", ""),

        sections=sections,

    )





def load_layout_json(json_str: str) -> Layout:

    return load_layout(json.loads(json_str))





    """_validate。"""
def _validate(data: dict[str, Any]) -> None:

    if data.get("schema_version") != "ui-v1":

        raise LayoutValidationError("schema_version 必须为 ui-v1")

    if not isinstance(data.get("name"), str) or not data["name"]:

        raise LayoutValidationError("缺少 name 字段")

    if not isinstance(data.get("sections"), list) or len(data["sections"]) == 0:

        raise LayoutValidationError("sections 必须为非空列表")



    seen_ids: set[str] = set()

    for sec in data["sections"]:

        if not isinstance(sec, dict):

            raise LayoutValidationError("每个 section 必须为对象")



        section_id = sec.get("id")

        if not isinstance(section_id, str) or not section_id:

            raise LayoutValidationError("每个 section 必须有非空 id")

        if section_id in seen_ids:

            raise LayoutValidationError(f"section id 重复: {section_id}")

        seen_ids.add(section_id)



        sec_type = sec.get("type")

        if sec_type not in VALID_SECTION_TYPES:

            raise LayoutValidationError(

                f"section type 必须为 {'/'.join(VALID_SECTION_TYPES)}，收到: {sec_type}"

            )



        if not isinstance(sec.get("title"), str) or not sec["title"]:

            raise LayoutValidationError(f"section {section_id} 缺少 title")



        if sec_type == "inputs" and not isinstance(sec.get("variables"), list):

            raise LayoutValidationError(f"inputs section {section_id} 缺少 variables 列表")

        if sec_type == "outputs" and not isinstance(sec.get("outputs"), list):

            raise LayoutValidationError(f"outputs section {section_id} 缺少 outputs 列表")

        if sec_type == "widget":

            widget_type = sec.get("widget_type", "")

            if widget_type not in VALID_WIDGET_TYPES:

                raise LayoutValidationError(

                    f"widget section {section_id} 的 widget_type 必须为 "

                    f"{'/'.join(VALID_WIDGET_TYPES)}，收到: {widget_type}"

                )




    """_build_sections。"""

def _build_sections(raw: list[dict[str, Any]]) -> list[Section]:

    result: list[Section] = []

    for sec in raw:

        result.append(Section(

            id=sec["id"],

            title=sec["title"],

            type=sec["type"],

            variables=sec.get("variables", []),

            outputs=sec.get("outputs", []),

            columns=sec.get("columns", 2),

            widget_type=sec.get("widget_type", ""),

            widget_config=sec.get("widget_config", {}),

        ))

    return result

