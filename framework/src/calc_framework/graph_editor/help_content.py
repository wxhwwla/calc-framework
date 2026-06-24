# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""帮助文档内容 — 集中管理所有使用说明文本。"""

from dataclasses import dataclass, field

from utils.gui.help_loader import load_multi_category

from .help_menu import (
    _compilation,
    _config,
    _file_ops,
    _format,
    _operations,
    _preview,
    _shortcuts,
)
from .help_nodes import _node_types


@dataclass
class HelpSection:
    """帮助文档中的一个分类。"""

    category: str
    title: str
    content: str
    sub_sections: list["HelpSection"] = field(default_factory=list)


def build_help_tree() -> list[HelpSection]:
    """构建完整的帮助文档树。"""
    docs = load_multi_category({"完整说明书": ["GUI ①：DAG 图编辑器"]})
    result = [
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
    return result + docs  # type: ignore[return-value]


def _overview() -> HelpSection:
    return HelpSection(
        category="入门",
        title="概述",
        content="""\
<h2>公式计算图编辑器</h2>

<p>公式计算图编辑器是一个<strong>可视化节点编程工具</strong>，</p>
<p>允许用户通过拖拽和连线的方式构建数学计算流程，</p>
<p>并将计算结果导出为 JSON 格式供其他工具使用。</p>

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
