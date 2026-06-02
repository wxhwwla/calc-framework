# SPDX-License-Identifier: AGPL-3.0
"""帮助文档 — 节点类型相关说明。"""

from .help_content import HelpSection


def _node_types() -> HelpSection:
    return HelpSection(
        category="节点类型",
        title="节点类型详解",
        content="""\
<h2>节点类型详解</h2>

<p>编辑器支持多种节点类型，每种类型有不同的功能和配置选项。</p>
""",
        sub_sections=[
            HelpSection(
                category="节点类型",
                title="常量（const）",
                content="""\
<h3>常量节点（const）</h3>

<p>定义一个固定数值，输出始终为该数值。</p>

<h4>配置参数</h4>
<ul>
<li><b>数值</b> — 浮点数，节点输出的固定值（范围：+-1e9，精度：4 位小数）</li>
</ul>

<h4>用途</h4>
<ul>
<li>作为二元运算的基准值（如加 1、乘 2）</li>
<li>定义公式中的固定系数</li>
<li>条件节点的基准比较值</li>
</ul>
""",
            ),
            HelpSection(
                category="节点类型",
                title="变量引用（var）",
                content="""\
<h3>变量引用节点（var）</h3>

<p>引用外部数据源中的变量值。运行时从数据上下文（DataContext）中按路径取值。</p>

<h4>配置参数</h4>
<ul>
<li><b>变量路径</b> — 字符串，如 <code>character.基础攻击</code>、<code>weapon.攻击力+</code></li>
</ul>

<h4>路径格式</h4>
<p>变量路径使用点分格式：<code>数据源.字段名</code></p>
<ul>
<li><code>character.xxx</code> — 角色属性</li>
<li><code>weapon.xxx</code> — 武器属性</li>
<li><code>equipment.xxx</code> — 装备属性</li>
<li><code>enemy.xxx</code> — 敌方属性</li>
<li><code>computed.xxx</code> — 中间计算结果</li>
</ul>

<h4>注意</h4>
<p>变量路径必须在图的 <code>external_variables</code> 中有对应的变量声明，否则编译时会自动按默认类型补全。</p>
""",
            ),
            HelpSection(
                category="节点类型",
                title="用户输入（user_input）",
                content="""\
<h3>用户输入节点（user_input）</h3>

<p>运行时由用户提供的数值输入。在 ComputeSheet 中会自动生成为可编辑控件。</p>

<h4>配置参数</h4>
<ul>
<li><b>默认值</b> — 初始数值</li>
<li><b>最小值</b> — 允许的最小值</li>
<li><b>最大值</b> — 允许的最大值</li>
<li><b>步长</b> — 滑块/微调框的步进值</li>
</ul>

<h4>控件类型推断</h4>
<p>根据配置自动推断界面控件类型：</p>
<ul>
<li><code>float</code> / <code>int</code> 类型 + min/max → 滑块 + 数字微调框</li>
<li><code>bool</code> 类型 → 开关/复选框</li>
<li><code>str</code> 类型 → 下拉选择框</li>
</ul>
""",
            ),
            HelpSection(
                category="节点类型",
                title="一元运算（unary）",
                content="""\
<h3>一元运算节点（unary）</h3>

<p>对单个输入值执行数学运算，输出计算结果。</p>

<h4>输入</h4>
<ul><li><b>值</b> — 待运算的数值（连接上一个节点的输出）</li></ul>

<h4>支持的运算</h4>
<table border="1" cellpadding="4" style="border-collapse: collapse;">
<tr><th>操作</th><th>说明</th><th>示例（输入=4）</th></tr>
<tr><td>neg</td><td>取反（正变负，负变正）</td><td>-4</td></tr>
<tr><td>floor</td><td>向下取整</td><td>4</td></tr>
<tr><td>ceil</td><td>向上取整</td><td>4</td></tr>
<tr><td>abs</td><td>绝对值</td><td>4</td></tr>
<tr><td>sqrt</td><td>平方根</td><td>2</td></tr>
<tr><td>ln</td><td>自然对数（以 e 为底）</td><td>~1.386</td></tr>
<tr><td>log10</td><td>常用对数（以 10 为底）</td><td>~0.602</td></tr>
<tr><td>sin</td><td>正弦（输入为弧度）</td><td>~-0.757</td></tr>
<tr><td>cos</td><td>余弦（输入为弧度）</td><td>~-0.653</td></tr>
<tr><td>tan</td><td>正切（输入为弧度）</td><td>~1.158</td></tr>
</table>

<h4>注意</h4>
<ul>
<li><b>sqrt</b> — 输入必须 >= 0，否则会报运行时错误</li>
<li><b>ln / log10</b> — 输入必须 > 0</li>
<li>三角函数使用<b>弧度制</b>，如需角度请先做角度转弧度（x pi / 180）</li>
</ul>
""",
            ),
            HelpSection(
                category="节点类型",
                title="二元运算（binary）",
                content="""\
<h3>二元运算节点（binary）</h3>

<p>对两个输入值执行数学运算，支持 8 种运算操作。</p>

<h4>输入</h4>
<ul>
<li><b>左值</b> — 左侧操作数</li>
<li><b>右值</b> — 右侧操作数</li>
</ul>

<h4>支持的运算</h4>
<table border="1" cellpadding="4" style="border-collapse: collapse;">
<tr><th>操作</th><th>说明</th><th>示例</th></tr>
<tr><td>+</td><td>加法</td><td>3 + 5 = 8</td></tr>
<tr><td>-</td><td>减法</td><td>10 - 3 = 7</td></tr>
<tr><td>*</td><td>乘法</td><td>4 x 3 = 12</td></tr>
<tr><td>/</td><td>除法（浮点数）</td><td>10 / 3 = 3.3333</td></tr>
<tr><td>^</td><td>乘方（幂运算）</td><td>2 ^ 3 = 8</td></tr>
<tr><td>mod</td><td>取模（求余数）</td><td>7 mod 3 = 1</td></tr>
<tr><td>min</td><td>取最小值</td><td>min(3, 7) = 3</td></tr>
<tr><td>max</td><td>取最大值</td><td>max(3, 7) = 7</td></tr>
</table>

<h4>注意</h4>
<ul>
<li>除法运算符（/）始终执行浮点数除法，不会发生整数截断</li>
<li>乘方运算符（^）支持实数指数，如 4 ^ 0.5 = 2（平方根）</li>
</ul>
""",
            ),
            HelpSection(
                category="节点类型",
                title="条件判断（condition）",
                content="""\
<h3>条件判断节点（condition）</h3>

<p>根据条件选择输出值之一。类似编程中的三目运算符 <code>条件 ? 真值 : 假值</code>。</p>

<h4>输入</h4>
<ul>
<li><b>Port 0（条件）</b> — 数值型条件：0 为假，非 0 为真</li>
<li><b>Port 1（真值）</b> — 条件成立时输出的值</li>
<li><b>Port 2（假值）</b> — 条件不成立时输出的值</li>
</ul>

<h4>行为</h4>
<p>条件输入值为 0 时输出假值，非 0 时输出真值。</p>
""",
            ),
            HelpSection(
                category="节点类型",
                title="输出标记（output）",
                content="""\
<h3>输出标记节点（output）</h3>

<p>标记某个计算结果为重要输出。编译器会自动收集图中所有 output 节点作为命名输出。</p>

<h4>特点</h4>
<ul>
<li>本身不执行计算，仅作为标记</li>
<li>编译时自动回溯到其输入源节点</li>
<li>图中所有 output 节点都会被自动识别为命名输出</li>
</ul>

<h4>用法</h4>
<p>把 output 节点连到计算链的末端即可。无需额外配置。</p>
""",
            ),
            HelpSection(
                category="节点类型",
                title="复合节点（composite）",
                content="""\
<h3>复合节点</h3>

<p>把一整张子图封装成一个节点。通过导入 JSON 或 ZIP 包生成。</p>

<h4>特点</h4>
<ul>
<li>端口由子图中的 user_input 和 output 节点自动推断</li>
<li>双击可打开子图编辑器，修改内部计算逻辑</li>
<li>可打包成 ZIP 文件分发</li>
</ul>

<h4>导入方式</h4>
<ul>
<li>切换到左侧面板的<b>包</b>选项卡</li>
<li>点击<b>+ 导入包</b>按钮</li>
<li>选择 .json 文件（单个复合节点）或 .zip 文件（多个复合节点）</li>
</ul>
""",
            ),
        ],
    )
