# SPDX-License-Identifier: AGPL-3.0
"""启动器内置说明书内容。"""



from __future__ import annotations



from utils.gui.help_dialog import HelpSection





def build_launcher_help() -> list[HelpSection]:

    return [

        _overview(),

        _tools(),

        _calcpack(),

        _tips(),

    ]





def _overview() -> HelpSection:

    return HelpSection(

        category="入门",

        title="概述",

        content="""\

<h2>Game Calc Platform — 统一启动器</h2>



<p>这是所有工具的<b>统一入口</b>，让你可以一站式启动所有功能。<br>

无需记住各种命令，点击按钮即可打开对应的工具。</p>



<h3>启动方式</h3>

<pre>python main_launcher.py</pre>



<h3>界面说明</h3>

<p>启动器窗口显示为卡片网格布局：</p>

<ul>

<li>上半部分：已安装的游戏适配器（以卡片形式展示）</li>

<li>下半部分：工具按钮区域</li>

<li>状态栏：当前适配器状态、版本号</li>

</ul>

""",

    )





def _tools() -> HelpSection:

    return HelpSection(

        category="工具",

        title="工具按钮说明",

        content="""\

<h2>工具按钮</h2>



<p>启动器提供了以下工具入口：</p>



<h3>终末地计算器</h3>

<p>伤害计算主工具。选择角色和武器，查看详细的伤害乘区分析。<br>

适合日常计算和配装优化。</p>



<h3>数据设计器</h3>

<p>数据管理工具。维护角色、武器、装备数据。<br>

适合数据维护者。</p>

""",

    )





def _calcpack() -> HelpSection:

    return HelpSection(

        category="配置包",

        title=".calcpack 文件说明",

        content="""\

<h2>.calcpack 配置包</h2>



<p><code>.calcpack</code> 是工具的配置包文件格式，一个文件包含了完整的计算器配置：</p>

<ul>

<li>DAG 计算逻辑</li>

<li>游戏数据</li>

<li>UI 布局定义</li>

<li>主题样式</li>

</ul>



<h3>打开 .calcpack 文件</h3>

<p>有两种方式：</p>

<ul>

<li>拖拽 <code>.calcpack</code> 文件到启动器窗口</li>

<li>命令行指定：<code>python main_launcher.py path/to/game.calcpack</code></li>

</ul>



<h3>创建 .calcpack</h3>

<p>使用「配置包设计器」工具（<code>python -m tools.designer</code>）来创建和编辑配置包。</p>

""",

    )





def _tips() -> HelpSection:

    return HelpSection(

        category="常见问题",

        title="使用技巧",

        content="""\

<h2>使用技巧</h2>



<h3>快速启动特定工具</h3>

<p>如果不想通过启动器选，可以直接运行对应的入口文件：</p>

<ul>

<li><code>python main.py</code> — 直接启动计算器</li>

<li><code>python main_designer.py</code> — 直接启动数据设计器</li>

</ul>



<h3>适配器切换</h3>

<p>如果有安装其他游戏的适配器，启动器会以卡片形式展示。点击卡片即可切换到该游戏的计算器。</p>

""",

    )

