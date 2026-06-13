# SPDX-License-Identifier: AGPL-3.0
"""帮助文档 — 菜单、操作、快捷键、文件、配置等说明。"""

from calc_framework.ui.i18n import tr

from .help_content import HelpSection


def _operations() -> HelpSection:
    return HelpSection(
        category=tr("desktop.graphEditor.helpCategoryOps"),
        title=tr("desktop.graphEditor.helpBasicOps"),
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
        category=tr("desktop.graphEditor.helpCategoryFile"),
        title=tr("desktop.graphEditor.helpFileOps"),
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
        category=tr("desktop.graphEditor.helpCategoryPreview"),
        title=tr("desktop.graphEditor.helpLivePreview"),
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
        category=tr("desktop.graphEditor.helpCategoryShortcuts"),
        title=tr("desktop.graphEditor.helpShortcuts"),
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
        category=tr("desktop.graphEditor.helpCategoryAdvanced"),
        title=tr("desktop.graphEditor.helpNodeConfig"),
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
        category=tr("desktop.graphEditor.helpCategoryAdvanced"),
        title=tr("desktop.graphEditor.helpCompilation"),
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
        category=tr("desktop.graphEditor.helpCategoryFormat"),
        title=tr("desktop.graphEditor.helpJsonFormat"),
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
