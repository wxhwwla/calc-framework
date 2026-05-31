# SPDX-License-Identifier: AGPL-3.0
"""数据设计器内置说明书内容。"""

from __future__ import annotations

from utils.gui_help_dialog import HelpSection


def build_designer_help() -> list[HelpSection]:
    return [
        _overview(),
        _inverse_tab(),
        _data_editor_tab(),
        _data_browser_tab(),
        _tools(),
        _tips(),
    ]


def _overview() -> HelpSection:
    return HelpSection(
        category="入门",
        title="概述",
        content="""\
<h2>数据设计器</h2>

<p>数据设计器是一个图形化数据管理工具，用于维护游戏的角色、武器和装备数据。<br>
支持公式反推、数据编辑、数据浏览三大功能，让不熟悉代码的人也能管理游戏数据。</p>

<h3>启动方式</h3>
<pre>python main_designer.py</pre>

<h3>三个页签</h3>
<ol>
<li><b>公式反推</b> — 从等级属性反推成长公式参数</li>
<li><b>数据编辑</b> — 图形化新增/编辑/删除角色、武器、装备数据</li>
<li><b>数据浏览</b> — 浏览角色/武器/装备的数据列表</li>
</ol>
""",
    )


def _inverse_tab() -> HelpSection:
    return HelpSection(
        category="公式反推",
        title="功能说明",
        content="""\
<h2>公式反推</h2>

<p>公式反推功能可以从已知的等级属性数据，反向推导出游戏使用的成长公式参数。<br>
适用于以下场景：</p>
<ul>
<li>知道角色在 1 级和 90 级的属性，想算出中间等级的成长规律</li>
<li>验证自己录入的数据是否符合游戏公式</li>
<li>分析不同星级/类型角色的成长差异</li>
</ul>

<h3>操作步骤</h3>
<ol>
<li>选择数据类型（如「属性 90 级」或「技能 9-12 级」）</li>
<li>在输入框中粘贴等级对应的数值数据</li>
<li>点击「计算」或「反推」按钮</li>
<li>查看结果：系统会显示推导出的公式参数和拟合曲线</li>
</ol>

<h3>支持的数据类型</h3>
<ul>
<li><b>属性 90 级</b> — 角色在 90 级时的各项属性值</li>
<li><b>技能 9-12 级</b> — 技能在不同等级下的倍率变化</li>
<li>其他自定义数据</li>
</ul>
""",
    )


def _data_editor_tab() -> HelpSection:
    return HelpSection(
        category="数据编辑",
        title="功能说明",
        content="""\
<h2>数据编辑</h2>

<p>图形化的数据管理界面，支持对角色、武器、装备数据进行增删改查操作。</p>

<h3>三个子页签</h3>

<h4>角色编辑</h4>
<ul>
<li>查看和编辑所有角色的属性数据</li>
<li>修改名称、类型、星级、能力值等</li>
<li>编辑技能 JSON 数据</li>
<li>保存后自动刷新缓存</li>
</ul>

<h4>武器编辑</h4>
<ul>
<li>查看和编辑所有武器的属性数据</li>
<li>修改基础攻击力、附加属性、特殊能力等</li>
<li>支持武器技能数据的编辑</li>
<li>保存后自动刷新缓存</li>
</ul>

<h4>装备编辑</h4>
<ul>
<li>查看和编辑所有装备的数据</li>
<li>修改装备属性、套装效果等</li>
<li>保存后自动刷新缓存</li>
</ul>

<h3>操作说明</h3>
<ul>
<li>点击数据行选中，底部详情面板会显示该条目的详细信息</li>
<li>修改完成后点击「保存」</li>
<li>每次保存后，计算器会使用最新数据</li>
</ul>
""",
    )


def _data_browser_tab() -> HelpSection:
    return HelpSection(
        category="数据浏览",
        title="功能说明",
        content="""\
<h2>数据浏览</h2>

<p>以列表形式展示角色、武器、装备的完整数据，便于查阅和核对。</p>

<h3>操作步骤</h3>
<ol>
<li>在顶部分类下拉框中选择数据类型（角色/武器/装备）</li>
<li>列表会展示所有数据条目</li>
<li>点击任意条目可以在右侧或底部查看详情</li>
</ol>

<h3>功能特点</h3>
<ul>
<li>列表模式：快速浏览所有数据</li>
<li>详情模式：点击条目查看完整数据结构</li>
<li>搜索过滤：支持按名称或关键字搜索</li>
<li>JSON 预览：以格式化 JSON 查看数据详情</li>
</ul>
""",
    )


def _tools() -> HelpSection:
    return HelpSection(
        category="工具",
        title="底栏工具",
        content="""\
<h2>底栏工具</h2>

<h3>BWIKI 同步</h3>
<p>点击底栏的绿色「BWIKI 同步」按钮，可以一键从终末地 Wiki 拉取最新数据：</p>
<ul>
<li>自动同步角色数据</li>
<li>自动同步武器数据</li>
<li>自动同步装备数据</li>
<li>同步完成后自动保存到本地</li>
</ul>
<p>适合在游戏版本更新后快速更新数据。</p>

<h3>数据录入</h3>
<p>「数据录入」页签提供了表单式的录入界面：</p>
<ul>
<li><b>角色录入</b> — 填写名称、类型、星级、能力值、基础攻击力、技能 JSON 即可新增角色</li>
<li><b>武器录入</b> — 填写名称、类型、星级、基础攻击力、附加属性、特殊能力即可新增武器</li>
</ul>
""",
    )


def _tips() -> HelpSection:
    return HelpSection(
        category="常见问题",
        title="使用技巧",
        content="""\
<h2>使用技巧与常见问题</h2>

<h3>技巧</h3>
<ul>
<li>修改数据后记得点「保存」，否则不会生效</li>
<li>公式反推时可以多次调整输入数据，对比不同结果</li>
<li>数据浏览时可以用筛选功能快速定位目标条目</li>
<li>新增角色或武器后，回到计算器需要刷新才能看到新数据</li>
</ul>

<h3>常见问题</h3>

<p><b>Q: 修改数据后计算器没有变化？</b><br>
A: 数据设计器和计算器共享同一份数据文件。保存后重启计算器或点击「确认选择」即可看到变化。</p>

<p><b>Q: 如何备份数据？</b><br>
A: 数据文件位于 <code>calc_engine/endfield/data/</code> 目录下，可以直接复制备份。</p>

<p><b>Q: 批量新增角色/武器？</b><br>
A: 使用「数据录入」页签可以逐个录入。批量操作需要使用脚本工具。</p>
""",
    )
