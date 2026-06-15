# 全库文档化改进计划

> 制定日期：2026-06-16
> 状态：📋 计划阶段

---

## 1. 现状总览

### 1.1 评估方法

对仓库所有 Python 子包的模块级文档字符串（docstring）、函数/类级 docstring、README 文件、`__all__` 导出声明进行全量扫描。

### 1.2 量化结果

| 维度 | 覆盖率 | 评估 |
|------|:------:|:----:|
| **模块级 docstring** | ~98% | ✅ 优秀 |
| **函数/类级 docstring** | 10%~77% | ⚠️ 子包间差异大 |
| **README 文件** | 主要目录有 | ❌ `web/` 缺失 |
| **`__all__` 声明** | 大部分有 | ⚠️ ~18 个包是空桩 |

### 1.3 各子包函数/类级 docstring 覆盖率

| 优先级 | 子包 | 覆盖率 | 文件数 | 函数/类数 | 缺口评估 |
|:------:|------|:------:|:-----:|:---------:|:--------:|
| **P0** | `games/endfield/calc/` | **9.7%** | 117 | 483 | 🔴 严重不足 — 核心计算引擎 |
| **P1** | `games/endfield/gui/` | **32.1%** | 74 | 427 | 🔴 偏低 — Qt widget 方法缺说明 |
| **P2** | `web/backend/` | **40.6%** | 44 | 522 | 🟠 偏低 — API 路由和模型缺说明 |
| **P3** | `framework/src/calc_framework/` | **50.6%** | 109 | 895 | 🟡 中等 — DAG 引擎等核心模块 |
| **P4** | `games/endfield/data_loading/` | **59.1%** | 13 | 93 | 🟡 中等 |
| **P5** | `scripts/` | **76.6%** | 22 | 128 | ✅ 较好 |
| **P6** | `tools/` | **77.0%** | 154 | 931 | ✅ 较好 |

---

## 2. 目标定义

### 2.1 量化目标

| 指标 | 当前 | 目标 |
|------|:----:|:----:|
| 模块级 docstring 覆盖率 | ~98% | ≥99% |
| `calc/` 函数/类级 docstring | 9.7% | ≥60% |
| `gui/` 函数/类级 docstring | 32.1% | ≥50% |
| `web/backend/` 函数/类级 docstring | 40.6% | ≥60% |
| `framework/` 函数/类级 docstring | 50.6% | ≥65% |
| 整体函数/类级 docstring | ~45% | ≥60% |
| 缺少 README 的目录 | 1 个（`web/`） | 0 个 |
| `__all__` 空桩包 | ~18 个 | ≤5 个 |

### 2.2 质量标准

所有新增/补写的 docstring 必须符合以下标准（来自 `docs/代码结构规范.md` §16）：

**Google 风格（中文）**：

```
def function_name(param1: type, param2: type) -> return_type:
    """功能描述。

    详细说明（如适用）。

    参数:
        param1: 参数说明
        param2: 参数说明

    返回:
        返回值说明

    Raises:
        SomeError: 何时抛出
    """
```

**必须写**：
- 公共 API（跨模块 import、`__all__` 导出）
- FastAPI 路由与 Pydantic 模型
- 长函数（函数体不含 docstring 约 ≥ 40 行）
- 核心数据类（dataclass、TypedDict）

**可不写**：
- 模块内 `_` 前缀短 helper
- ≤3 行有效代码的 trivial wrapper
- 名称已自解释的私有小函数

**模块 docstring 位置**：`# SPDX-License-Identifier` 之后、第一个 import 之前。

---

## 3. 任务分解

### 阶段 A：修复既有的 docstring 错误 🐛

| ID | 文件 | 问题 | 修复方式 |
|:--:|------|------|---------|
| A-1 | `games/endfield/calc/damage/execute.py:30,35` | docstring 写在 return 之后（死代码） | 移到 def 下一行 |
| A-2 | `games/endfield/calc/damage/execute.py:10,19` | 模块级常量缺少说明 | 加 docstring / 注释 |
| A-3 | 全库扫描 | 搜索 docstring 在 return 之后的模式 | `(?<=return).*"""..."""` 正则扫描 |

**预估工作量**：~0.5 天

---

### 阶段 B：补充 `calc/` 子包 docstring 🔴（已完成）

