"""帮助文档内容 — 集中管理所有使用说明文本。"""

from dataclasses import dataclass, field


@dataclass
class HelpSection:
    """帮助文档中的一个分类。"""
    category: str
    title: str
    content: str
    sub_sections: list["HelpSection"] = field(default_factory=list)


def build_help_tree() -> list[HelpSection]:
    """构建完整的帮助文档树。"""
    return [
        _overview(),
        _interface(),
        _node_types(),
        _operations(),
        _file_ops(),
        _layout_mgmt(),
        _preview(),
        _shortcuts(),
        _config(),
        _compilation(),
        _format(),
    ]


def _overview() -> HelpSection:
    return HelpSection(
        category="入门",
        title="概述",
        content="""\
<h2>公式计算图编辑器</h2>

<p>公式计算图编辑器是一个<strong>可视化节点编程工具</strong>，允许用户通过拖拽和连线的方式构建数学计算流程，并将计算结果导出为 JSON 格式供其他工具使用。</p>

<h3>核心概念</h3>
<ul>
<li><b>节点（Node）</b> — 计算的基本单元，每个节点执行一个特定的操作（常量、变量引用、运算等）</li>
<li><b>连线（Wire）</b> — 节点之间的数据流通路，将一个节点的输出连接到另一个节点的输入</li>
<li><b>图（Graph）</b> — 节点和连线的集合，构成完整的计算流程</li>
<li><b>Section（节）</b> — 用于组织输出节点的分组，方便在结果展示中按模块排列</li>
</ul>

<h3>工作流程</h3>
<ol>
<li>从左侧节点面板拖拽节点到画布</li>
<li>连线：从输出端口拖到输入端口</li>
<li>选中节点，在右侧属性面板中配置参数</li>
<li>在排版面板中添加 Section，指定哪些节点为输出</li>
<li>保存为 .json 文件，或直接查看实时预览结果</li>
</ol>

<h3>适用场景</h3>
<ul>
<li>游戏数值公式设计与调试</li>
<li>多步数学计算流程的可视化构建</li>
<li>计算逻辑的文档化存档与分享</li>
<li>与 DAG 计算引擎集成，进行批量求值</li>
</ul>
""",
    )


def _interface() -> HelpSection:
    return HelpSection(
        category="入门",
        title="界面布局",
        content="""\
<h2>界面布局</h2>

<p>编辑器采用经典的三栏布局：</p>

<h3>左栏：节点面板（NodePanel）</h3>
<p>按分类列出所有可用的节点类型。点击并拖拽到中间的画布即可创建一个节点。</p>
<ul>
<li><b>基础</b> — 常量、一元运算、二元运算、条件判断</li>
<li><b>输入</b> — 变量引用、用户输入</li>
<li><b>输出</b> — 输出标记节点</li>
</ul>

<h3>中栏：画布（Canvas）</h3>
<p>可视化编辑的主工作区：</p>
<ul>
<li>拖拽节点调整位置</li>
<li>从端口拖出连线</li>
<li>点击选择节点（显示为虚线边框）</li>
<li>按 Delete 键删除选中节点及关联的连线</li>
<li>任意位置单击取消选择</li>
</ul>

<h3>右栏：排版 + 属性面板</h3>
<p>分为上下两部分：</p>
<ul>
<li><b>上：排版面板（LayoutPanel）</b> — 管理输出分组 Section，添加/删除/设置列数</li>
<li><b>下：属性面板（PropPanel）</b> — 编辑选中节点的详细参数，底部显示实时预览值</li>
</ul>
""",
    )


