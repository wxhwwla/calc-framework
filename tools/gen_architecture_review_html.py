#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成架构审查 HTML 到系统临时目录（improve-codebase-architecture 技能用）。"""

from __future__ import annotations

import tempfile
import time
import webbrowser
from pathlib import Path

CANDIDATES = [
    {
        "num": "1",
        "strength": "Strong",
        "title": "将全量遍历编排移出 gui.py",
        "files": "gui.py · single_skill_search_runner · mvp_pipeline · search_results_view",
        "problem": (
            "计算与搜索区的线程、取消、预估、MVP 与弹窗仍挤在 DamageCalculatorApp；"
            "runner 几乎只是转发。删除 runner 不减少复杂度；预估路径未传 multi_skill_eval。"
        ),
        "solution": (
            "新增 calculation 侧 search_controller：统一 job 组装、estimate、run+cancel；"
            "GUI 只做适配器。"
        ),
        "wins": ["预估与实跑同一接口", "可无头测取消/进度", "gui.py 变薄易导航"],
        "mermaid": """flowchart TB
  subgraph before["Before"]
    G["gui.py"] --> J["job 组装 x2"]
    G --> T["threading + app.after"]
    E["estimate"] -.泄漏.-> M["缺 multi_skill_eval"]
  end
  subgraph after["After"]
    G2["gui 薄适配"] --> C["search_controller 深模块"]
    C --> R["estimate / run / cancel"]
  end""",
    },
    {
        "num": "2",
        "strength": "Strong",
        "title": "统一搜索 job 的敌方防御与 OptimizerConfig",
        "files": "single_skill_search_job · gui · enemy_params · loadout_optimizer",
        "problem": (
            "确认选择/预览用插件 enemy_defense；全量遍历 job 写死 100 防。"
            "OptimizerConfig 在 GUI 与 runner 各建一份，易漂移。"
        ),
        "solution": (
            "job 或 optimizer_config_for_job() 集中 DamageContext 与 config；"
            "estimate、MVP、GUI 共用。"
        ),
        "wins": ["预览与 TopN 同敌人", "单测可断言防御", "接缝即测试面"],
        "mermaid": """flowchart LR
  P["右侧乘区预览"] --> D1["enemy_defense 来自插件"]
  S["全量遍历 TopN"] --> D2["enemy_defense=100"]
  classDef leak stroke:#dc2626,stroke-width:2px
  class D2 leak""",
    },
    {
        "num": "3",
        "strength": "Strong",
        "title": "拆分 property_display：文案 vs CTk 渲染",
        "files": "property_display · preview_lines · test_property_display_*",
        "problem": (
            "confirm_selection 接口 15+ 参数，与实现同宽（浅模块）；"
            "纯文案与 destroy/grid 混在一起。"
        ),
        "solution": "display_lines.py（纯）+ display_view.py（CTk）；模式分派只保留一处。",
        "wins": ["行构建已有测", "CTk 可 mock 渲染", "新计算模式一处加"],
        "mermaid": None,
    },
    {
        "num": "4",
        "strength": "Strong",
        "title": "LoadoutState 值对象（GUI↔calculation 接缝）",
        "files": "gui · confirm_refresh · enhancement_controls · damage_snapshot · gui_fixtures",
        "problem": (
            "角色/武器/固定配装/多技能次数/敌人防御在 N 处从 panel 刮取；"
            "MockSelectionPanel 手工同步 API。"
        ),
        "solution": (
            "loadout_state.read_from_panels() → 预设、确认签名、搜索 job、伤害快照共用。"
        ),
        "wins": ["新字段只改一处", "预设与搜索对齐", "Mock 只实现一个读法"],
        "mermaid": None,
    },
    {
        "num": "5",
        "strength": "Worth exploring",
        "title": "提取计算与搜索区控件",
        "files": "gui._build_control_panel · fixed_loadout_controls · search_settings",
        "problem": (
            "固定配装、工具与分享已抽出；全量按钮/并行/预估仍内联 gui，"
            "与 enhancement_controls 不对称。"
        ),
        "solution": "search_controls.place_search_section() + 句柄；绑定 search_controller。",
        "wins": ["与 enhancement 同模式", "控件可集成测", "搜索文案集中"],
        "mermaid": None,
    },
    {
        "num": "6",
        "strength": "Worth exploring",
        "title": "GameDataFacade 统一加载",
        "files": "loader · equipment_catalog · gui 启动 · enhancement_controls",
        "problem": (
            "启动只缓存武器；装备按装备范围懒加载；多方案对比直接 get_equipments()。"
            "三种入口，失败时机不一。"
        ),
        "solution": "应用持 facade：角色/武器/范围 catalog，统一 DataLoadError。",
        "wins": ["一处 mock 适配器", "全量前即知数据坏", "符合统一加载层"],
        "mermaid": None,
    },
]

BADGE = {
    "Strong": "bg-emerald-100 text-emerald-800",
    "Worth exploring": "bg-amber-100 text-amber-800",
    "Speculative": "bg-slate-200 text-slate-700",
}


def _card(c: dict) -> str:
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
    cards = "".join(_card(c) for c in CANDIDATES)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Architecture review — endfield_damage_calculator</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, theme: "neutral", securityLevel: "loose" }});
  </script>
</head>
<body class="bg-stone-50 text-slate-900 font-sans">
<main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
<header class="border-b border-stone-200 pb-8">
  <p class="text-xs uppercase tracking-wider text-slate-500">2026-05-23 · endfield_damage_calculator</p>
  <h1 class="text-3xl font-serif mt-2">架构加深机会</h1>
  <p class="text-sm text-slate-600 mt-3">术语：module · interface · implementation · depth · seam · adapter · leverage · locality（见技能 LANGUAGE.md）</p>
</header>
<section id="candidates" class="space-y-10">{cards}</section>
<section id="top-recommendation" class="rounded-xl border-2 border-emerald-600 bg-emerald-50 p-6">
  <h2 class="text-lg font-serif text-emerald-900">Top recommendation</h2>
  <p class="mt-2 text-emerald-900"><strong>#1 + #2</strong>：全量遍历/MVP 迁入 calculation 深模块，并统一 job 的敌方防御与 OptimizerConfig（修复预估与实跑、预览与 TopN 的接缝泄漏）。随后 <strong>#4 LoadoutState</strong> 统一确认/预设/搜索的刮取。</p>
</section>
</main>
</body>
</html>"""


def main() -> None:
    path = Path(tempfile.gettempdir()) / f"architecture-review-{int(time.time())}.html"
    path.write_text(build_html(), encoding="utf-8")
    print(path)
    webbrowser.open(path.as_uri())


if __name__ == "__main__":
    main()
