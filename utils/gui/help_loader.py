# SPDX-License-Identifier: AGPL-3.0
"""从 docs/ 目录加载说明书内容到 HelpSection。"""

from __future__ import annotations

from pathlib import Path

from utils.gui.help_dialog import HelpSection

_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "docs"
_MANUAL_PATH = _DOCS_DIR / "制造游戏计算器完整流程.md"


def _markdown_to_html(md_text: str) -> str:
    """简单的 markdown 子集 → HTML 转换（只为文档中的标题/列表/表格/代码块）。"""
    lines = md_text.split("\n")
    out: list[str] = []
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                out.append("</pre>")
                in_code = False
            else:
                out.append("<pre>")
                in_code = True
            continue
        if in_code:
            out.append(line)
            continue
        if stripped.startswith("### "):
            out.append(f"<h4>{stripped[4:]}</h4>")
        elif stripped.startswith("## "):
            out.append(f"<h3>{stripped[3:]}</h3>")
        elif stripped.startswith("# "):
            out.append(f"<h2>{stripped[2:]}</h2>")
        elif stripped.startswith("- **") and "** —" in stripped:
            # "  - **控件名** — 说明"
            label, desc = stripped.split("** —", 1)
            out.append(f"<li><b>{label[4:]}</b> — {desc}</li>")
        elif stripped.startswith("- "):
            out.append(f"<li>{stripped[2:]}</li>")
        elif stripped.startswith("|") and stripped.endswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if all(c.startswith("-") or c == "" for c in cols):
                continue
            out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cols) + "</tr>")
        elif stripped:
            out.append(f"<p>{stripped}</p>")
    return "\n".join(out)


def load_section(
    heading: str,
    *,
    category: str = "完整手册",
    title: str | None = None,
) -> HelpSection | None:
    """从完整流程文档中加载指定标题下的内容。

    参数:
        heading: markdown 标题文本（如 "GUI ①：DAG 图编辑器"）。
        category: HelpSection 的 category。
        title: 显示标题，默认与 heading 相同。

    返回:
        HelpSection 或 None（文件不存在 / 未找到）。
    """
    if not _MANUAL_PATH.exists():
        return None

    md = _MANUAL_PATH.read_text(encoding="utf-8")
    lines = md.split("\n")

    start_idx = -1
    end_idx = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and heading in stripped:
            start_idx = i
            break
    if start_idx == -1:
        return None

    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("## ") and "GUI" not in stripped:
            end_idx = i
            break

    section_lines = lines[start_idx:end_idx]
    html = _markdown_to_html("\n".join(section_lines))
    return HelpSection(
        category=category,
        title=title or heading,
        content=html,
    )


def load_multi_category(
    categories: dict[str, list[str]],
) -> list[HelpSection]:
    """批量加载多个分类及其子主题。

    参数:
        categories: { "分类名": ["标题A", "标题B"] }

    返回:
        合并后的 HelpSection 列表，每个分类一个顶层节点。
    """
    result: list[HelpSection] = []
    for cat, headings in categories.items():
        sections: list[HelpSection] = []
        for h in headings:
            sec = load_section(h, category=cat)
            if sec:
                sections.append(sec)
        if sections:
            result.append(
                HelpSection(
                    category=cat,
                    title=cat,
                    content="<h3>完整手册参考</h3><p>以下内容摘自 <code>docs/制造游戏计算器完整流程.md</code>。</p>",
                    sub_sections=sections,
                )
            )
    return result
