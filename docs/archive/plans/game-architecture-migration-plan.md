# 游戏包架构迁移路线图

对应 ADR-0023，将终末地包结构逐步对齐到"纯 DAG 适配器架构"标准模板。

---

## 优先级排序

| 优先级 | 候选 | 影响范围 | 风险 | 预估工作量 |
|--------|------|---------|------|-----------|
| **P0** | **候选 3：对齐目录结构 + 定义 game-template** | `games/endfield/` 所有文件 | 低 | 2-3 天 |
| P1 | 候选 1：伤害公式迁移到框架适配器层 | `calc/damage/` 15 文件 + `adapters/endfield/functions.py` | 高 | 2-3 周 |
| P2 | 候选 2：GUI 统一到单片式 + ComputeSheet | `gui_design/` 60+ 文件 | 中 | 1-2 周 |
| P3 | 候选 4：装备/搜索/配装 → 框架级插件 | `calc/equipment/`, `calc/search/`, `calc/loadout/` | 中 | 2-3 周 |

---

## P0：对齐目录结构 + game-template

### 目标

终末地的 `games/endfield/` 目录结构对齐 ADR-0023 的标准模板，明日方舟作为参考实现。

### 具体步骤

#### 步骤 1：创建 game-template 目录

```
docs/game-template/
├── games/              # 游戏包骨架
│   └── _template/
│       ├── __init__.py
│       ├── _package_meta.py
│       ├── calc/
│       │   └── dag_adapter/
│       │       ├── __init__.py
│       │       ├── loader.py
│       │       └── adapter.py
│       ├── gui/
│       │   └── _template_App.py
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── conftest.py
│       │   ├── test_adapter.py
│       │   └── test_dag_compute.py
│       └── framework_bridge.py
├── test_template.py    # 模板验证脚本
└── README.md           # 使用说明
```

#### 步骤 2：终末地目录结构对齐 ✅ 已完成（2026-06-02）

改动集中在 `games/endfield/` 顶层：

```
迁移前:                 迁移后:
games/endfield/        games/endfield/
├── calc/              ├── calc/                  ← 不变
├── data/              ├── data/                  ← 不变
├── data_loading/      ├── data_loading/          ← 不变
├── gui_design/        ├── gui/                   ← 重命名 ✅
├── tests/             ├── tests/                 ← 不变
├── framework_bridge   ├── framework_bridge.py    ← 不变
├── main.py            ├── main.py                ← 不变
├── _replace_imports   └── ...                    ← 其他文件归类
├── upload_meta.py
├── ui_preferences
│   └── ... (legacy)
```

关键变化：
- `gui_design/` → `gui/`（子目录保持不变）✅ 已执行
- 更新了 150+ 个外部文件中的导入路径
- 更新了所有文档（会话接续手册、代码结构规范、操作指令集、README、CONTEXT）
- 1056 个测试全部通过

#### 步骤 3：更新框架适配器路径引用

`framework/adapters/endfield/` 中如果有引用旧路径的需要更新。

#### 步骤 4：测试验证 ✅ 已完成

所有测试通过（1056 passed, 1 skipped, 9 subtests passed）。game-template 可用于创建第三个游戏包。

---

## P1：伤害公式迁移到框架适配器层

### 目标

将 `games/endfield/calc/damage/` 中的伤害公式逐步提取为 DAG 自定义函数，注册到 `framework/adapters/endfield/functions.py`。

### 背景

终末地目前有两条计算路径：
1. **本地引擎**：`calc/damage/engine/calculate.py` — 历史实现
2. **DAG 引擎**：`calc/dag_adapter/adapter.py` → DAG 求值 — 框架实现

两条路径都用同一个 DataContext，但公式实现是独立的，需要保持结果一致。

### 策略：并行验证 + 逐步迁移

不删除本地引擎，而是通过测试验证 DAG 输出与本地引擎一致后，逐步关闭本地路径。

```
阶段 1: 在 functions.py 中实现 DAG 版本
          ↓
阶段 2: 测试验证两路输出一致
          ↓
阶段 3: 调用方切换到 DAG 路径
          ↓
阶段 4: 标记本地引擎为 @deprecated
          ↓
阶段 5: 删除本地引擎代码
```

### 步骤 1：审计 formula.py → functions.py

`games/endfield/calc/damage/formula.py` 中的核心公式：

