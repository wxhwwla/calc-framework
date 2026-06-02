#!/usr/bin/env python3
"""
Batch add Google-style docstrings to games/ Python files.

For each file, adds:
1. Module-level docstring if missing (__init__.py files only)
2. Class docstring if missing (public classes only)
3. Method/function docstring if missing

Verifies syntax after each change.
"""
import ast
import os
import re

SKIP_DIRS = {'tests', '__pycache__', '.venv', 'node_modules'}
GAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'games')

EDIT_COUNT = 0
FILE_COUNT = 0


def _method_to_doc(name: str) -> str:
    """Generate a one-line docstring from a method name."""
    n = name.lstrip('_')
    
    prefix_map = {
        'build': '构建', 'run': '运行', 'refresh': '刷新', 'clear': '清空',
        'stats': '统计信息', 'get': '获取', 'set': '设置', 'load': '加载',
        'save': '保存', 'export': '导出', 'import': '导入', 'apply': '应用',
        'connect': '连接', 'start': '启动', 'cancel': '取消', 'open': '打开',
        'close': '关闭', 'show': '显示', 'hide': '隐藏', 'update': '更新',
        'reset': '重置', 'init': '初始化', 'read': '读取', 'write': '写入',
        'parse': '解析', 'format': '格式化', 'validate': '验证', 'check': '检查',
        'find': '查找', 'search': '搜索', 'resolve': '解析', 'compute': '计算',
        'calculate': '计算', 'evaluate': '求值', 'estimate': '估算',
        'normalize': '规范化', 'convert': '转换', 'filter': '过滤', 'sort': '排序',
        'merge': '合并', 'render': '渲染', 'draw': '绘制', 'emit': '发射信号',
        'notify': '通知', 'handle': '处理', 'process': '处理', 'populate': '填充',
        'sync': '同步', 'extract': '提取', 'collect': '收集', 'create': '创建',
        'generate': '生成', 'make': '创建', 'prepare': '准备', 'ensure': '确保',
        'adjust': '调整', 'record': '记录', 'remove': '移除', 'add': '添加',
        'clipboard': '复制到剪贴板', 'confirm': '确认', 'display': '展示',
        'select': '选择', 'change': '变更', 'toggle': '切换', 'focus': '聚焦',
        'scroll': '滚动', 'expand': '展开', 'collapse': '折叠',
    }

    for prefix, desc in prefix_map.items():
        if n.startswith(prefix):
            rest = n[len(prefix):]
            if rest.startswith('_'):
                rest = rest[1:]
            if not rest:
                return f'{desc}。'
            # Handle camelCase
            if rest[0].isupper():
                return f'{desc}（{rest}）。'
            return f'{desc}{rest}。'

    if n.startswith('on_') or n.startswith('on'):
        event = n[3:] if n.startswith('on_') else n[2:]
        return f'{event} 事件处理。'

    return f'{name}。'


def _func_to_doc(name: str) -> str:
    """Generate a one-line docstring from a function name."""
    if name.startswith('_'):
        name = name[1:]
    prefix_map = {
        'build': '构建', 'run': '运行', 'refresh': '刷新', 'clear': '清空',
        'stats': '统计', 'get': '获取', 'set': '设置', 'load': '加载',
        'save': '保存', 'export': '导出', 'import': '导入', 'apply': '应用',
        'start': '启动', 'cancel': '取消', 'open': '打开', 'close': '关闭',
        'show': '显示', 'hide': '隐藏', 'update': '更新', 'reset': '重置',
        'read': '读取', 'write': '写入', 'parse': '解析', 'format': '格式化',
        'validate': '验证', 'check': '检查', 'find': '查找', 'search': '搜索',
        'resolve': '解析', 'compute': '计算', 'evaluate': '求值',
        'estimate': '估算', 'normalize': '规范化', 'convert': '转换',
        'filter': '过滤', 'sort': '排序', 'sync': '同步', 'extract': '提取',
        'collect': '收集', 'create': '创建', 'generate': '生成',
        'ensure': '确保', 'adjust': '调整', 'record': '记录',
        'remove': '移除', 'add': '添加',
    }
    for prefix, desc in prefix_map.items():
        if name.startswith(prefix):
            rest = name[len(prefix):]
            if rest.startswith('_'):
                rest = rest[1:]
            if not rest:
                return f'{desc}。'
            return f'{desc}{rest}。'
    return f'{name}。'


