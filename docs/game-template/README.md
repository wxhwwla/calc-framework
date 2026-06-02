# 游戏包骨架模板

## 用途

本模板为基于 calc-framework 开发新游戏适配计算器提供标准骨架代码。包含：

- `games/_template/` — 游戏包 Python 源码（入口、数据加载器、DAG 适配器、GUI、测试）
- `framework/adapters/_template/` — 框架适配器配置（DAG 公式、自定义函数、属性模式）

## 如何使用

### 1. 复制模板

```bash
# 从仓库根目录执行
cp -r docs/game-template/games/_template games/your_game
cp -r docs/game-template/framework/adapters/_template framework/adapters/your_game
```

### 2. 全局替换

将模板文件中的 **`_template`** 和 **`_TEMPLATE`** / **`{Game}`** 替换为你的游戏名称：

| 占位符 | 替换为 | 示例 |
|--------|--------|------|
| 文件名 `_template` | `your_game` | `_template_App.py` → `your_game_App.py` |
| `_template`（代码内 import） | `your_game` | `from games.your_game.calc...` |
| `TEMPLATE` / `{Game}`（类名/显示名） | `YourGame` | `YourGameContextLoader` |
| `DISPLAY_NAME` | 游戏中文名 | `"明日方舟"` |

建议替换工具：

```bash
# PowerShell
Get-ChildItem -Recurse -File | Where-Object { $_.Extension -in '.py','.json','.md' } | ForEach-Object {
    (Get-Content $_.FullName) -replace '_template', 'your_game' -replace 'TEMPLATE', 'YourGame' | Set-Content $_.FullName
}

# Linux/macOS
find . -type f \( -name '*.py' -o -name '*.json' -o -name '*.md' \) -exec sed -i '' 's/_template/your_game/g; s/TEMPLATE/YourGame/g' {} +
```

### 3. 开发流程

完成替换后，按以下顺序推进：

1. **创建 DAG 公式**：在 `framework/adapters/your_game/` 下创建 `.dag.json`（可参考 arknights 或 endfield）
2. **实现数据加载器**：填充 `calc/dag_adapter/loader.py` 中的 TODO，从你的游戏数据结构提取属性
3. **注册自定义函数**：在 `framework/adapters/your_game/functions.py` 中添加游戏专属公式
4. **配置 UI 布局**：在 `framework/adapters/your_game/ui/layout.json` 中定义输入/输出 Section
5. **运行测试**：`python -m pytest games/your_game/tests/ -v`
6. **启动 GUI**：`python games/your_game/main.py`
7. **打包**：使用图编辑器/布局编辑器导出 `.calcpack`

### 4. 目录结构（替换后）

```
games/your_game/
├── __init__.py                  # 包初始化
├── _package_meta.py             # 包元数据
├── framework_bridge.py          # 框架桥接
├── main.py                      # 入口点（需自行创建）
├── calc/
│   ├── __init__.py
│   └── dag_adapter/
│       ├── __init__.py          # 导出 {Game}ContextLoader, compute_snapshot_with_dag
│       ├── loader.py            # DataContextLoader 实现
│       ├── adapter.py           # DAG 计算适配器
│       └── types.py             # （可选）类型定义
├── gui/
│   ├── __init__.py
│   └── your_game_App.py         # QMainWindow 骨架
└── tests/
    ├── __init__.py
    ├── conftest.py              # fixture
    ├── test_adapter.py          # loader 输出格式测试
    └── test_dag_compute.py      # DAG 计算测试

framework/adapters/your_game/
├── meta.json                    # 适配器元数据
├── your_game.dag.json           # DAG 公式（需自行创建）
├── attr_schema.json             # 属性模式
├── functions.py                 # 自定义函数
└── ui/
    └── layout.json              # UI 布局（需自行创建）
```
