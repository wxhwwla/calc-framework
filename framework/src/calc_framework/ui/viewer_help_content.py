# SPDX-License-Identifier: AGPL-3.0
"""CalcPackViewer 帮助内容。"""

from calc_framework.ui.help_dialog import HelpSection


def build_viewer_help() -> list[HelpSection]:
    """构造 CalcPackViewer 的使用说明帮助内容。"""
    return [
        HelpSection(
            category="入门",
            title="概述",
            content="""\
<h2>CalcPackViewer — 配置包查看器</h2>

<p>CalcPackViewer 是通用计算展示层，用于加载 .calcpack 文件并呈现交互式计算界面。<br>
支持实体选择、自定义输入和实时 DAG 求值。</p>

<h3>启动方式</h3>
<pre>python -m calc_framework.ui path/to/game.calcpack</pre>
<p>也可以从启动器拖拽 .calcpack 文件到窗口打开。</p>

<h3>主要功能</h3>
<ul>
<li>加载并渲染 .calcpack 配置包</li>
<li>实体选择（角色/武器/装备）</li>
<li>自定义用户输入（滑块/数字框/下拉框）</li>
<li>实时 DAG 求值与结果展示</li>
<li>插件管理（导入/打包/查看插件）</li>
<li>多主题切换</li>
</ul>
""",
        ),
        HelpSection(
            category="界面",
            title="界面布局",
            content="""\
<h2>界面布局</h2>

<h3>菜单栏</h3>
<ul>
<li><b>文件</b> — 打开 .calcpack、退出</li>
<li><b>工具</b> — 插件管理器（导入/打包/刷新插件）</li>
<li><b>主题</b> — 切换界面主题（多个预设主题可选）</li>
<li><b>布局</b> — 切换左侧/右侧面板显示</li>
<li><b>帮助</b> — 使用说明</li>
</ul>

<h3>主内容区</h3>
<p>加载 .calcpack 后，根据包定义显示：</p>
<ul>
<li><b>左侧面板</b> — 实体选择（下拉框选择角色/武器等）</li>
<li><b>中间面板</b> — DAG 求值结果与用户输入控件</li>
<li><b>右侧面板</b> — 详细数据/属性展示</li>
</ul>

<h3>状态栏</h3>
<p>底部显示当前加载的配置包路径和状态信息。</p>
""",
        ),
        HelpSection(
            category="操作",
            title="操作说明",
            content="""\
<h2>操作说明</h2>

<h3>打开配置包</h3>
<ul>
<li>菜单「文件 → 打开 .calcpack」选择文件</li>
<li>拖拽 .calcpack 文件到窗口</li>
<li>启动时命令行参数指定路径</li>
</ul>

<h3>使用计算器</h3>
<ol>
<li>在左侧面板选择实体（如选择角色）</li>
<li>中间面板会显示可调参数（滑块拖拽或数字输入）</li>
<li>结果面板实时更新 DAG 求值结果</li>
</ol>

<h3>插件管理</h3>
<ol>
<li>菜单「工具 → 插件管理器」打开插件管理对话框</li>
<li>可导入 .calcplugin 插件文件</li>
<li>可打包插件目录为 .calcplugin</li>
<li>插件加载后自动生效</li>
</ol>

<h3>切换主题</h3>
<p>菜单「主题」下选择不同预设主题，界面配色和样式会实时切换。</p>
""",
        ),
        HelpSection(
            category="常见问题",
            title="常见问题",
            content="""\
<h2>使用技巧与常见问题</h2>

<h3>快捷键</h3>
<ul>
<li><b>Ctrl+O</b> — 打开 .calcpack</li>
<li><b>Ctrl+Q</b> — 退出</li>
<li><b>Ctrl+B</b> — 切换左侧面板</li>
<li><b>Ctrl+R</b> — 切换右侧面板</li>
<li><b>F1</b> — 打开此使用说明</li>
</ul>

<h3>常见问题</h3>

<p><b>Q: .calcpack 文件在哪里？</b><br>
A: .calcpack 是由配置包设计器（<code>python -m tools.designer</code>）创建的压缩包文件。</p>

<p><b>Q: 支持的插件格式？</b><br>
A: 支持 .calcplugin 插件文件，包含扩展数据和计算逻辑。</p>

<p><b>Q: 如何自定义主题？</b><br>
A: 当前版本通过主题菜单切换预设主题。自定义主题需编辑配置文件。</p>
""",
        ),
    ]
