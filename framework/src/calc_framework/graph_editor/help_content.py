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
<li><b>复合节点</b> — 把一整张子图封装成一个节点，可打包分发</li>
</ul>

<h3>工作流程</h3>
<ol>
<li>从左侧节点面板拖拽节点到画布</li>
<li>连线：从输出端口拖到输入端口</li>
<li>选中节点，在右侧属性面板中配置参数</li>
<li>用 output 节点标记最终输出结果</li>
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
<li><b>包</b> — 导入的复合节点（显示为紫色）</li>
</ul>

<h3>中栏：画布（Canvas）</h3>
<p>可视化编辑的主工作区：</p>
<ul>
<li>拖拽节点调整位置（自动吸附到网格）</li>
<li>从端口拖出连线（显示为灰色的贝塞尔曲线）</li>
<li>点击选择节点（显示为虚线边框）</li>
<li>按 Delete 键删除选中节点及关联的连线</li>
<li>鼠标中键拖拽平移画布</li>
<li>鼠标滚轮缩放画布</li>
</ul>

<h3>右栏：属性面板（PropPanel）</h3>
<p>编辑选中节点的详细参数，底部显示实时预览值。</p>
""",
    )


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
<li>一条灰色的贝塞尔曲线连线即建立完成（与源节点颜色一致）</li>
</ol>

<h3>选择与编辑</h3>
<ul>
<li><b>单击节点</b> — 选中节点（显示虚线边框），右侧属性面板显示该节点的配置</li>
<li><b>单击空白处</b> — 取消选中</li>
<li><b>选中后</b> — 在属性面板中修改节点的各项参数</li>
<li><b>节点标签</b> — 可在属性面板的名称字段中修改显示名称</li>
</ul>

<h3>删除节点或连线</h3>
<ul>
<li><b>选中节点 -> Delete 键</b> — 删除节点及其所有关联的连线</li>
</ul>

<h3>画布操作</h3>
<ul>
<li><b>左键拖拽</b> — 移动节点（自动吸附到 40px 网格）</li>
<li><b>中键拖拽</b> — 平移画布</li>
<li><b>滚轮</b> — 缩放画布</li>
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
<p>清空当前画布和属性面板，开始一个新的计算图。</p>

<h3>打开（Ctrl + O）</h3>
<p>从 .json 文件加载之前保存的计算图。加载后画布完全恢复到保存时的状态。</p>

<h3>保存（Ctrl + S）</h3>
<p>将当前编辑器的完整状态保存到 .json 文件。</p>
<ul>
<li>保存内容包括：所有节点信息、连线数据、节点位置坐标</li>
<li>文件编码为 UTF-8</li>
</ul>

<h3>另存为（Ctrl + Shift + S）</h3>
<p>将当前状态另存为一个新的 .json 文件。</p>

<h3>JSON 文件格式</h3>
<p>保存的文件格式是一个结构化 JSON 对象，包含以下顶层字段：</p>
<ul>
<li><code>schema_version</code> — 模式版本号</li>
<li><code>name</code> / <code>description</code> — 图的名称和描述</li>
<li><code>nodes</code> — 节点数组，每个包含 id / type / op / label / config / position</li>
<li><code>edges</code> — 连线数组，每条包含 from_node / from_port / to_node / to_port</li>
<li><code>layout</code> — 排版信息（保留兼容，不再需要手动配置）</li>
<li><code>external_variables</code> — 外部变量声明</li>
</ul>
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
<li><b>选择节点</b> -> 自动编译当前整个图 -> 调用 DAG 引擎求值</li>
<li>从计算结果中提取选中节点的值并显示</li>
</ol>

<h3>自动更新时机</h3>
<ul>
<li>切换选择的节点</li>
<li>修改节点配置（数值/路径/操作符）</li>
<li>添加或删除节点或连线</li>
</ul>

<h3>显示格式</h3>
<ul>
<li><b>数值</b> — 浮点数显示 6 位小数</li>
<li><b>无法计算</b> — 显示"(无法计算)"（通常是因为输入未完全连接）</li>
<li><b>错误</b> — 显示"错误: xxx"</li>
<li><b>未选择</b> — 显示"—"</li>
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
<tr><th>快捷键</th><th>功能</th></tr>
<tr><td>Ctrl + N</td><td>新建计算图</td></tr>
<tr><td>Ctrl + O</td><td>打开计算图文件</td></tr>
<tr><td>Ctrl + S</td><td>保存当前计算图</td></tr>
<tr><td>Ctrl + Shift + S</td><td>另存为</td></tr>
<tr><td>Delete</td><td>删除选中节点及关联连线</td></tr>
<tr><td>F1</td><td>打开使用说明</td></tr>
</table>
""",
    )


def _config() -> HelpSection:
    return HelpSection(
        category="高级配置",
        title="节点配置说明",
        content="""\
<h2>节点配置说明</h2>

<h3>属性面板功能</h3>
<ul>
<li>选中节点后，右侧属性面板显示该节点的所有可配置参数</li>
<li><b>名称</b> — 节点的显示标签，支持中文</li>
<li><b>类型</b> — 只读，显示节点类型</li>
<li><b>操作</b> — 一元/二元运算节点可选择运算类型</li>
<li><b>数值</b> — 常量节点的输出值</li>
<li><b>变量路径</b> — 变量引用节点的数据路径</li>
<li><b>默认值/最小值/最大值/步长</b> — 用户输入节点的范围控制</li>
</ul>
""",
    )


def _compilation() -> HelpSection:
    return HelpSection(
        category="高级配置",
        title="编译流程",
        content="""\
<h2>编译流程</h2>

<h3>从编辑图到 DAG 的转换</h3>
<ol>
<li><b>收集</b> — collect_document() 从画布上收集所有节点和连线</li>
<li><b>编译</b> — compile_graph() 将编辑器格式转换为 DAG 引擎格式</li>
<li><b>求值</b> — evaluate_graph() 执行 DAG 并计算所有节点</li>
</ol>

<h3>输出自动检测</h3>
<p>编译器不再需要手动配置 Section。它会自动扫描图中的 output 节点：</p>
<ul>
<li>遍历所有节点，找到 type="output" 的节点</li>
<li>回溯连线，找到输出节点上游的实际计算节点</li>
<li>用 output 节点的 label 作为输出的名称</li>
</ul>

<h3>复合节点</h3>
<p>遇到 type="composite" 的节点时，编译器会递归编译其内部子图：</p>
<ul>
<li>子图编译生成 DAGSubgraph</li>
<li>根据子图的 user_input 自动推导绑定关系</li>
<li>根据子图的 output 节点自动推导输出</li>
</ul>
""",
    )


def _format() -> HelpSection:
    return HelpSection(
        category="文件规范",
        title="JSON 格式规范",
        content="""\
<h2>JSON 格式规范</h2>

<h3>文档结构</h3>
<pre>{
  "schema_version": "calc-graph-v1",
  "name": "图名称",
  "description": "图描述",
  "nodes": [...],
  "edges": [...],
  "layout": {"sections": [...]},
  "external_variables": {}
}</pre>

<h3>节点对象</h3>
<pre>{
  "id": "唯一标识",
  "type": "const|var|user_input|unary|binary|condition|output|composite",
  "op": "运算类型字符串",
  "label": "显示名称",
  "config": { "value": 0.0, "path": "", "default": 0, ... },
  "position": {"x": 0, "y": 0}
}</pre>

<h3>复合节点特殊字段</h3>
<ul>
<li><code>config.source_graph</code> — 嵌入的子图 JSON 字符串</li>
<li><code>config.package_name</code> — 来源包名</li>
</ul>
""",
    )
