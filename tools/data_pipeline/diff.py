#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0
"""数据差异比较引擎 — 对比两个标准 EntitySchema 列表，输出差异详情。

支持三种输出格式：
- text: 终端友好的 git-diff 风格文本
- json: 机器可读的结构化数据
- html: 浏览器可预览的差异页面

用法::

    from tools.data_pipeline.diff import compare_entities, render_text

    old = [{"名称": "A", "星级": 5, ...}, ...]
    new = [{"名称": "A", "星级": 6, ...}, ...]
    result = compare_entities(old, new)
    print(render_text(result))
"""

from __future__ import annotations

import difflib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── 差异数据结构 ──


@dataclass
class FieldChange:
    """某个字段的值变化。"""
    field: str
    old_value: Any
    new_value: Any
    path: str = ""


@dataclass
class SegmentDiff:
    """技能段的差异。"""
    index: int
    rates_old: Optional[List[int]] = None
    rates_new: Optional[List[int]] = None
    type_old: Optional[str] = None
    type_new: Optional[str] = None
    field_changes: List[FieldChange] = field(default_factory=list)


@dataclass
class SkillDiff:
    """技能的差异。"""
    name: str
    status: str  # "added" / "removed" / "modified"
    added_segments: List[int] = field(default_factory=list)
    removed_segments: List[int] = field(default_factory=list)
    modified_segments: List[SegmentDiff] = field(default_factory=list)
    field_changes: List[FieldChange] = field(default_factory=list)


@dataclass
class EntityDiff:
    """单个实体的差异。"""
    name: str
    status: str  # "added" / "removed" / "modified"
    field_changes: List[FieldChange] = field(default_factory=list)
    added_skills: List[SkillDiff] = field(default_factory=list)
    removed_skills: List[SkillDiff] = field(default_factory=list)
    modified_skills: List[SkillDiff] = field(default_factory=list)


@dataclass
class DataDiffResult:
    """完整的数据差异比较结果。"""
    added: List[EntityDiff] = field(default_factory=list)
    removed: List[EntityDiff] = field(default_factory=list)
    modified: List[EntityDiff] = field(default_factory=list)
    total_old: int = 0
    total_new: int = 0

    @property
    def has_changes(self) -> bool:
        """has_changes 实现。"""
        return bool(self.added or self.removed or self.modified)

    @property
    def summary(self) -> str:
        """summary 实现。"""
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} 新增")
        if self.removed:
            parts.append(f"-{len(self.removed)} 删除")
        if self.modified:
            parts.append(f"~{len(self.modified)} 修改")
        if not parts:
            return "无差异"
        return ", ".join(parts)


# ── 核心比较逻辑 ──


def compare_entities(
    old_list: List[Dict[str, Any]],
    new_list: List[Dict[str, Any]],
    *,
    name_key: str = "名称",
) -> DataDiffResult:
    """比较新旧两个实体列表，返回结构化差异结果。

    Args:
        old_list: 旧版本的实体列表（EntitySchema）
        new_list: 新版本的实体列表（EntitySchema）
        name_key: 实体标识字段名，默认 "名称"

    Returns:
        DataDiffResult 结构
    """
    result = DataDiffResult(
        total_old=len(old_list),
        total_new=len(new_list),
    )

    old_by_name = {e.get(name_key, ""): e for e in old_list}
    new_by_name = {e.get(name_key, ""): e for e in new_list}

    old_names = set(old_by_name.keys())
    new_names = set(new_by_name.keys())

    for name in sorted(new_names - old_names):
        result.added.append(
            EntityDiff(name=name, status="added")
        )

    for name in sorted(old_names - new_names):
        result.removed.append(
            EntityDiff(name=name, status="removed")
        )

    for name in sorted(old_names & new_names):
        diff = _diff_entity(old_by_name[name], new_by_name[name], name)
        if diff is not None:
            result.modified.append(diff)

    return result


def _diff_entity(
    old: Dict[str, Any],
    new: Dict[str, Any],
    name: str,
) -> Optional[EntityDiff]:
    """比较单个实体的新旧版本，返回差异或 None（无变化）。"""
    old_clean = _without_skills(old)
    new_clean = _without_skills(new)

    field_changes = _diff_dict(old_clean, new_clean, name)

    old_skills = old.get("技能", [])
    new_skills = new.get("技能", [])
    skill_diffs = _diff_skills(old_skills, new_skills, name)

    if not field_changes and not skill_diffs:
        return None

    diff = EntityDiff(
        name=name,
        status="modified",
        field_changes=field_changes,
    )

    for sd in skill_diffs:
        if sd.status == "added":
            diff.added_skills.append(sd)
        elif sd.status == "removed":
            diff.removed_skills.append(sd)
        else:
            diff.modified_skills.append(sd)

    return diff


