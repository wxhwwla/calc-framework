# 编码损坏处置手册

> **版本**：2026-05-29  
> **受众**：维护者、Agent  
> **适用于**：Git 提交或工作区中出现编码乱码时的诊断与处置流程

---

## 1. 什么是编码损坏

本仓库文件全部为 UTF-8。当文件以非 UTF-8 编码（如 GBK）写入并提交后，多字节中文字符会在 Git 历史中变成 **U+FFFD（Unicode 替换字符）**。

### 典型症状

**Python 源码（`.py`/`.pyw`）**：
1. Python 语法错误：字符串或注释中出现 `\ufffd` 导致未闭合引号
2. `python -m pytest` 收集阶段报 `SyntaxError`
3. `git show <commit>:<file>` 输出的 bytes 中包含 `\xef\xbf\xbd`（UTF-8 编码的 U+FFFD）

**其他文本文件（`.json`/`.md`/`.yml`/`.ts`/`.tsx`/`.html` 等）**：
4. 文件内容出现 `。?"` 或 `属�?` 等乱码
5. `json.JSONDecodeError` 或 `tomllib.TOMLDecodeError`（JSON/TOML 配置文件）
6. TypeScript 编译报 `SyntaxError`（含中文字符的行）
7. CI 配置（`.yml`）解析失败

### 根源

Windows 控制台/终端默认编码为 GBK（代码页 936）。当某个脚本或工具以 GBK 模式打开文件写入时，UTF-8 的中文字节序列会被 GBK 解码产生错误字符，再以 UTF-8 写入 Git，产生不可逆的损坏。

---

## 2. 严重级别判定

| 级别 | 标准 | 处置 |
|------|------|------|
| **极严重** | 多个 `.py` 文件语法错误，`pytest` 无法收集，`check_layout` 在业务文件中报错 | **立即回滚**（`git reset --hard HEAD~1`），从干净版本重做 |
| **严重** | 仅新文件损坏、损坏文件可删除重建；或损坏仅限注释/文档 | 考虑回滚，视文件数量决定 |
| **一般** | 个别文件损坏，不影响代码逻辑，可手动逐字修复 | 修复即可，不回滚 |

### 决策规则

- **极严重 → 必定回滚**。不要试图逐文件修复——损坏已经发生在 Git history 层面，修复后的文件内容已经丢失了原始正确字符。
- **严重 → 优先回滚**。如果损坏文件 ≤ 2 个且重建代价 < 回滚代价，可以修复。否则回滚。
- **一般 → 修复**。不回滚。

---

## 3. 标准处置流程

### 3.1 诊断

```powershell
# 检查 HEAD 中是否已有损坏（所有文本文件类型）
python -c "
import subprocess
UFFFD = b'\xef\xbf\xbd'
TEXT_EXTS = ('.py','.pyw','.json','.md','.html','.xml','.yml','.yaml',
             '.ts','.tsx','.js','.css','.sh','.bat','.ps1','.toml',
             '.spec','.nsi','.gitignore','.cfg','.conf','.ini','.txt',
             '.mdc','.cursorrules')
r = subprocess.run(['git','diff-tree','--no-commit-id','-r','HEAD'], capture_output=True)
for line in r.stdout.decode().splitlines():
    parts = line.split()
    if len(parts)>=5 and parts[-1].endswith(TEXT_EXTS):
        src = parts[-2]
        blob = parts[-1]
        r2 = subprocess.run(['git','cat-file','-p',blob], capture_output=True)
        if UFFFD in r2.stdout:
            print(f'CORRUPT: {src}')
"
```

也可运行全量 UTF-8 离线扫描（扫描工作区而非仅 HEAD）：
```powershell
# 扫描所有文本文件是否为有效 UTF-8（排除 dist/node_modules/.venv/.git）
python -c "
import glob, os
SKIP_DIRS = {'dist','node_modules','.venv','.git','__pycache__'}
EXTS = ('*.py','*.pyw','*.json','*.md','*.html','*.xml','*.yml','*.yaml',
        '*.ts','*.tsx','*.js','*.css','*.sh','*.bat','*.ps1','*.toml',
        '*.spec','*.nsi','*.gitignore','*.cfg','*.conf','*.ini','*.txt',
        '*.mdc','*.cursorrules')
fail = []
for ext in EXTS:
    for f in glob.glob(f'**/{ext}', recursive=True):
        parts = os.path.normpath(f).split(os.sep)
        if not any(s in parts for s in SKIP_DIRS) and os.path.getsize(f):
            try:
                with open(f,'r',encoding='utf-8') as fh:
                    fh.read()
            except UnicodeDecodeError:
                fail.append(f)
[print(f'CORRUPT: {f}') for f in sorted(fail)]
if not fail: print('所有文本文件 UTF-8 解码通过')
"
```