def _node_types() -> HelpSection:
    return HelpSection(
        category="节点类型",
        title="节点类型详解",
        content="""\
<h2>节点类型详解</h2>

<p>编辑器支持 7 种节点类型，每种类型有不同的功能和配置选项。</p>
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
<li><b>数值</b> — 浮点数，节点输出的固定值（范围：±1e9，精度：4 位小数）</li>
</ul>

<h4>用途</h4>
<ul>
<li>作为二元运算的基准值（如加 1、乘 2）</li>
<li>定义公式中的固定系数</li>
<li>条件节点的基准比较值</li>
</ul>

<h4>示例</h4>
<ul>
<li>设置数值为 100 → 输出 100</li>
<li>与变量节点连线做加法 → 实现偏移量</li>
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

<p>运行时由用户提供的数值输入。在 ComputeSheet（计算表）中会自动生成为可编辑控件。</p>

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
<tr><td>ln</td><td>自然对数（以 e 为底）</td><td>≈1.386</td></tr>
<tr><td>log10</td><td>常用对数（以 10 为底）</td><td>≈0.602</td></tr>
<tr><td>sin</td><td>正弦（输入为弧度）</td><td>≈-0.757</td></tr>
<tr><td>cos</td><td>余弦（输入为弧度）</td><td>≈-0.653</td></tr>
<tr><td>tan</td><td>正切（输入为弧度）</td><td>≈1.158</td></tr>
<tr><td>asin</td><td>反正弦（输出为弧度）</td><td>≈1.571</td></tr>
<tr><td>acos</td><td>反余弦（输出为弧度）</td><td>≈0</td></tr>
<tr><td>atan</td><td>反正切（输出为弧度）</td><td>≈1.326</td></tr>
</table>

<h4>注意</h4>
<ul>
<li><b>sqrt</b> — 输入必须 ≥ 0，否则会报运行时错误</li>
<li><b>ln / log10</b> — 输入必须 > 0</li>
<li><b>asin / acos</b> — 输入必须在 [-1, 1] 范围内</li>
<li>三角函数使用<b>弧度制</b>，如需角度请先做角度转弧度（× π / 180）</li>
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
<tr><td>*</td><td>乘法</td><td>4 × 3 = 12</td></tr>
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
<li>注意运算符优先级：目前 ^ 与 * / 同级，需用节点链保证正确顺序</li>
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

<h4>典型用法</h4>
<ul>
<li>与比较表达式（通过 expr 节点）配合实现 if-else 逻辑</li>
<li>做边界检查：如果数值超出范围则使用默认值</li>
<li>多条件嵌套：多个 condition 节点串联实现多路分支</li>
</ul>
""",
            ),
            HelpSection(
                category="节点类型",
                title="输出标记（output）",
                content="""\
<h3>输出标记节点（output）</h3>

<p>标记某个计算结果为"重要输出"，在图编译时会被纳入 outputs 区域。</p>

<h4>特点</h4>
<ul>
<li>本身不执行计算，仅作为标记</li>
<li>编译时自动回溯到其输入源节点</li>
<li>在排版面板中添加到 Section 后，输出结果会显示在对应分组中</li>
</ul>

<h4>与 Section 配合</h4>
<p>将 output 节点的 ID 添加到排版面板的 Section 中，即可将该计算结果归入特定的分组。</p>

<h4>示例</h4>
<ul>
<li>创建一个"最终攻击力"output 节点，连接到攻击力计算链的末端</li>
<li>在排版面板中添加"结果"Section，填入该 output 节点的 ID</li>
<li>编译后，"最终攻击力"会作为命名输出出现在结果中</li>
</ul>
""",
            ),
        ],
    )


def _operations() -> HelpSection:
    return HelpSection(
        category="操作指南",
        title="基本操作",
        content="""\
<h2>基本操作</h2>

<h3>创建节点</h3>
<ol>
<li>在左侧<b>节点面板</b>中浏览可用的节点类型</li>
<li>鼠标左键按住一个节点类型项</li>
<li>拖拽到中间的<b>画布</b>上松开</li>
<li>节点即出现在画布上，带有对应的颜色和端口</li>
</ol>

<h3>连接节点</h3>
<ol>
<li>鼠标左键按住节点右侧的<b>输出端口</b>（小圆圈）</li>
<li>拖拽到另一个节点左侧的<b>输入端口</b>上松开</li>
<li>一条贝塞尔曲线连线即建立完成</li>
<li>连线颜色与源节点的类型颜色一致</li>
</ol>

<h3>选择与编辑</h3>
<ul>
<li><b>单击节点</b> — 选中节点（显示虚线边框），右侧属性面板显示该节点的配置</li>
<li><b>单击空白处</b> — 取消选中</li>
<li><b>选中后</b> — 在属性面板中修改节点的各项参数（数值/路径/操作符等）</li>
<li><b>节点标签</b> — 可在属性面板的"名称"字段中修改显示名称</li>
</ul>

<h3>删除节点或连线</h3>
<ul>
<li><b>选中节点 → Delete 键</b> — 删除节点及其所有关联的连线</li>
<li>删除节点时，与之相连的所有连线会被自动清理</li>
</ul>

<h3>拖拽移动</h3>
<ul>
<li>鼠标左键按住节点标题区域拖拽，可调整节点在画布上的位置</li>
<li>位置信息会自动保存到 JSON 文件中</li>
</ul>
""",
    )


