# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""数据差异比较引擎测试。"""

from __future__ import annotations

import json
import subprocess
import sys

from tools.data_pipeline.diff import (
    DataDiffResult,
    compare_entities,
    render_html,
    render_json,
    render_text,
)

# ── 测试辅助 ──


_A = {"名称": "角色A", "星级": 5, "类型": "近卫", "武器": "单手剑", "技能": []}
_B = {"名称": "角色B", "星级": 4, "类型": "术师", "技能": []}
_C = {"名称": "角色C", "星级": 5, "类型": "狙击", "技能": []}

_SKILL_A = {
    "名称": "战技",
    "标签": "主动",
    "百分比": True,
    "段": [
        {"倍率": [100, 110, 120]},
        {"倍率": [200, 220, 240], "伤害类型": "物理"},
    ],
}

_SKILL_B = {
    "名称": "连携技",
    "标签": "主动",
    "百分比": True,
    "段": [
        {"倍率": [300, 330, 360]},
    ],
}

_SKILL_A_MODIFIED = {
    "名称": "战技",
    "标签": "主动",
    "百分比": True,
    "段": [
        {"倍率": [105, 115, 125]},
        {"倍率": [200, 220, 240], "伤害类型": "法术"},
    ],
}


# ── 无差异 ──


def test_identical_data():
    old = [_A, _B]
    new = [_A, _B]
    result = compare_entities(old, new)
    assert not result.has_changes
    assert result.total_old == 2
    assert result.total_new == 2
    assert len(result.added) == 0
    assert len(result.removed) == 0
    assert len(result.modified) == 0


def test_identical_empty():
    result = compare_entities([], [])
    assert not result.has_changes
    assert result.total_old == 0
    assert result.total_new == 0


# ── 新增 / 删除 ──


def test_added_entity():
    old = [_A]
    new = [_A, _B]
    result = compare_entities(old, new)
    assert result.has_changes
    assert len(result.added) == 1
    assert result.added[0].name == "角色B"
    assert result.added[0].status == "added"


def test_removed_entity():
    old = [_A, _B]
    new = [_A]
    result = compare_entities(old, new)
    assert result.has_changes
    assert len(result.removed) == 1
    assert result.removed[0].name == "角色B"


def test_added_and_removed():
    old = [_A, _B]
    new = [_A, _C]
    result = compare_entities(old, new)
    assert len(result.added) == 1
    assert result.added[0].name == "角色C"
    assert len(result.removed) == 1
    assert result.removed[0].name == "角色B"


# ── 字段级修改 ──


def test_field_change():
    old_a = dict(_A)
    new_a = dict(_A)
    new_a["星级"] = 6
    old = [old_a]
    new = [new_a]
    result = compare_entities(old, new)
    assert result.has_changes
    assert len(result.modified) == 1
    md = result.modified[0]
    assert md.name == "角色A"
    assert len(md.field_changes) == 1
    assert md.field_changes[0].field == "星级"
    assert md.field_changes[0].old_value == 5
    assert md.field_changes[0].new_value == 6


def test_field_added():
    old_a = {"名称": "角色A", "星级": 5}
    new_a = {"名称": "角色A", "星级": 5, "类型": "近卫"}
    result = compare_entities([old_a], [new_a])
    assert len(result.modified) == 1
    assert len(result.modified[0].field_changes) == 1
    assert result.modified[0].field_changes[0].field == "类型"


def test_field_removed():
    old_a = {"名称": "角色A", "星级": 5, "类型": "近卫"}
    new_a = {"名称": "角色A", "星级": 5}
    result = compare_entities([old_a], [new_a])
    assert len(result.modified) == 1
    assert len(result.modified[0].field_changes) == 1


# ── 技能级修改 ──


def test_skill_added():
    old = [{"名称": "角色A", "技能": [_SKILL_A]}]
    new = [{"名称": "角色A", "技能": [_SKILL_A, _SKILL_B]}]
    result = compare_entities(old, new)
    assert len(result.modified) == 1
    md = result.modified[0]
    assert len(md.added_skills) == 1
    assert md.added_skills[0].name == "连携技"


def test_skill_removed():
    old = [{"名称": "角色A", "技能": [_SKILL_A, _SKILL_B]}]
    new = [{"名称": "角色A", "技能": [_SKILL_A]}]
    result = compare_entities(old, new)
    assert len(result.modified) == 1
    md = result.modified[0]
    assert len(md.removed_skills) == 1
    assert md.removed_skills[0].name == "连携技"


def test_skill_field_change():
    old = [{"名称": "角色A", "技能": [dict(_SKILL_A, 百分比=True)]}]
    new = [{"名称": "角色A", "技能": [dict(_SKILL_A, 百分比=False)]}]
    result = compare_entities(old, new)
    assert len(result.modified) == 1
    md = result.modified[0]
    assert len(md.modified_skills) == 1
    assert len(md.modified_skills[0].field_changes) == 1
    assert md.modified_skills[0].field_changes[0].field == "百分比"


# ── 段级修改 ──