def _without_skills(entity: Dict[str, Any]) -> Dict[str, Any]:
    """返回移除了技能相关字段的实体副本。"""
    return {k: v for k, v in entity.items() if k != "技能"}


def _diff_dict(
    old: Dict[str, Any],
    new: Dict[str, Any],
    prefix: str = "",
) -> List[FieldChange]:
    """比较两个字典的字段级差异。"""
    changes: List[FieldChange] = []
    all_keys = sorted(set(old.keys()) | set(new.keys()))

    for key in all_keys:
        old_val = old.get(key)
        new_val = new.get(key)
        if _values_equal(old_val, new_val):
            continue
        path = f"{prefix}.{key}" if prefix else key
        changes.append(FieldChange(
            field=key,
            old_value=_summarize_value(old_val),
            new_value=_summarize_value(new_val),
            path=path,
        ))

    return changes


def _values_equal(a: Any, b: Any) -> bool:
    """判断两个值是否相等（支持列表/嵌套比较）。"""
    if type(a) != type(b):
        return False
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_values_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(_values_equal(a[k], b[k]) for k in a)
    return a == b


def _summarize_value(value: Any, max_len: int = 80) -> Any:
    """对长列表/字符串进行摘要，便于人类阅读。"""
    if isinstance(value, list):
        if len(value) > 8:
            return f"[{len(value)} 项] {value[:4]}...{value[-2:]}"
        return value
    if isinstance(value, str) and len(value) > max_len:
        return value[:max_len] + "..."
    return value


def _diff_skills(
    old_skills: List[Dict[str, Any]],
    new_skills: List[Dict[str, Any]],
    entity_name: str,
) -> List[SkillDiff]:
    """比较两个技能列表。通过技能名称匹配。"""
    result: List[SkillDiff] = []

    old_by_name = {s.get("名称", ""): s for s in old_skills}
    new_by_name = {s.get("名称", ""): s for s in new_skills}
    old_names = set(old_by_name.keys())
    new_names = set(new_by_name.keys())

    for name in sorted(new_names - old_names):
        result.append(SkillDiff(name=name, status="added"))

    for name in sorted(old_names - new_names):
        result.append(SkillDiff(name=name, status="removed"))

    for name in sorted(old_names & new_names):
        diff = _diff_skill(old_by_name[name], new_by_name[name], entity_name, name)
        if diff is not None:
            result.append(diff)

    return result


def _diff_skill(
    old: Dict[str, Any],
    new: Dict[str, Any],
    entity_name: str,
    skill_name: str,
) -> Optional[SkillDiff]:
    """比较单个技能的新旧版本。"""
    old_segments = old.get("段", [])
    new_segments = new.get("段", [])

    field_changes = _diff_dict(
        {k: v for k, v in old.items() if k != "段"},
        {k: v for k, v in new.items() if k != "段"},
        f"{entity_name}.技能'{skill_name}'",
    )

    segment_diffs = _diff_segments(old_segments, new_segments, entity_name, skill_name)

    if not field_changes and not segment_diffs:
        return None

    sd = SkillDiff(
        name=skill_name,
        status="modified",
        field_changes=field_changes,
    )

    for seg_diff in segment_diffs:
        status = seg_diff.get("status", "modified")
        idx = seg_diff["index"]
        if status == "added":
            sd.added_segments.append(idx)
        elif status == "removed":
            sd.removed_segments.append(idx)
        else:
            sd.modified_segments.append(SegmentDiff(
                index=idx,
                rates_old=seg_diff.get("rates_old"),
                rates_new=seg_diff.get("rates_new"),
                type_old=seg_diff.get("type_old"),
                type_new=seg_diff.get("type_new"),
            ))

    return sd


