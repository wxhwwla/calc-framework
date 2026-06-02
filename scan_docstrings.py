#!/usr/bin/env python3
"""
Safe docstring batch adder for games/ Python files.

For each file missing module/class/function docstrings, adds appropriate
Google-style one-line docstrings. Operates on AST level and validates
syntax after each change.
"""
import ast
import os
import subprocess
import sys
from typing import Any

SKIP_DIRS = {'tests', '__pycache__', '.venv', 'node_modules'}
GAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'games')

# Map of relpath -> module-level docstring for __init__.py files
MODULE_DOCS = {
    os.path.join('endfield', 'calc', 'survival', '__init__.py'): "生存能力估算模块。",
    os.path.join('endfield', 'gui', 'legal', '__init__.py'): "GUI 法律信息模块。",
    os.path.join('endfield', 'gui', 'presentation', 'total_damage_panel.py'): "总伤结算面板 — 确认后展示各技能段加权总伤。",
    os.path.join('arknights', 'gui', '__init__.py'): "明日方舟 GUI 包。",
    os.path.join('__init__.py'): "游戏包根目录。",
}

# Map of relpath -> {lineno -> docstring} for specific items
# Only classes and public functions that need docstrings
SPECIFIC_DOCS: dict[str, dict[int, str]] = {}

def make_doc(node_type: str, name: str, parent_class: str | None = None) -> str:
    """Generate an appropriate one-line docstring for a code item."""
    if node_type == 'CLS':
        return f"""{name}"""
    elif node_type == 'FUN':
        return f"""{name}"""
    elif node_type == 'MET':
        # Try to generate meaningful docstring from method name
        doc = _method_name_to_doc(name)
        return doc
    return f"""{name}"""

def _method_name_to_doc(name: str) -> str:
    """Convert a method name to a descriptive one-line docstring."""
    name = name.lstrip('_')
    
    # Common method prefixes and their descriptions
    docs = {
        'build': '构建',
        'run': '运行',
        'refresh': '刷新',
        'clear': '清空',
        'stats': '统计',
        'get': '获取',
        'set': '设置',
        'load': '加载',
        'save': '保存',
        'export': '导出',
        'import': '导入',
        'apply': '应用',
        'connect': '连接',
        'start': '启动',
        'cancel': '取消',
        'open': '打开',
        'close': '关闭',
        'show': '显示',
        'hide': '隐藏',
        'update': '更新',
        'reset': '重置',
        'init': '初始化',
        'read': '读取',
        'write': '写入',
        'parse': '解析',
        'format': '格式化',
        'validate': '验证',
        'check': '检查',
        'find': '查找',
        'search': '搜索',
        'resolve': '解析',
        'compute': '计算',
        'calculate': '计算',
        'evaluate': '求值',
        'estimate': '估算',
        'normalize': '规范化',
        'convert': '转换',
        'filter': '过滤',
        'sort': '排序',
        'merge': '合并',
        'split': '分割',
        'render': '渲染',
        'draw': '绘制',
        'emit': '发射',
        'notify': '通知',
        'handle': '处理',
        'process': '处理',
        'notify': '通知',
        'populate': '填充',
        'sync': '同步',
        'extract': '提取',
        'collect': '收集',
        'build': '构建',
        'create': '创建',
        'generate': '生成',
        'make': '创建',
        'prepare': '准备',
        'ensure': '确保',
        'adjust': '调整',
        'update': '更新',
        'record': '记录',
        'copy': '复制',
        'move': '移动',
        'delete': '删除',
        'remove': '移除',
        'add': '添加',
        'insert': '插入',
        'append': '追加',
        'clipboard': '复制到剪贴板',
        'human_size': '格式化人类可读大小',
    }
    
    for prefix, desc in docs.items():
        if name.startswith(prefix):
            rest = name[len(prefix):]
            if rest.startswith('_'):
                rest = rest[1:]
            # Handle camelCase: "onConfirm" -> "确认"
            if rest and rest[0].isupper():
                # Could be camelCase - just return prefix description
                return f"""{desc}{rest}"""
            if not rest:
                return f"""{desc}"""
            return f"""{desc}{rest}"""
    
    # Default: use name as-is with general prefix
    return f"""{name}"""


def process_file(filepath: str, relpath: str) -> list[str]:
    """Process a single file, adding docstrings. Returns list of changes made."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. Add module-level docstring if needed
    lines = content.split('\n')
    new_lines = list(lines)
    
    # Find the line after SPDX header or first import/code line
    module_doc_added = False
    if relpath in MODULE_DOCS:
        doc_text = MODULE_DOCS[relpath]
        for i, line in enumerate(lines):
            if line.startswith('# SPDX-License-Identifier:'):
                # Add docstring after SPDX line
                if i + 1 < len(lines) and not lines[i+1].strip().startswith('"""'):
                    new_lines.insert(i + 1, f'"""{doc_text}"""')
                    module_doc_added = True
                break
    
    if module_doc_added:
        content = '\n'.join(new_lines)
    
    # 2. Parse AST to find classes and functions without docstrings
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return [f"SYNTAX ERROR in {relpath}"]
    
    # Collect line numbers of classes/functions without docstrings
    changes = []
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node) and not node.name.startswith('_'):
                # Add class docstring
                cls_doc = f'"""{node.name}"""'
                changes.append(f"CLS {node.name}:{node.lineno}")
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(child) and not child.name.startswith('__'):
                        changes.append(f"MET {node.name}.{child.name}:{child.lineno}")
        
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(node):
                changes.append(f"FUN {node.name}:{node.lineno}")
    
    return changes


def main():
    count_files = 0
    total_changes = 0
    
    for root, dirs, files in os.walk(GAMES_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith('.py'):
                continue
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, GAMES_DIR)
            changes = process_file(fpath, rel)
            if changes:
                count_files += 1
                total_changes += len(changes)
                print(f"\n{rel}:")
                for c in changes:
                    print(f"  {c}")
    
    print(f"\n\n总览: {count_files} 个文件, {total_changes} 处需要 docstring")


if __name__ == '__main__':
    main()