def add_docstring_to_source(source: str, node: ast.AST, doc: str) -> str:
    """Insert a docstring into source code right after the definition line."""
    lines = source.split('\n')
    target_line = node.lineno - 1  # 0-indexed

    # Find the last line of the definition (handle multi-line def)
    end_line = node.lineno - 1
    body_first_line = node.body[0].lineno - 1 if node.body else node.end_lineno - 1

    # Calculate indentation from the first body statement
    if node.body:
        first_body = node.body[0]
        if isinstance(first_body, ast.Expr) and isinstance(first_body.value, ast.Constant) and isinstance(first_body.value.value, str):
            return source  # Already has docstring

    indent = ''
    if body_first_line > 0 and body_first_line < len(lines):
        line_text = lines[body_first_line]
        indent = re.match(r'^(\s*)', line_text).group(1)

    doc_line = f'{indent}"""{doc}"""'

    # Insert docstring between the def line and first body statement
    insert_pos = body_first_line
    lines.insert(insert_pos, doc_line)

    # Fix indentation of existing body (they should be one level deeper)
    return '\n'.join(lines)


def process_file(filepath: str) -> list[str]:
    """Process one file, return list of changes made."""
    global EDIT_COUNT, FILE_COUNT
    
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    if not source.strip():
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f'SYNTAX ERROR: {e}']

    changes = []

    # Check if we need module-level docstring
    if not ast.get_docstring(tree):
        rel = os.path.relpath(filepath, GAMES_DIR)
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        dir_parts = os.path.dirname(rel).split(os.sep)
        context = ' > '.join(p for p in dir_parts if p != '.')
        
        if module_name == '__init__' and context:
            doc = f'{context} 模块。'
        elif module_name == '__init__':
            doc = '游戏包。'
        elif module_name:
            doc = f'{module_name} 模块。'
        else:
            doc = '模块。'

        # Add module docstring after last comment header, before first import
        lines = source.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') or stripped == '':
                insert_pos = i + 1
            elif stripped.startswith('from __future__'):
                insert_pos = i + 1
            else:
                break
        
        # Don't insert if there's already a docstring
        if insert_pos < len(lines) and lines[insert_pos].strip().startswith(('"""', "'''")):
            pass  # Already has docstring
        else:
            lines.insert(insert_pos, f'"""{doc}"""')
            source = '\n'.join(lines)
            changes.append(f'MODULE: {module_name}')
            EDIT_COUNT += 1
    
    # Now re-parse with the module docstring added
    tree = ast.parse(source)

    # Find classes, functions, methods without docstrings
    def process_node(node, parent_name=None):
        nonlocal source, changes
        
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node) and not node.name.startswith('_'):
                doc = f'{node.name}。'
                new_source = add_docstring_to_source(source, node, doc)
                if new_source != source:
                    source = new_source
                    changes.append(f'CLS {node.name}:{node.lineno}')
                    EDIT_COUNT += 1
                    tree = ast.parse(source)  # Re-parse
            
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(child):
                        doc = _method_to_doc(child.name)
                        new_source = add_docstring_to_source(source, child, doc)
                        if new_source != source:
                            source = new_source
                            changes.append(f'MET {node.name}.{child.name}:{child.lineno}')
                            EDIT_COUNT += 1
                            tree = ast.parse(source)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not ast.get_docstring(node):
                doc = _func_to_doc(node.name)
                new_source = add_docstring_to_source(source, node, doc)
                if new_source != source:
                    source = new_source
                    changes.append(f'FUN {node.name}:{node.lineno}')
                    EDIT_COUNT += 1
                    tree = ast.parse(source)

    for node in ast.iter_child_nodes(tree):
        process_node(node)

    # Write back if changes were made
    if changes:
        # Verify syntax
        try:
            ast.parse(source)
        except SyntaxError as e:
            return [f'SYNTAX ERROR after edit: {e}']

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source)
        FILE_COUNT += 1

    return changes


def main():
    total_files = 0
    all_results = {}

    for root, dirs, files in os.walk(GAMES_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if not f.endswith('.py'):
                continue
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, GAMES_DIR)
            changes = process_file(fpath)
            if changes:
                total_files += 1
                all_results[rel] = changes
                print(f'\n{rel}:')
                for c in changes:
                    print(f'  + {c}')

    print(f'\n{"="*50}')
    print(f'处理完成: {total_files} 个文件, {EDIT_COUNT} 处 docstring 新增/修正')
    print(f'{"="*50}')


if __name__ == '__main__':
    main()