def _file_ops() -> HelpSection:
    return HelpSection(
        category="文件操作",
        title="文件操作",
        content="""\
<h2>文件操作</h2>

<h3>新建（Ctrl + N）</h3>
<p>清空当前画布、排版和属性面板，开始一个新的计算图。</p>
<ul>
<li><b>注意</b>：新建前请确保已保存当前工作，此操作不可撤销</li>
</ul>

<h3>打开（Ctrl + O）</h3>
<p>从 .json 文件加载之前保存的计算图。</p>
<ul>
<li>支持标准的 graph.json 格式文件</li>
<li>文件内容会自动校验完整性</li>
<li>加载成功后，画布、排版、节点位置将完全恢复到保存时的状态</li>
</ul>

<h3>保存（Ctrl + S）</h3>
<p>将当前编辑器的完整状态保存到 .json 文件。</p>
<ul>
<li>如果尚未指定文件名，会自动弹出"另存为"对话框</li>
<li>保存内容包括：所有节点信息、连线数据、排版 Section 配置、节点位置坐标</li>
<li>文件编码为 UTF-8，含 BOM</li>
</ul>

<h3>另存为（Ctrl + Shift + S）</h3>
<p>将当前状态另存为一个新的 .json 文件。</p>
<ul>
<li>始终弹出文件选择对话框</li>
<li>如果指定的文件名没有 .json 后缀，会自动添加</li>
</ul>

<h3>JSON 文件格式</h3>
<p>保存的文件格式是一个结构化 JSON 对象，包含以下顶层字段：</p>
<ul>
<li><code>schema_version</code> — 模式版本号（"calc-graph-v1"）</li>
<li><code>name</code> / <code>description</code> — 图的名示和描述</li>
<li><code>nodes</code> — 节点数组，每个节点包含 id/type/op/label/config/position</li>
<li><code>edges</code> — 连线数组，每条包含 from_node/from_port/to_node/to_port</li>
<li><code>layout</code> — 排版信息，包含 sections 数组</li>
<li><code>external_variables</code> — 外部变量声明</li>
</ul>
""",
    )


def _layout_mgmt() -> HelpSection:
    return HelpSection(
        category="排版管理",
        title="排版（Section）管理",
        content="""\
<h2>排版管理</h2>

<p>排版面板位于右侧上方，用于管理输出的分组方式。</p>

<h3>什么是 Section？</h3>
<p>Section（节）是输出节点的分组容器。一个图可以有多个 Section，每个 Section 包含一组输出节点的 ID。在最终结果展示中，不同 Section 的输出会分开显示。</p>

<h3>添加 Section</h3>
<ol>
<li>点击排版面板底部的 <b>+ 添加节</b> 按钮</li>
<li>系统自动生成一个新的 Section，带有一个自动 ID 和默认标题</li>
<li>在 Section 行中可设置列数（1-4 列）</li>
</ol>

<h3>Section 配置</h3>
<ul>
<li><b>标题</b> — 显示在 Section 顶部的名称</li>
<li><b>列数</b> — 该 Section 在结果展示时分为几列显示（1-4 列）</li>
<li><b>输出节点</b> — 该 Section 包含的输出节点 ID 列表</li>
</ul>

<h3>清空</h3>
<p>点击"清空"按钮可删除所有 Section。</p>

<h3>与 output 节点的关系</h3>
<p>Section 中的输出节点 ID 对应画布上的 output 类型节点的 ID。编译图时，编译器会解析 output 节点的输入源，将实际的计算结果与 Section 关联。</p>
""",
    )


