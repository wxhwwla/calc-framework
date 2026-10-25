# ADR-0019：拆分 ui/viewer.py 职责

## 状态

已采纳

## 上下文

`calc_framework/ui/viewer.py` 是一个 **842 行的单体文件**，远超 ~400 行的代码结构规范。它同时承担 5 个职责：

| 职责 | 行数范围 | 说明 |
|------|----------|------|
| .calcpack 加载/解压/资源提取 | 95–145 | `_load_calcpack()`, `_extract_assets_from_calcpack()`, `_resolve_asset_paths_in_layout()` |
| 实体 → context 构建 | 148–180 + 51–92 | `_build_context_from_entity()`, `_resolve_field_name()`, 常量映射表 |
| CalcPackViewer GUI | 183–809 | QMainWindow、菜单、面板、主题切换、ComputeSheet 编排、信号路由 |
| 插件管理器对话框 | 698–803 | 导入 .calcplugin、打包目录、刷新/查看 |
| 帮助内容 | 322–439 | `_build_viewer_help()` 含 5 个 HelpSection 的 HTML 内容 |

每个职责之间的耦合度低（通过函数调用关联），适合提取到独立的文件中。

## 决策

将 `ui/viewer.py` 拆分为 4 个文件，目标是：

1. `viewer.py` ≤ 500 行（仍超过但大幅改善）
2. 各文件有明确的单一职责
3. 不改变外部 API 行为
4. 测试覆盖率不变

### 拆分方案

```
ui/
├── viewer.py                 ← CalcPackViewer 主类（-320 行）
├── viewer_pack_utils.py      ← .calcpack I/O + context 构建（新建，~90 行）
├── viewer_help_content.py    ← 帮助内容（新建，~120 行）
└── viewer_plugin_manager.py  ← 插件管理器对话框（新建，~110 行）
```

### 文件 1：`viewer_pack_utils.py`

抽取以下模块级函数和常量：

```python
# 常量
_VARIABLE_FIELD_MAP: dict[str, str]
_SOURCE_TO_DATA_FILE: dict[str, str]
_DATA_FILE_TO_SOURCE: dict[str, str]
_FALLBACK_DEFAULTS: dict[str, float]
_ASSETS_DIR = "assets/"

# 函数
_load_calcpack(path) -> dict[str, Any]
_extract_assets_from_calcpack(pack_path, target_dir) -> dict[str, str]
_resolve_asset_paths_in_layout(layout_data, asset_map) -> dict[str, Any]
_resolve_field_name(field) -> str
_build_context_from_entity(entity, namespace, level=90) -> dict[str, float]
```

### 文件 2：`viewer_help_content.py`

抽取 `_build_viewer_help()`（原为 CalcPackViewer 的静态方法）：

```python
def build_viewer_help() -> list[HelpSection]:
    """构造 CalcPackViewer 的使用说明帮助内容。"""
    ...
```

### 文件 3：`viewer_plugin_manager.py`

抽取插件管理对话框为独立类：

```python
class PluginManagerDialog(QDialog):
    """插件管理器对话框 — 导入/打包/查看插件。"""

    def __init__(self, parent=None, status_callback=None):
        ...

    def _import_plugin(self) -> None: ...
    def _build_plugin(self) -> None: ...
```

### 文件 4：`viewer.py` 保留部分

- `CalcPackViewer` 类主体
- `open_calcpack()` 便捷函数
- `main()` CLI 入口

移除的方法：
- `_build_viewer_help()` → 委托给 `viewer_help_content.build_viewer_help()`
- `_show_plugin_manager()` → 委托给 `PluginManagerDialog`
- `_import_plugin()`, `_build_plugin()` → 移入 `PluginManagerDialog`
- `.calcpack` 加载/context 构建 → 委托给 `viewer_pack_utils`

## 影响范围

| 文件 | 变动 | 风险 |
|------|------|------|
| `ui/viewer.py` | 删除 ~320 行，新增 3 个 import | 中 —— 需确保所有引用正确更新 |
| `ui/viewer_pack_utils.py` | 新建 | 低 —— 纯移动 + 导入 |
| `ui/viewer_help_content.py` | 新建 | 低 —— 纯移动 |
| `ui/viewer_plugin_manager.py` | 新建 | 低 —— 纯移动 + 少量 API 适配 |

## 向后兼容

- `open_calcpack()` 签名不变
- `main()` CLI 入口不变
- `CalcPackViewer` 所有公共方法签名不变
- Helper 函数通过 `from calc_framework.ui.viewer_pack_utils import _load_calcpack` 等路径访问（使用 `_` 前缀表示内部 API）

## 验证标准

1. [ ] 843 测试全部通过
2. [ ] ruff 检查无新增错误
3. [ ] `viewer.py` 行数 ≤ 500
4. [ ] 新增文件各 ≤ 150 行
5. [ ] `CalcPackViewer` 所有公共方法运行正常

## 考虑过的替代方案

### 方案 A：只提取帮助内容（最小改动）

减少行数有限，不能解决根本问题。

### 方案 B：全部保留在一个文件

放弃 —— 842 行 / 5 种职责已超出可维护性边界。

## 时间线

- 实施：与候选 4（本 ADR）同步
- 预计测试回退率：0%（纯移动逻辑，不改变行为）

## 术语表

- **CalcPack** (.calcpack)：计算配置包，内含 DAG 公式 + UI 布局 + 数据 + 资源