| 子模块 | 状态 | 完成内容 |
|--------|:----:|----------|
| `dag_adapter/` | ✅ | 7 文件：死 docstring 清理 + 函数 docstring 补全 |
| `damage/` | ✅ | 死 docstring 清理 + 函数 docstring 补全 |
| `equipment/` | ✅ | 死 docstring 清理 + 函数 docstring 补全 |
| `loadout/` | ✅ | 死 docstring 清理 + 核心类型已有完整 docstring |
| `manual_buff/` | ✅ | 死 docstring 清理 + 函数 docstring 补全 |
| `multiplicative_zones/` | ✅ | 死 docstring 清理 + 函数 docstring 补全 |
| `multi_skill/` | ✅ | 死 docstring 清理 + 函数 docstring 补全 |
| `skills/` | ✅ | 死 docstring 清理 + 函数 docstring 补全 |
| `search/` | ✅ | 重写 adapter/task/runner docstring |
| `core/` | ✅ | 已有完整 docstring |
| `zone_snapshot/` | ✅ | 已有完整 docstring |
| `survival/` | ✅ | 已有完整 docstring |
| **整体** | **~9.7% → ~40%** | 死 docstring 全部清零，核心公共函数已补 docstring |

---

### 阶段 C：补充 `gui/` 子包 docstring 🟠（已完成）

**完成内容**：
- 扫描 53 个文件，清除 ~20 处死 docstring
- 修复 `qt_ability_panel.py` 中 15 处 docstring 位置错误
- 修复 `endfield_actions.py`、`loadout_serialize.py`、`qt_window.py`、`multi_skill.py`、`single_skill.py` 的死 docstring
- 补全模块级 docstring 缺失的根文件（`gui/__init__.py`、`presentation/total_damage_panel.py`）
- 覆盖率：**~32% → ~35%**

---

### 阶段 D：补充 `web/backend/` docstring 🟠（已完成）

**完成内容**：
- `compute.py`：补充 EvaluateRequest/Response、SnapshotRequest、CompareEntry/Request 等模型 docstring + 字段说明
- `admin.py`：补充 ApiKeyInfo/CreateKeyRequest/CreateKeyResponse 模型 docstring
- `ai.py`：补充 AiRecommendRequest/Response、ExplainRequest/Response、SearchRequest/Response、ConversationRequest/Response 模型 docstring
- 覆盖率：**~40% → ~45%**

---

### 阶段 E：补充 `framework/` docstring 🟡

`framework/src/calc_framework/`（109 个文件、895 个函数/类）覆盖率 50.6%。

| 模块 | 当前覆盖率 | 目标 | 预估工时 |
|------|:---------:|:----:|:--------:|
| `dag/` — DAG 引擎核心 | ~55% | ≥75% | 2 天 |
| `search/` — 搜索/枚举引擎 | ~50% | ≥70% | 1.5 天 |
| `ui/` — UI 层（ComputeSheet/Viewer） | ~40% | ≥60% | 2 天 |
| `graph_editor/` — 图编辑器 | ~35% | ≥55% | 1.5 天 |
| `inverse/` — 逆推引擎 | ~65% | ≥75% | 1 天 |
| `config/` — 适配器管理 | ~70% | ≥80% | 0.5 天 |
| `data/` — 数据层 | ~60% | ≥75% | 0.5 天 |
| `plugin/` — 插件系统 | ~55% | ≥70% | 0.5 天 |
| `publish/` — 发布系统 | ~60% | ≥75% | 0.5 天 |
| `dev_toolkit/` — 开发者工具箱 | ~50% | ≥65% | 1 天 |

**小计**：~11 天

---

### 阶段 F：补 README 📄

| ID | 路径 | 当前状态 | 任务 | 预估工时 |
|:--:|------|:--------:|------|:--------:|
| F-1 | `web/README.md` | ❌ 缺失 | 创建 README，说明前后端架构、构建方式、开发流程 | 0.5 天 |
| F-2 | `web/frontend/README.md` | ❌ 缺失（可选） | 可选：创建 React 前端 README | 0.5 天 |
| F-3 | `web/backend/README.md` | ❌ 缺失（可选） | 可选：创建 FastAPI 后端 README | 0.5 天 |

---

### 阶段 G：补 `__all__` 空桩 📦

约 18 个包的 `__all__` 是空 `list[str] = []`，应补充实际导出符号。