def _preview() -> HelpSection:
    return HelpSection(
        category="实时预览",
        title="实时预览",
        content="""\
<h2>实时预览</h2>

<p>属性面板底部有一个"预览值"显示区，可以在编辑过程中实时查看选中节点的计算结果。</p>

<h3>工作方式</h3>
<ol>
<li><b>选择节点</b> → 自动编译当前整个图 → 调用 DAG 引擎求值</li>
<li>从 <code>DAGResult.node_values</code> 中提取选中节点的计算结果</li>
<li>在属性面板底部的"预览值"行中显示（天蓝色 Consolas 等宽字体）</li>
</ol>

<h3>自动更新时机</h3>
<ul>
<li>切换选择的节点</li>
<li>修改节点配置（数值/路径/操作符）</li>
<li>添加或删除节点</li>
<li>添加或删除连线</li>
</ul>

<h3>显示格式</h3>
<ul>
<li><b>数值</b> — 浮点数显示 6 位小数</li>
<li><b>字符串</b> — 按原样显示</li>
<li><b>无法计算</b> — 显示"(无法计算)"（通常是因为输入未完全连接）</li>
<li><b>错误</b> — 显示"错误: xxx"（编译或求值时发生异常，超长消息自动截断）</li>
<li><b>未选择</b> — 显示"—"</li>
</ul>

<h3>注意事项</h3>
<ul>
<li>实时预览会<b>编译整个图</b>再取单个节点的值，大图可能会有短暂延迟</li>
<li>如果图结构不完整（存在未连接的输入端口），被依赖的节点可能无法求值</li>
<li>预览使用的是 DAG 引擎的中间结果（node_values），不是 outputs</li>
</ul>
""",
    )


def _shortcuts() -> HelpSection:
    return HelpSection(
        category="快捷键",
        title="快捷键参考",
        content="""\
<h2>快捷键参考</h2>

<table border="1" cellpadding="6" style="border-collapse: collapse;">
<tr><th>快捷键</th><th>操作</th><th>说明</th></tr>
<tr><td><b>Ctrl + N</b></td><td>新建</td><td>清空当前图，开始新编辑</td></tr>
<tr><td><b>Ctrl + O</b></td><td>打开</td><td>从文件加载计算图</td></tr>
<tr><td><b>Ctrl + S</b></td><td>保存</td><td>保存当前图到文件</td></tr>
<tr><td><b>Ctrl + Shift + S</b></td><td>另存为</td><td>另存到新文件</td></tr>
<tr><td><b>Delete</b></td><td>删除选中节点</td><td>删除选中的节点及其所有连线</td></tr>
<tr><td><b>单击节点</b></td><td>选中</td><td>选中节点，显示属性面板</td></tr>
<tr><td><b>拖拽节点</b></td><td>移动</td><td>调整节点位置</td></tr>
<tr><td><b>端口拖拽</b></td><td>连线</td><td>从输出端口拖到输入端口建立连接</td></tr>
</table>

<h3>鼠标操作</h3>
<ul>
<li><b>左键拖拽</b> — 从节点面板拖出创建节点 / 从端口拖出建立连线 / 拖拽节点移动位置</li>
<li><b>左键单击</b> — 选中节点 / 取消选中</li>
</ul>
""",
    )


def _config() -> HelpSection:
    return HelpSection(
        category="配置详解",
        title="节点配置详解",
        content="""\
<h2>节点配置</h2>

<p>选中节点后，右侧属性面板会显示该节点可编辑的配置参数。不同节点类型有不同的配置项。</p>

<h3>通用配置</h3>
<ul>
<li><b>ID</b> — 节点的唯一标识（只读，创建时自动生成）</li>
<li><b>名称</b> — 节点的显示标签，可自定义</li>
<li><b>类型</b> — 节点的类型（只读）</li>
</ul>

<h3>常量节点</h3>
<ul>
<li><b>数值</b> — 设置固定输出值。支持 ±1e9 范围，4 位小数精度</li>
</ul>

<h3>变量引用节点</h3>
<ul>
<li><b>变量路径</b> — 点分格式的路径字符串，如 <code>character.基础攻击</code></li>
</ul>

<h3>用户输入节点</h3>
<ul>
<li><b>默认值</b> — 初始值</li>
<li><b>最小值</b> — 允许输入的最小值</li>
<li><b>最大值</b> — 允许输入的最大值</li>
<li><b>步长</b> — 调节步进（最小 0.001）</li>
</ul>

<h3>一元/二元运算节点</h3>
<ul>
<li><b>操作</b> — 下拉选择要执行的运算类型</li>
</ul>

<h3>配置修改后的效果</h3>
<ul>
<li>任何配置修改会立即通过 <code>node_changed</code> 信号同步到画布和预览</li>
<li>修改操作符后，实时预览会自动重新求值</li>
</ul>
""",
    )


