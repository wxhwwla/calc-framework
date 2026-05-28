# ADR-0009：PySide6 GUI 迁移 — 完全依赖抽象框架

**状态**：已批准  
**日期**：2026-05-28  
**决策者**：维护者  
**影响范围**：`main.py`、`gui_design/shell/`、`framework/src/calc_framework/ui/`

---

## 1. 现状

当前仓库并存两套 GUI：

| | customtkinter 版 | PySide6 版 |
|--|-----------------|-----------|
| 类名 | `DamageCalculatorApp` | `QtDamageApp` |
| 位置 | `gui_design/shell/app.py` + 6 个 mixin | `gui_design/shell/qt_app.py` |
| 状态 | 完整实现 | 功能等价（选择/确认/搜索/预设/dock） |
| 入口 | `is_qt()=False` | `is_qt()=True` |
| 右栏 | CTkFrame + 标签展示 | QTableWidget 三列展示 |
| ComputeSheet | ❌ 未使用 | ❌ 未使用 |
| 框架依赖 | ❌ 无 | ❌ 无 |

**关键发现**：`qt_app.py` 已经是一个功能完备的 PySide6 实现，迁移工作比最初估算小得多。

---

## 2. 迁移方案

### 2.1 决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 基础 | 以现有 `qt_app.py` 为基座，不重写 | 避免了数周工作量 |
| 右栏 | 用 ComputeSheet 替换 QTableWidget 区 | 抽象框架关键目标 |
| DAG | ComputeSheet 使用 DAG 引擎求值 | Phase 1 已完成 |
| CTk | 标记弃用，迁移后移除 | 减少维护负担 |
| 版本 | 本次改动用 `--minor` bump | 非破坏性架构变更 |

### 2.2 架构变化

```
迁移前:
  main.py → is_qt()? → 否 → DamageCalculatorApp (CTk, 手写右栏)
                       → 是 → QtDamageApp (PySide6, 手写右栏)

迁移后:
  main.py → QtDamageApp (PySide6, 唯一入口)
              └── 右栏: ComputeSheet (DAG 驱动)
              └── 输入面板: ComputeSheet 控件
              └── 高级页: QtControlDock (不变)
              └── CTk DamageCalculatorApp → 标记弃用
```

### 2.3 执行步骤

| 步骤 | 内容 |
|------|------|
| 1 | 写入本文档（ADR-0009） |
| 2 | `main.py` 默认走 PySide6，移除 `is_qt()` 分支 |
| 3 | `qt_app.py` 右栏接入 ComputeSheet |
| 4 | `qt_app.py` 在角色/武器选择下方添加 ComputeSheet 输入控件区 |
| 5 | 连接选择变更信号 → ComputeSheet 重建 |
| 6 | `gui_design/backends/__init__.py` 标记 CTk 弃用 |
| 7 | 运行全部测试验证无回归 |

---

## 3. 风险与缓解

| 风险 | 概率 | 缓解 |
|------|------|------|
| ComputeSheet 输入控件与手写技能/信赖面板冲突 | 中 | ComputeSheet 仅渲染 layout.json 中 `user_input` 变量，不覆盖角色/武器选择 |
| CTk 导入还在其他模块被引用 | 低 | 保持模块存在，仅 `main.py` 切换入口 |
| 老用户 CTk 习惯差异 | 低 | UI 布局一致，仅底层换框架 |