def test_segment_rate_change():
    old_skill = dict(_SKILL_A)
    new_skill = dict(_SKILL_A_MODIFIED)
    old = [{"名称": "角色A", "技能": [old_skill]}]
    new = [{"名称": "角色A", "技能": [new_skill]}]
    result = compare_entities(old, new)
    assert len(result.modified) == 1
    md = result.modified[0]
    assert len(md.modified_skills) == 1
    ms = md.modified_skills[0]
    assert len(ms.modified_segments) == 2
    seg0 = ms.modified_segments[0]
    assert seg0.index == 0
    assert seg0.rates_old == [100, 110, 120]
    assert seg0.rates_new == [105, 115, 125]
    seg1 = ms.modified_segments[1]
    assert seg1.index == 1
    assert seg1.type_old == "物理"
    assert seg1.type_new == "法术"


def test_segment_added():
    old_skill = {"名称": "战技", "标签": "主动", "百分比": True, "段": [_SKILL_A["段"][0]]}
    new_skill = dict(_SKILL_A)
    result = compare_entities(
        [{"名称": "角色A", "技能": [old_skill]}],
        [{"名称": "角色A", "技能": [new_skill]}],
    )
    assert len(result.modified) == 1
    assert result.modified[0].modified_skills[0].added_segments == [1]


def test_segment_removed():
    old_skill = dict(_SKILL_A)
    new_skill = {"名称": "战技", "标签": "主动", "百分比": True, "段": [_SKILL_A["段"][0]]}
    result = compare_entities(
        [{"名称": "角色A", "技能": [old_skill]}],
        [{"名称": "角色A", "技能": [new_skill]}],
    )
    assert len(result.modified) == 1
    assert result.modified[0].modified_skills[0].removed_segments == [1]


# ── 渲染输出 ──


def test_render_text_no_changes():
    result = compare_entities([_A], [_A])
    text = render_text(result)
    assert "无差异" in text


def test_render_text_with_changes():
    result = compare_entities([_A], [_A, _B])
    text = render_text(result)
    assert "新增" in text
    assert "角色B" in text


def test_render_json_structure():
    result = compare_entities([_A], [_A, _B])
    data = render_json(result)
    assert "summary" in data
    assert data["summary"]["added"] == 1
    assert data["summary"]["total_old"] == 1
    assert data["summary"]["total_new"] == 2
    assert len(data["added"]) == 1
    assert data["added"][0]["name"] == "角色B"


def test_render_json_modified():
    old_a = dict(_A)
    new_a = dict(_A)
    new_a["星级"] = 6
    result = compare_entities([old_a], [new_a])
    data = render_json(result)
    assert data["summary"]["modified"] == 1
    assert len(data["modified"]) == 1
    assert data["modified"][0]["field_changes"][0]["field"] == "星级"


def test_render_html_structure():
    result = compare_entities([_A], [_A, _B])
    html = render_html(result)
    assert "<!DOCTYPE html>" in html
    assert "角色B" in html
    assert "新增" in html or "新增" in html


def test_render_html_no_changes():
    result = compare_entities([_A], [_A])
    html = render_html(result)
    assert "无差异" in html


# ── 排序顺序 ──


def test_output_sorted_by_name():
    old = [_B, _A]
    new = [_B, _A, {"名称": "角色C", "技能": []}]
    result = compare_entities(old, new)
    assert len(result.added) == 1
    assert result.added[0].name == "角色C"


def test_summary_property():
    r1 = DataDiffResult(total_old=2, total_new=2)
    assert r1.summary == "无差异"

    r2 = DataDiffResult(total_old=2, total_new=3, added=[_entity_diff("X")])
    assert "新增" in r2.summary

    r3 = DataDiffResult(total_old=3, total_new=2, removed=[_entity_diff("X")])
    assert "删除" in r3.summary

    r4 = DataDiffResult(total_old=2, total_new=2, modified=[_entity_diff("X")])
    assert "修改" in r4.summary


def _entity_diff(name: str):
    from tools.data_pipeline.diff import EntityDiff

    return EntityDiff(name=name, status="modified")


# ── 长值摘要 ──


def test_long_list_summary():
    long_list = list(range(100))
    old = [{"名称": "A", "数据": long_list}]
    new = [{"名称": "A", "数据": list(range(50))}]
    result = compare_entities(old, new)
    assert result.has_changes
    fc = result.modified[0].field_changes[0]
    assert "[100 项]" in str(fc.old_value)


# ── CLI 转换与校验 ──


def _run_cli_json(path, *args):
    import os

    result = subprocess.run(
        [sys.executable, "-m", "tools.data_pipeline.cli", str(path), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert result.returncode == 0, result.stderr
    return result.stdout, json.loads(result.stdout[result.stdout.index("[\n") :])


def test_validate_standard_json_preserves_nested_skills(tmp_path):
    entity = dict(_A, 技能=[_SKILL_A])
    path = tmp_path / "standard.json"
    path.write_text(json.dumps([entity], ensure_ascii=False), encoding="utf-8")

    message, payload = _run_cli_json(path, "--validate")

    assert "校验通过" in message
    assert payload == [entity]


def test_stacked_skills_merge_and_preserve_numeric_types(tmp_path):
    path = tmp_path / "stacked.csv"
    path.write_text(
        "名称,星级,技能名称1,技能标签1,技能百分比1,段1倍率1\n"
        '角色A,1,战技,主动,true,"100,110"\n'
        '角色A,0,连携技,主动,false,"200,220"\n',
        encoding="utf-8",
    )

    _message, payload = _run_cli_json(path, "--stacked-skills")

    assert len(payload) == 1
    assert [skill["名称"] for skill in payload[0]["技能"]] == ["战技", "连携技"]
    assert payload[0]["星级"] == 1
    assert isinstance(payload[0]["星级"], int)
