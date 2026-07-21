#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0


# SPDX-License-Identifier: AGPL-3.0
"""生成架构审查 HTML 到系统临时目录（improve-codebase-architecture 技能用）。"""

from __future__ import annotations


import tempfile

import time

import webbrowser

from pathlib import Path


# 2026-05 第一轮+第二轮均已落地；若再生成报告请改 CANDIDATES 为第三轮新接缝

CANDIDATES = [
    {
        "num": "1",
        "strength": "Strong",
        "title": "瘦化 gui.py：确认编排 + 多技能次数区",
        "files": "gui.py · confirm_refresh · loadout_state · (new) multi_skill_controls.py",
        "problem": (
            "search_controls / enhancement_controls 已抽出，但 gui 仍含 ~200 行确认去重、"
            "多技能次数区与五列 grid 接线；_resolve_selected_skill 与 loadout_state 重复且 gui 内未用。"
        ),
        "solution": (
            "place_multi_skill_section() 对称 search_controls；ConfirmOrchestrator 管签名/合并/失焦；"
            "gui 仅窗口与面板生命周期。"
        ),
        "wins": ["确认语义一处", "底栏两列对称", "删重复技能解析"],
        "mermaid": """flowchart LR

  subgraph before["Before"]

    G["gui.py ~860L"] --> C["确认编排"]

    G --> M["多技能次数区"]

  end

  subgraph after["After"]

    G2["gui 薄壳"] --> CO["ConfirmOrchestrator"]

    G2 --> MSC["multi_skill_controls"]

    CO --> LS["LoadoutState"]

  end""",
    },
    {
        "num": "2",
        "strength": "Strong",
        "title": "LoadoutState → DisplayRequest（确认与右侧乘区）",
        "files": "loadout_state · display_view · game_data_facade · gui._run_confirm",
        "problem": (
            "_run_confirm 仍手工传 12+ 参数进 confirm_selection，display 路径再次刮 panel；"
            "LoadoutState 已含模式/范围/固定配装/次数，但未作为 display 唯一输入。"
        ),
        "solution": (
            "to_display_request(game_data) 含 catalog 与武器候选；"
            "confirm_selection(DisplayRequest, scrolls) 内部分派计算模式。"
        ),
        "wins": ["确认与乘区同一次刮取", "测 DisplayRequest 非 CTk", "catalog 走 GameDataFacade"],
        "mermaid": """flowchart TB

  LS[LoadoutState] --> DR[DisplayRequest]

  GDF[GameDataFacade] --> DR

  DR --> DV[display_view]

  DR --> PL[preview_lines 格式化]""",
    },
    {
        "num": "3",
        "strength": "Strong",
        "title": "统一 LoadoutEvaluation（预览 / 单段 / 仪表盘）",
        "files": "preview_lines · display_lines · damage_snapshot · preview_cache",
        "problem": (
            "单段伤害、单/多技能快速预览、伤害仪表盘三条路径各自算 final_attack 与技能场景；"
            "preview_lines 仍直调 get_equipment_catalog，绕过 GameDataFacade。"
        ),
        "solution": (
            "calculation 层 LoadoutEvaluation：一次求值 → 行文案 / DamageSnapshot 格式化；"
            "preview 与确认共用 preview_cache 失效面。"
        ),
        "wins": ["预览与仪表盘数字一致", "一处缓存失效", "门面无旁路"],
        "mermaid": None,
    },
    {
        "num": "4",
        "strength": "Worth exploring",
        "title": "退役 property_display 再导出门面",
        "files": "property_display.py · tests · gui.py imports",
        "problem": (
            "property_display 仅 re-export display_* / preview_lines；删除测试不通过但复杂度不收敛（浅模块）。"
            "测试与 gui 仍经此间接 import，真实 seam 被遮住。"
        ),
        "solution": "调用方改 import display_view / display_lines；保留短期 shim 后删除。",
        "wins": ["删 pass-through", "import 图清晰", "测试对准真实模块"],
        "mermaid": None,
    },
    {
        "num": "5",
        "strength": "Worth exploring",
        "title": "合并全量遍历执行栈 SearchRunner",
        "files": "search_session · in_memory_optimizer · search_persistence · single_skill_search_runner",
        "problem": (
            "search_session / in_memory_optimizer / search_persistence 薄转发重复 bounded parallel；"
            "续跑与内存路径 evaluator 易漂移。"
        ),
        "solution": (
            "SearchRunner.run(job, persistence?) 统一 plan、evaluator、TopN、cancel；"
            "estimate 只经 optimizer_config_for_search_job。"
        ),
        "wins": ["取消/进度一处修", "可无头测全量遍历", "MVP 与内存同栈"],
        "mermaid": """flowchart LR

  SC[search_controller] --> Job[SingleSkillSearchJob]

  Job --> SR[SearchRunner]

  SR --> LO[evaluate_task]

  SR --> PS[run_bounded_parallel]""",
    },
    {
        "num": "6",
        "strength": "Worth exploring",
        "title": "enhancement 与 DamageSnapshot 接 LoadoutState",
        "files": "enhancement_controls · damage_snapshot · preset_batch_compare",
        "problem": (
            "refresh_damage_snapshot 确认后再次刮 panel；build_preset_from_app 仍有 panel fallback；"
            "enhancement_controls 混 UI 与预设/对比逻辑。"
        ),
        "solution": ("refresh_from_state(state)；拆分 preset_dialogs；多方案对比只读 game_data 三列表。"),
        "wins": ["仪表盘与右侧乘区同源", "预设测 LoadoutState", "CTk 与逻辑分离"],
        "mermaid": None,
    },
]