### 3.2 回滚

```powershell
git reset --hard HEAD~1
git clean -fd
```

回滚后，工作区回到上个版本。不要 `git revert`（会产生新提交而非真正回滚）。

### 3.3 重建

回滚后，**不要从损坏提交中提取文件来"修复"**。应该：

1. 分析损坏提交中**增/改/删**了哪些文件（`git diff --name-status <回滚前的commit>`）
2. 对**纯移动**（rename）：用 `git mv` 重做
3. 对**纯删除**：用 `git rm` 重做
4. 对**无编码损坏的新增/修改**：用 `git show <commit>:<path>` 提取（验证无 `\xef\xbf\xbd`）
5. 对**全新文件**：从 v3.6.1 的同一代码写起，不复制已损坏的内容
6. 对**有编码损坏的新增/修改**：丢弃，用正确方式从干净基础重建

### 3.4 验证

重建完成后：
```powershell
python tools/check_layout.py --max-lines 400
python -m pytest tests/ -q
```

---

## 4. 案例：v3.6.2 编码损坏事件

### 时间线

| 步骤 | 操作 |
|------|------|
| 1 | v3.6.2（`003a53f`）提交了 51 个文件变更 |
| 2 | 发现 14 个 `.py` 文件含 U+FFFD，3 个有语法错误 |
| 3 | 判定为**极严重**（核心计算模块语法错误 + 大量 GUI 文件损坏） |
| 4 | 回滚到 v3.6.1（`14d53ff`）|
| 5 | 分析 v3.6.2 变更：27 个干净文件 + 14 个损坏文件 + 若干纯移动/删除 |

### v3.6.2 实际改动（非编码损坏）

v3.6.2 是一次**代码结构规范化重构**，解决 `check_layout` 的 6 个 ERROR：

| 违规 | 修复 |
|------|------|
| `calculation/` 11 子项 | `abnormal/` → `manual_buff/` |
| `calculation/multiplicative_zones/` 11 子项 | 删除 `ability_bonus_zone.py` |
| `tests/` 12 子项 | 迁走 `test_qt_imports.py`、删除 `release_bundle/` |
| `qt_app.py` 1170 行 | 拆分 3 个 mixin |
| `qt_control_dock.py` 785 行 | 拆分 2 个 helper |
| `dag/config.py` 587 行 | 提取 `_subgraph_builders.py` |

另有新增文件：`gui_design/designer/`、`gui_design/legal/`、`scripts/editor_app.py`、`gui_design/controls/search/` 等。

### 重建方法

1. `git mv` / `git rm` 完成所有结构移动
2. 从 `003a53f` 提取 **27 个无 U+FFFD 的文件**（验证字节级别干净）
3. 全新文件（designer/legal/scripts/search_controls/test）从 v3.6.1 代码写起
4. `manual_buff/spell.py` 和 `physical.py` 从 v3.6.1 的 `abnormal/spell.py` 和 `abnormal/physical.py` 用 Python 从 git 直接读取（避开 shell 编码干扰）
5. 结果：`check_layout` 零 ERROR，360+ 测试通过

---

## 5. 预防措施

### Agent 操作规范

1. **写文件统一用 Python**，不要通过 PowerShell `>` 重定向包含中文的文件
2. 写入时显式指定 UTF-8（**适用于所有文本文件类型**，不仅是 `.py`）：
   ```python
   with open(path, 'w', encoding='utf-8') as f:
       f.write(content)
   ```