def _diff_segments(
    old_segments: List[Dict[str, Any]],
    new_segments: List[Dict[str, Any]],
    entity_name: str,
    skill_name: str,
) -> List[Dict[str, Any]]:
    """比较段级差异。通过段索引匹配。"""
    result: List[Dict[str, Any]] = []
    max_len = max(len(old_segments), len(new_segments))

    for i in range(max_len):
        if i >= len(old_segments):
            result.append({"index": i, "status": "added"})
        elif i >= len(new_segments):
            result.append({"index": i, "status": "removed"})
        else:
            old_seg = old_segments[i]
            new_seg = new_segments[i]

            old_rates = old_seg.get("倍率", [])
            new_rates = new_seg.get("倍率", [])
            old_type = old_seg.get("伤害类型")
            new_type = new_seg.get("伤害类型")

            if old_rates != new_rates or old_type != new_type:
                result.append({
                    "index": i,
                    "status": "modified",
                    "rates_old": old_rates,
                    "rates_new": new_rates,
                    "type_old": old_type,
                    "type_new": new_type,
                })

    return result


# ── 渲染输出 ──


def render_text(result: DataDiffResult) -> str:
    """将差异结果渲染为终端友好的文本格式。"""
    lines: List[str] = []

    if not result.has_changes:
        lines.append("✅ 无差异 — 新旧数据完全一致")
        return "\n".join(lines)

    lines.append(f"📊 数据差异报告")
    lines.append(f"   旧数据: {result.total_old} 条")
    lines.append(f"   新数据: {result.total_new} 条")
    lines.append(f"   差异: {result.summary}")
    lines.append("")

    if result.removed:
        lines.append(_section_header(f"🗑️  已删除 ({len(result.removed)} 个)"))
        for ed in result.removed:
            lines.append(f"  - {ed.name}")
        lines.append("")

    if result.added:
        lines.append(_section_header(f"🆕 新增 ({len(result.added)} 个)"))
        for ed in result.added:
            lines.append(f"  + {ed.name}")
        lines.append("")

    if result.modified:
        lines.append(_section_header(f"📝 已修改 ({len(result.modified)} 个)"))
        for ed in result.modified:
            lines.append(f"  ~ {ed.name}")
            _render_entity_detail(lines, ed)
            lines.append("")

    return "\n".join(lines)


def _section_header(title: str) -> str:
    """_section_header 实现。"""
    return f"━━━ {title} ━━━"


def _render_entity_detail(lines: List[str], diff: EntityDiff, indent: str = "    ") -> None:
    """_render_entity_detail 实现。"""
    for fc in diff.field_changes:
        lines.append(f"{indent}  • {fc.field}: {fc.old_value} → {fc.new_value}")

    for sd in diff.removed_skills:
        lines.append(f"{indent}  🗑️  技能 '{sd.name}' 已删除")

    for sd in diff.added_skills:
        lines.append(f"{indent}  🆕 技能 '{sd.name}' 已新增")

    for sd in diff.modified_skills:
        lines.append(f"{indent}  ~ 技能 '{sd.name}':")
        for fc in sd.field_changes:
            lines.append(f"{indent}      • {fc.field}: {fc.old_value} → {fc.new_value}")
        for si in sd.added_segments:
            lines.append(f"{indent}      🆕 段[{si}] 新增")
        for si in sd.removed_segments:
            lines.append(f"{indent}      🗑️  段[{si}] 删除")
        for seg in sd.modified_segments:
            if seg.rates_old != seg.rates_new:
                lines.append(f"{indent}      段[{seg.index}] 倍率: {seg.rates_old} → {seg.rates_new}")
            if seg.type_old != seg.type_new:
                lines.append(f"{indent}      段[{seg.index}] 伤害类型: {seg.type_old} → {seg.type_new}")


def render_json(result: DataDiffResult) -> Dict[str, Any]:
    """将差异结果渲染为 JSON 结构。"""
    return {
        "summary": {
            "total_old": result.total_old,
            "total_new": result.total_new,
            "added": len(result.added),
            "removed": len(result.removed),
            "modified": len(result.modified),
        },
        "added": [{"name": e.name} for e in result.added],
        "removed": [{"name": e.name} for e in result.removed],
        "modified": [_entity_to_json(e) for e in result.modified],
    }


def _entity_to_json(diff: EntityDiff) -> Dict[str, Any]:
    """_entity_to_json 实现。"""
    return {
        "name": diff.name,
        "field_changes": [
            {"field": fc.field, "old": fc.old_value, "new": fc.new_value}
            for fc in diff.field_changes
        ],
        "added_skills": [{"name": s.name} for s in diff.added_skills],
        "removed_skills": [{"name": s.name} for s in diff.removed_skills],
        "modified_skills": [
            {
                "name": s.name,
                "field_changes": [
                    {"field": fc.field, "old": fc.old_value, "new": fc.new_value}
                    for fc in s.field_changes
                ],
                "added_segments": s.added_segments,
                "removed_segments": s.removed_segments,
                "modified_segments": [
                    {
                        "index": seg.index,
                        "rates_old": seg.rates_old,
                        "rates_new": seg.rates_new,
                        "type_old": seg.type_old,
                        "type_new": seg.type_new,
                    }
                    for seg in s.modified_segments
                ],
            }
            for s in diff.modified_skills
        ],
    }