BADGE = {
    "Strong": "bg-emerald-100 text-emerald-800",
    "Worth exploring": "bg-amber-100 text-amber-800",
    "Speculative": "bg-slate-200 text-slate-700",
}


def _card(c: dict) -> str:
    """_card 实现。"""
    mermaid_block = ""

    if c.get("mermaid"):
        mermaid_block = (
            f'<div class="rounded-lg border border-slate-200 bg-stone-50 p-3 mb-4">'
            f'<pre class="mermaid text-sm">{c["mermaid"]}</pre></div>'
        )

    wins = "".join(f"<li>{w}</li>" for w in c["wins"])

    return f"""

<article class="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

  <div class="flex flex-wrap items-center gap-2 mb-4">

    <h2 class="text-xl font-serif">{c["num"]}. {c["title"]}</h2>

    <span class="text-xs uppercase tracking-wider px-2 py-0.5 rounded {BADGE[c["strength"]]}">{c["strength"]}</span>

  </div>

  <p class="font-mono text-sm text-slate-600 mb-4">{c["files"]}</p>

  <div class="grid md:grid-cols-2 gap-4 mb-4">

    <div>

      <p class="text-xs uppercase tracking-wider text-slate-500 mb-2">Before · shallow</p>

      <div class="space-y-1">

        <div class="h-16 border-2 border-slate-400 rounded flex items-center justify-center text-xs">interface 宽</div>

        <div class="h-14 border border-slate-300 bg-slate-100 rounded flex items-center justify-center text-xs">implementation</div>

      </div>

    </div>

    <div>

      <p class="text-xs uppercase tracking-wider text-slate-500 mb-2">After · deep</p>

      <div class="space-y-1">

        <div class="h-5 bg-slate-900 rounded flex items-center justify-center text-xs text-white">小接口</div>

        <div class="h-20 bg-slate-800 rounded flex items-center justify-center text-xs text-slate-200">内聚 implementation</div>

      </div>

    </div>

  </div>

  {mermaid_block}

  <p class="text-sm"><strong>Problem:</strong> {c["problem"]}</p>

  <p class="text-sm mt-2"><strong>Solution:</strong> {c["solution"]}</p>

  <ul class="mt-3 text-sm text-slate-700 list-disc pl-5">{wins}</ul>

</article>"""


def build_html() -> str:
    """生成架构审查的 HTML 页面内容。"""

    cards = "".join(_card(c) for c in CANDIDATES)

    return f"""<!doctype html>

<html lang="zh-CN">

<head>

  <meta charset="utf-8" />

  <title>Architecture review — calc-framework</title>

  <script src="https://cdn.tailwindcss.com"></script>

  <script type="module">

    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";

    mermaid.initialize({{ startOnLoad: true, theme: "neutral", securityLevel: "loose" }});

  </script>

</head>

<body class="bg-stone-50 text-slate-900 font-sans">

<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">

<header class="border-b border-stone-200 pb-8">

  <p class="text-xs uppercase tracking-wider text-slate-500">2026-05-23 · 第二轮审查 · calc-framework</p>

  <h1 class="text-3xl font-serif mt-2">架构加深机会（post #1–#6）</h1>

  <p class="text-sm text-slate-600 mt-3">已完成：search_controller · LoadoutState · display_lines/view · search_controls · GameDataFacade。术语见 LANGUAGE.md。</p>

</header>

<section id="candidates" class="space-y-10">{cards}</section>

<section id="top-recommendation" class="rounded-xl border-2 border-emerald-600 bg-emerald-50 p-6">

  <h2 class="text-lg font-serif text-emerald-900">Top recommendation</h2>

  <p class="mt-2 text-emerald-900"><strong>#1 + #2</strong>：在已有 LoadoutState / GameDataFacade 上，抽出 ConfirmOrchestrator + multi_skill_controls，并让 <code>DisplayRequest</code> 成为确认刷新与右侧乘区的唯一接口——locality 最高、与上轮接缝直接衔接。</p>

</section>

</main>

</body>

</html>"""


def main() -> None:
    """CLI 入口：生成架构审查 HTML 文件并在浏览器中打开。"""
    path = Path(tempfile.gettempdir()) / f"architecture-review-{int(time.time())}.html"

    path.write_text(build_html(), encoding="utf-8")

    print(path)

    webbrowser.open(path.as_uri())


if __name__ == "__main__":
    main()