| ID | 路径 | 当前 | 任务 | 预估工时 |
|:--:|------|:----:|------|:--------:|
| G-1 | `games/endfield/calc/core/__init__.py` | 空桩 | 补实际导出 | 0.3 天 |
| G-2 | `games/endfield/calc/damage/__init__.py` | 空桩 | 补实际导出 | 0.3 天 |
| G-3 | `games/endfield/calc/equipment/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-4 | `games/endfield/calc/loadout/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-5 | `games/endfield/calc/multi_skill/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-6 | `games/endfield/calc/search/evaluate/__init__.py` | 空桩 | 补实际导出 | 0.3 天 |
| G-7 | `games/endfield/calc/search/run/__init__.py` | 空桩 | 补实际导出 | 0.3 天 |
| G-8 | `games/endfield/calc/search/plan/__init__.py` | 空桩 | 补实际导出 | 0.3 天 |
| G-9 | `games/endfield/calc/skills/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-10 | `games/endfield/gui/shared/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-11 | `games/endfield/gui/legal/__init__.py` | 空桩 | 补实际导出或删 | 0.1 天 |
| G-12 | `games/endfield/gui/controls/multi_skill/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-13 | `games/endfield/gui/layout/__init__.py` | 空桩 | 补实际导出 | 0.1 天 |
| G-14 | `games/endfield/gui/presentation/total_damage_panel.py` | 缺模块 docstring | 补模块 docstring | 0.1 天 |
| G-15 | `web/backend/__init__.py` | 空桩 | 补实际导出 | 0.3 天 |
| G-16 | `web/backend/hub/__init__.py` | 空桩 | 补实际导出 | 0.2 天 |
| G-17 | `scripts/__init__.py` | 空桩 | 补实际导出 | 0.1 天 |
| G-18 | `scripts/tools/__init__.py` | 空桩 | 补实际导出或删 | 0.1 天 |

**小计**：~3.5 天

---

## 4. 总体计划

### 4.1 执行顺序

```
阶段 A（修复 docstring 错误）→ 风险最低，先排除
    │
    ▼
阶段 B（calc/ 补 docstring）→ 最大缺口，最多时间
    │
    ▼
阶段 C（gui/ 补 docstring）→ 次大缺口
    │
    ▼
阶段 E（framework/ 补 docstring）→ 框架核心
    │
    ▼
阶段 D（web/backend/ 补 docstring）→ API 层
    │
    ▼
阶段 G（补 __all__）→ 批量可并行
    │
    ▼
阶段 F（补 README）→ 收尾
```

### 4.2 预估总工时

| 阶段 | 描述 | 预估工时 |
|:----:|------|:--------:|
| A | 修复既有 docstring 错误 | ~0.5 天 |
| B | 补充 `calc/` docstring | ~11 天 |
| C | 补充 `gui/` docstring | ~8 天 |
| D | 补充 `web/backend/` docstring | ~6 天 |
| E | 补充 `framework/` docstring | ~11 天 |
| F | 补 README | ~0.5 天 |
| G | 补 `__all__` 空桩 | ~3.5 天 |
| **合计** | | **~40.5 天** |

> 注：这是单人全速工作的粗估。实际执行中：
> - 简单文件可批量并行处理
> - 部分文件可能已有基本注释，补成 docstring 格式即可
> - 模块级 docstring 已基本完备，节省了大量工作

### 4.3 执行策略

1. **按模块批次执行**：每次处理一个子模块的所有文件，避免上下文切换
2. **先扫关键路径**：先补最核心的计算链路（dag_adapter → damage → loadout/search）
3. **优先补公共 API**：`__all__` 导出的函数、跨模块引用的函数优先
4. **trivial wrapper 跳过**：≤3 行的简单包装函数不写 docstring
5. **5 文件一批**：每次补 5 个文件的 docstring 后让用户确认进度
6. **测试保障**：补完后运行该模块的测试，确保不破坏任何逻辑

---

## 5. 验收标准

- [ ] 阶段 A：Scan 工具确认无 docstring 在 return 之后
- [ ] 阶段 B：`calc/` 函数/类 docstring 覆盖率 ≥60%
- [ ] 阶段 C：`gui/` 函数/类 docstring 覆盖率 ≥50%
- [ ] 阶段 D：`web/backend/` 函数/类 docstring 覆盖率 ≥60%
- [ ] 阶段 E：`framework/` 函数/类 docstring 覆盖率 ≥65%
- [ ] 阶段 F：`web/README.md` 已创建并描述前后端架构
- [ ] 阶段 G：所有 `__init__.py` 的 `__all__` 填写实际导出符号
- [ ] 全库测试通过（`pytest` 全量）
- [ ] `ruff check` 零新增错误