3. 从 Git 读取文件内容时用 Python `subprocess` + `capture_output=True`（返回 bytes），不要用 shell 重定向
4. 提交前跑 Unicode 编码扫描：
    ```powershell
    # 全量检查所有文本文件 UTF-8 解码 + Python AST 解析 + JSON 解析
    python -c "
    import glob, os, ast, json
    SKIP = {'dist','node_modules','.venv','.git','__pycache__'}
   EXTS = {'*.py','*.pyw','*.json','*.md','*.html','*.xml','*.yml','*.yaml',
           '*.ts','*.tsx','*.js','*.css','*.sh','*.bat','*.ps1','*.toml',
           '*.spec','*.nsi','*.gitignore','*.cfg','*.conf','*.ini','*.txt',
           '*.mdc','*.cursorrules'}
   fail = False
   for e in EXTS:
       for f in glob.glob(f'**/{e}', recursive=True):
           p = os.path.normpath(f).split(os.sep)
           if any(s in p for s in SKIP) or not os.path.getsize(f):
               continue
           try:
               src = open(f,'r',encoding='utf-8').read()
           except UnicodeDecodeError:
               print(f'DECODE_FAIL: {f}'); fail = True; continue
           if f.endswith('.py') or f.endswith('.pyw'):
               try:
                   ast.parse(src)
               except SyntaxError as e:
                   print(f'SYNTAX_ERROR: {f}: {e}'); fail = True
           elif f.endswith('.json'):
               try:
                   json.loads(src)
               except json.JSONDecodeError as e:
                   print(f'JSON_ERROR: {f}: {e}'); fail = True
   if not fail: print('所有文本文件检查通过')
   "
   ```
5. 也可运行 `check_layout` 和 `pytest` 验证

### 环境

```powershell
$env:PYTHONIOENCODING = "utf-8"
```

所有 Python 子进程应在调用时设置此环境变量。

---

## 6. venv/site-packages 编码损坏

### 6.1 场景

`pip install` 后，**venv 内**的 `site-packages` 出现 `SyntaxError`，如：

```
File ".venv\Lib\site-packages\pyparsing\unicode.py", line 272
    婕㈠瓧 = Kanji
    ^
SyntaxError: invalid character '㈠' (U+3220)
```

或 pip 自身报 `SyntaxError: unterminated string literal`。

### 6.2 根源

- 中华区 Windows 系统区域设置为 **cp936（GBK）**
- 当终端/进程的默认编码为 GBK 时，pip 安装含 Unicode 字符（如 emoji、CJK 标识符）的包时有概率写入损坏文件
- 常见于：Python < 3.12 且无 `PYTHONUTF8=1`，或在 `chcp 936` 终端中执行 `pip install`
- 本项目当前 venv（Python 3.13）已默认 UTF-8，但历史 venv 可能在旧版本 Python 或编码未设置时创建

### 6.3 诊断

```powershell
# 检查 venv 的 Python 默认编码
.venv\Scripts\python.exe -c "import sys; print('fs enc:', sys.getfilesystemencoding(), '| def enc:', sys.getdefaultencoding())"

# 检查 site-packages 中是否有编码损坏的文件
python -c "
import os, glob
for f in glob.glob('.venv/Lib/site-packages/**/*.py', recursive=True):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            fh.read()
    except UnicodeDecodeError:
        print(f'CORRUPT: {f}')
"
```

### 6.4 修复

修复方法（从系统 Python 复制正确的包文件覆盖 venv 版本）：

```powershell
# 示例：修复 pyparsing（已有正确的包在系统 Python 中）
$sys = "E:\python\Lib\site-packages\pyparsing"
$venv = ".venv\Lib\site-packages\pyparsing"
Copy-Item "$sys\*" $venv -Recurse -Force
```

**如果损坏范围大（多个包）**，直接重建 venv 更干净：

```powershell
deactivate
rm -r .venv
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,build]"
```

### 6.5 预防

创建/重建 venv 前确保编码正确：

```powershell
# Python < 3.12 必须设置
$env:PYTHONUTF8 = "1"

# 统一终端编码
chcp 65001

# 验证
python -c "import sys; assert sys.getfilesystemencoding()=='utf-8'"

# 然后再创建 venv
python -m venv .venv
```

---

## 相关文档

- [代码结构规范](../代码结构规范.md)
- [ADR-0001：代码目录与文件规模约束](../adr/0001-code-layout-constraints.md)
- [会话接续手册](../会话接续手册.md) - §3 记录每次版本变更摘要
- [操作指令集](../操作指令集.md) - venv 创建流程