| 公式 | 迁移目标 | 复杂度 |
|------|---------|--------|
| `calculate_physical_damage()` | `functions.py` → `physical_damage()` | 低 |
| `calculate_spell_damage()` | `functions.py` → `spell_damage()` | 低 |
| `calculate_true_damage()` | `functions.py` → `true_damage()` | 低 |
| 15 乘区计算 | 框架 DAG 子图 | 中 |
| 异常状态/腐蚀伤害 | `functions.py` → `abnormal_damage()` | 中 |

### 步骤 2：在 functions.py 中实现 DAG 版本

参照 `framework/adapters/arknights/functions.py` 的模式，在 `framework/adapters/endfield/functions.py` 中添加自定义函数：

```python
# framework/adapters/endfield/functions.py
def physical_damage(ctx: DataContext, **kwargs) -> float:
    """物理伤害公式（与本地引擎计算结果一致）。"""
    # 公式实现...
```

### 步骤 3：测试双重验证

创建 `games/endfield/tests/framework/test_formula_consistency.py`：

```python
def test_physical_damage_consistency():
    本地结果 = evaluate_physical_damage(...)    # 旧引擎
    dag_result = compute_via_dag(...)           # DAG functions.py
    assert abs(本地结果 - dag_result) < 1e-6
```

### 步骤 4：调用方迁移

| 调用方 | 当前路径 | 切换目标 |
|--------|---------|---------|
| `calc/dag_adapter/adapter.py` | 直接调用 `calc/damage/formula.py` | DAG 求值 |
| `calc/multiplicative_zones/` | 调用 `calc/damage/` | DAG 求值 |
| `calc/search/` | 调用本地引擎 | DAG 求值 |
| `gui/` 面板 | 调用本地引擎 | DAG 求值 |

---

## P2：GUI 统一到单片式 + ComputeSheet

### 目标

终末地 GUI 从模块化 `gui_design/` 重构为单片式 `gui/EndfieldApp.py`，与明日方舟的 `gui/ArknightsDamageApp.py` 模式一致。

### 方向

```
gui_design/                          gui/
├── shell/                           ├── EndfieldApp.py        ← 单片 QMainWindow
│   ├── qt_app.py                    ├── panels/               ← 可保留的分面板（如果太大）
│   ├── qt_app_search_mixin.py       │   ├── selection.py
│   ├── qt_app_dialog_mixin.py       │   ├── controls.py
│   └── ...                          │   └── display.py
├── panels/                          ├── shared/               ← 保留
├── controls/                        ├── legal/                ← 保留
├── presentation/                    └── ...
├── shared/
├── legal/
└── designer/
```

### 关键变更

1. 用 `framework.ui.compute_sheet.ComputeSheet` 替代自定义面板
2. 布局由 `framework/adapters/endfield/ui/layout.json` 定义
3. 搜索 UI 通过框架搜索 API 桥接

---

## P3：装备/搜索/配装 → 框架级插件

### 目标

将终末地特有的装备/搜索/配装系统暴露为框架插件接口。

### 方向

- `calc/equipment/` → `framework/src/calc_framework/plugins/equipment/`
- `calc/search/` → `framework/src/calc_framework/plugins/search/`
- `calc/loadout/` → `framework/src/calc_framework/plugins/loadout/`

### 插件接口

```python
# framework/src/calc_framework/plugins/interface.py
class GamePlugin(ABC):
    @abstractmethod
    def get_equipment_system(self) -> EquipmentSystem | None: ...
    @abstractmethod
    def get_search_engine(self) -> SearchEngine | None: ...
    @abstractmethod
    def get_loadout_optimizer(self) -> LoadoutOptimizer | None: ...
```

---

## 依赖关系

```
P0（对齐结构）
  └── 前置条件：无
  └── 后续：所有后续步骤依赖标准结构

P1（伤害公式迁移）
  └── 前置条件：P0 完成（至少目录对齐部分）
  └── 后续：P2（GUI 统一后使用纯 DAG 公式）

P2（GUI 统一）
  └── 前置条件：P1 至少完成阶段 1-2（DAG 公式可用）
  └── 后续：无

P3（框架插件）
  └── 前置条件：P0 完成
  └── 后续：无
```

## 当前优先级

**P0 → 对齐目录结构 + game-template** 已经开始执行。

下一步：确定 game-template 的具体文件内容，然后开始终末地目录重构。
