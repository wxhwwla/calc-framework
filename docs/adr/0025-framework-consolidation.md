# ADR-0025：框架接口一致性巩固 — 异常层次、DataContextLoader、主题、工具类统一

**日期**：2026-06-13  
**状态**：已批准  
**影响范围**：`framework/`、`games/endfield/`、`games/arknights/`、`utils/gui/`

---

## 1. 动机

经过 ADR-0013（反推 SPI）、ADR-0023（标准游戏包架构）、ADR-0024（逆推完全抽象化）三轮抽象后，框架与游戏层的边界已基本清晰。但仍存在 4 个「接口已定义但游戏层未遵循」或「通用代码散落在游戏层」的问题。

---

## 2. 问题分析

### 2.1 异常层次断裂

框架定义了 `CalcFrameworkError(Exception)`，但游戏层的异常类（`DataLoadingError`、`DataLoadError`）直接继承 `Exception`。上层代码无法用 `except CalcFrameworkError` 统一捕获框架相关错误。

### 2.2 `CalcWorker` 散落在终末地层

`games/endfield/gui/shell/qt_worker.py` 是一个完全游戏无关的 QThread+QObject 包装器。它已经在被终末地使用，但明日方舟和其他未来游戏无法复用。

### 2.3 Endfield 未实现 `DataContextLoader` ABC

框架 `calc_framework.data.loader.DataContextLoader` 是 DAG 计算的标准数据上下文构建接口。Arknights 已正确实现，但 Endfield 的 `build_dag_context()` 是独立函数，未继承 ABC。这破坏了框架的「任意游戏通过 `DataContextLoader` 接入 DAG 引擎」的承诺。

### 2.4 主题系统碎片化

框架 `calc_framework.ui.theme.ThemeManager` 已提供 dark/light/high_contrast 三主题，通过 QSS 动态生成。但：
- Arknights `ArknightsDamageApp.py` 内联 `DARK_QSS` 字符串
- Arknights `ArknightsApp.py` 手写 `_apply_dark_style()`
- Endfield `qt_control_dock_builders.py` 内联 `_BTN_PRIMARY_STYLE`、`_COMBO_STYLE` 等

两个游戏都没有使用框架的 `ThemeManager`。

---

## 3. 设计方案

### 3.1 异常层次统一

```
CalcFrameworkError (framework/errors.py)
├── DataLoadingError (games/*/data_loading/__init__.py)
│   └── DataLoadError (games/*/data_loading/loader.py)
├── AdapterError (framework/config/adapter.py)
├── AttributeSchemaError (framework/data/attr_schema.py)
└── ...
```

游戏层 `DataLoadingError` 改为继承 `CalcFrameworkError`，保持 `except DataLoadingError` 的向后兼容。

### 3.2 `CalcWorker` 移入 `utils/gui/`

```
utils/gui/qt_worker.py  ← 从 games/endfield/gui/shell/qt_worker.py 移动
```

`CalcWorker` 零游戏依赖，是纯 Qt 工具类。移入 `utils/gui/` 后，Arknights 和未来游戏可直接复用。终末地通过 `from utils.gui.qt_worker import CalcWorker` 导入。

### 3.3 Endfield 实现 `DataContextLoader`

当前 Endfield 的 `calc/dag_adapter/loader.py` 中有 `EndfieldContextLoader` 类，需要确认它是否已继承 `DataContextLoader`。如果未继承，改为继承并实现 `build_context()` 方法。

同时，`build_dag_context()` 函数改为调用 `EndfieldContextLoader().build_context()`。

### 3.4 主题系统统一

第一步（本次）：在 Arknights 中移除内联 QSS，改用 `ThemeManager`。Endfield 的内联样式暂保留（改动面太大，需要逐控件迁移）。

第二步（后续）：Endfield 逐步迁移到 `ThemeManager`。

---

## 4. 实现步骤

| 步骤 | 内容 | 影响范围 |
|:--:|------|------|
| 1 | `DataLoadingError` → 继承 `CalcFrameworkError` | `games/endfield/data_loading/__init__.py` |
| 2 | `CalcWorker` 移入 `utils/gui/qt_worker.py`，更新终末地 import | `games/endfield/gui/shell/qt_worker.py` → `utils/gui/qt_worker.py` |
| 3 | 检查并修复 Endfield `DataContextLoader` 实现 | `games/endfield/calc/dag_adapter/loader.py` |
| 4 | Arknights 主题迁移到 `ThemeManager` | `games/arknights/gui/ArknightsApp.py`、`ArknightsDamageApp.py` |
| 5 | 运行全量测试确认无回归 | `framework/tests/` + `games/endfield/tests/` + `games/arknights/tests/` |