def render_html(result: DataDiffResult) -> str:
    """将差异结果渲染为 HTML 页面。"""
    summary_class = "no-changes"
    summary_text = "无差异 — 新旧数据完全一致"
    if result.has_changes:
        summary_class = "has-changes"
        summary_text = result.summary

    entities_html = _render_entities_html(result)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>数据差异报告</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
  h1 {{ color: #333; }}
  .summary {{ padding: 12px 16px; border-radius: 6px; margin: 16px 0; font-size: 16px; }}
  .summary.has-changes {{ background: #fff3cd; border: 1px solid #ffc107; }}
  .summary.no-changes {{ background: #d4edda; border: 1px solid #28a745; }}
  .stats {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
  .section {{ margin: 20px 0; }}
  .section-title {{ font-weight: 700; font-size: 18px; margin: 12px 0; padding-bottom: 6px; border-bottom: 2px solid #ddd; }}
  .section-title.removed {{ color: #dc3545; border-color: #dc3545; }}
  .section-title.added {{ color: #28a745; border-color: #28a745; }}
  .section-title.modified {{ color: #fd7e14; border-color: #fd7e14; }}
  .entity {{ margin: 8px 0 8px 16px; }}
  .entity-name {{ font-weight: 600; font-size: 15px; }}
  .entity-name.removed {{ color: #dc3545; }}
  .entity-name.added {{ color: #28a745; }}
  .entity-name.modified {{ color: #fd7e14; }}
  .detail {{ margin: 4px 0 4px 28px; font-size: 13px; color: #555; font-family: "SFMono-Regular", Consolas, monospace; }}
  .detail .old {{ color: #dc3545; background: #f8d7da; padding: 1px 4px; border-radius: 3px; }}
  .detail .new {{ color: #28a745; background: #d4edda; padding: 1px 4px; border-radius: 3px; }}
  .arrow {{ color: #999; margin: 0 6px; }}
  .skill {{ margin: 4px 0 4px 32px; font-size: 13px; }}
  .skill-name {{ font-weight: 500; }}
  .skill.removed {{ color: #dc3545; }}
  .skill.added {{ color: #28a745; }}
  .skill.modified {{ color: #fd7e14; }}
  .segment {{ margin: 2px 0 2px 48px; font-size: 12px; font-family: "SFMono-Regular", Consolas, monospace; }}
</style>
</head>
<body>
<h1>📊 数据差异报告</h1>
<p class="stats">旧数据: {result.total_old} 条 &nbsp;|&nbsp; 新数据: {result.total_new} 条</p>
<div class="summary {summary_class}">{summary_text}</div>
{entities_html}
</body>
</html>"""


def _render_entities_html(result: DataDiffResult) -> str:
    """_render_entities_html 实现。"""
    parts = []

    if result.removed:
        parts.append('<div class="section">')
        parts.append(f'<div class="section-title removed">🗑️ 已删除 ({len(result.removed)} 个)</div>')
        for ed in result.removed:
            parts.append(f'<div class="entity"><span class="entity-name removed">- {ed.name}</span></div>')
        parts.append('</div>')

    if result.added:
        parts.append('<div class="section">')
        parts.append(f'<div class="section-title added">🆕 新增 ({len(result.added)} 个)</div>')
        for ed in result.added:
            parts.append(f'<div class="entity"><span class="entity-name added">+ {ed.name}</span></div>')
        parts.append('</div>')

    if result.modified:
        parts.append('<div class="section">')
        parts.append(f'<div class="section-title modified">📝 已修改 ({len(result.modified)} 个)</div>')
        for ed in result.modified:
            parts.append('<div class="entity">')
            parts.append(f'<div class="entity-name modified">~ {ed.name}</div>')
            for fc in ed.field_changes:
                parts.append(
                    f'<div class="detail">• {fc.field}: '
                    f'<span class="old">{_escape_html(str(fc.old_value))}</span>'
                    f'<span class="arrow">→</span>'
                    f'<span class="new">{_escape_html(str(fc.new_value))}</span>'
                    f'</div>'
                )
            for sd in ed.removed_skills:
                parts.append(f'<div class="skill removed">🗑️ 技能 &ldquo;{_escape_html(sd.name)}&rdquo; 已删除</div>')
            for sd in ed.added_skills:
                parts.append(f'<div class="skill added">🆕 技能 &ldquo;{_escape_html(sd.name)}&rdquo; 已新增</div>')
            for sd in ed.modified_skills:
                parts.append(f'<div class="skill modified">~ 技能 &ldquo;{_escape_html(sd.name)}&rdquo;</div>')
                for fc in sd.field_changes:
                    parts.append(
                        f'<div class="detail" style="margin-left:48px">• {fc.field}: '
                        f'<span class="old">{_escape_html(str(fc.old_value))}</span>'
                        f'<span class="arrow">→</span>'
                        f'<span class="new">{_escape_html(str(fc.new_value))}</span>'
                        f'</div>'
                    )
                for si in sd.added_segments:
                    parts.append(f'<div class="segment" style="color:#28a745">🆕 段[{si}] 新增</div>')
                for si in sd.removed_segments:
                    parts.append(f'<div class="segment" style="color:#dc3545">🗑️ 段[{si}] 删除</div>')
                for seg in sd.modified_segments:
                    if seg.rates_old != seg.rates_new:
                        parts.append(
                            f'<div class="segment">段[{seg.index}] 倍率: '
                            f'<span class="old">{seg.rates_old}</span>'
                            f'<span class="arrow">→</span>'
                            f'<span class="new">{seg.rates_new}</span>'
                            f'</div>'
                        )
                    if seg.type_old != seg.type_new:
                        parts.append(
                            f'<div class="segment">段[{seg.index}] 伤害类型: '
                            f'<span class="old">{seg.type_old}</span>'
                            f'<span class="arrow">→</span>'
                            f'<span class="new">{seg.type_new}</span>'
                            f'</div>'
                        )
            parts.append('</div>')
        parts.append('</div>')

    return "\n".join(parts)


def _escape_html(text: str) -> str:
    """_escape_html 实现。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")
    )


# ── CLI 入口点 ──


def diff_main(args: List[str]) -> int:
    """CLI 入口：python -m tools.data_pipeline diff 旧文件 新文件 [选项]

    用法::
        python -m tools.data_pipeline diff old.json new.json
        python -m tools.data_pipeline diff old.json new.json -o diff.html
        python -m tools.data_pipeline diff old.json new.json --format json
    """
    if not args or args[0] in ("--help", "-h"):
        print(_diff_help())
        return 0

    old_path = args[0]
    new_path = args[1] if len(args) > 1 else None

    if new_path is None:
        print("用法: python -m tools.data_pipeline diff <旧文件> <新文件> [选项]", file=__import__('sys').stderr)
        return 1

    output_path = None
    output_format = "text"

    i = 2
    while i < len(args):
        if args[i] == "-o" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--format" and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        else:
            print(f"未知参数: {args[i]}", file=__import__('sys').stderr)
            return 1

    try:
        from .readers.json_reader import read_json
        from .validators.schema_check import validate_all
    except ImportError:
        from tools.data_pipeline.readers.json_reader import read_json
        from tools.data_pipeline.validators.schema_check import validate_all

    try:
        old_data = read_json(old_path)
        new_data = read_json(new_path)
    except Exception as e:
        print(f"读取失败: {e}", file=__import__('sys').stderr)
        return 1

    old_errors = validate_all(old_data)
    new_errors = validate_all(new_data)

    result = compare_entities(old_data, new_data)

    if output_format == "html" or (output_path and output_path.endswith(".html")):
        content = render_html(result)
    elif output_format == "json":
        content = json.dumps(render_json(result), ensure_ascii=False, indent=2)
    else:
        content = render_text(result)

    if output_path:
        import os
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"差异报告已写入 {output_path}")
    else:
        print(content)

    return 0 if not result.has_changes else 2


def _diff_help() -> str:
    """_diff_help 实现。"""
    return """数据差异比较工具 — 对比两个标准 EntitySchema 文件

用法:
  python -m tools.data_pipeline diff <旧文件> <新文件>        # 终端文本输出
  python -m tools.data_pipeline diff <旧文件> <新文件> -o diff.html  # HTML 输出
  python -m tools.data_pipeline diff <旧文件> <新文件> --format json  # JSON 输出

参数:
  -o <路径>        输出到文件（扩展名决定格式）
  --format <格式>  输出格式: text / json / html
  --help           显示本帮助
"""