def _compilation() -> HelpSection:
    return HelpSection(
        category="编译流程",
        title="编译与求值",
        content="""\
<h2>编译与求值流程</h2>

<p>图编辑器支持将可视化图编译为 DAG 引擎可执行格式，并进行求值计算。</p>

<h3>编译流程（GraphCompiler）</h3>
<p>编译过程分为以下步骤：</p>
<ol>
<li><b>端口映射</b> — 根据连线数据建立"目标节点端口 → 源节点"的映射关系</li>
<li><b>节点编译</b> — 将每个 GraphNode 转换为对应的 DAG 引擎节点类型：
<ul>
<li><code>const</code> → <code>ConstNode(value)</code></li>
<li><code>var</code> → <code>VarNode(path)</code></li>
<li><code>user_input</code> → <code>UserInputNode(default, min, max, step)</code></li>
<li><code>unary</code> → <code>UnaryNode(op, input)</code></li>
<li><code>binary</code> → <code>BinaryNode(op, lhs, rhs)</code></li>
<li><code>condition</code> → <code>ConditionNode(cond, true_val, false_val)</code></li>
</ul>
</li>
<li><b>变量声明</b> — 自动收集 var 节点中的路径，创建变量声明表</li>
<li><b>输出解析</b> — 解析 Section 中 output 节点的输入源，建立输出映射</li>
</ol>

<h3>求值流程（DAG Engine）</h3>
<ol>
<li><b>拓扑排序</b> — 按依赖关系确定节点的计算顺序（底层使用 Kahn 算法）</li>
<li><b>循环检测</b> — 自动检测图中的循环引用，有环时抛出 DAGCycleError</li>
<li><b>逐节点求值</b> — 按拓扑顺序依次计算每个节点</li>
<li><b>结果收集</b> — 收集所有节点的中间值和最终输出</li>
</ol>

<h3>使用方式</h3>
<p>编译和求值在以下场景自动触发：</p>
<ul>
<li><b>实时预览</b> — 选中节点时自动编译并求值</li>
<li><b>外部 API</b> — <code>compile_graph(doc)</code> 编译 → <code>evaluate_graph(dag, context)</code> 求值</li>
<li><b>DAGService</b> — <code>DAGService.from_graph_file(path)</code> 从文件加载并求值</li>
</ul>
""",
    )


def _format() -> HelpSection:
    return HelpSection(
        category="文件格式",
        title="JSON 文件格式说明",
        content="""\
<h2>JSON 文件格式</h2>

<p>编辑器使用 JSON 格式保存和加载计算图。以下是一个完整的格式说明。</p>

<h3>顶层结构</h3>
<pre>
{
  "schema_version": "calc-graph-v1",
  "name": "图名称",
  "description": "图描述",
  "external_variables": {
    "变量路径": {
      "type": "float",
      "source": "character|weapon|equipment|enemy|computed",
      "description": "变量说明"
    }
  },
  "nodes": [...],
  "edges": [...],
  "layout": {
    "sections": [...]
  }
}
</pre>

<h3>节点对象</h3>
<pre>
{
  "id": "node_abc12345",
  "type": "const|var|user_input|unary|binary|condition|output",
  "op": "floor|+|^|...",         // 仅 unary/binary 需要
  "label": "显示名称",
  "position": {"x": 100.0, "y": 200.0},
  "config": {                    // 按节点类型不同
    "value": 0.0,                // const
    "path": "character.xxx",     // var
    "default": 0.0,              // user_input
    "min": 0.0, "max": 100.0, "step": 1.0
  }
}
</pre>

<h3>连线对象</h3>
<pre>
{
  "from_node": "源节点ID",
  "from_port": 0,                // 源节点的输出端口索引
  "to_node": "目标节点ID",
  "to_port": 0,                  // 目标节点的输入端口索引
  "id": "edge_..."               // 可选
}
</pre>

<h3>Section 对象</h3>
<pre>
{
  "id": "sec_1",
  "title": "结果",
  "output_nodes": ["out_1", "out_2"],
  "columns": 1
}
</pre>
""",
    )
