# ADR-0027：Web 浏览器计算（WASM）技术选型

**日期**：2026-06-15  
**状态**：已批准（POC 阶段）  
**影响范围**：`web/frontend/src/calc/`、`web/wasm/`、`docs/plans/web-compact-wasm-plan.md`

---

## 1. 背景

Web 阶段 1–3 已完成：`成长参数` compact 下发、搜索 POST 瘦身、多段反推 API。用户目标 **G2** 要求浏览器内完成与桌面一致的配装 DAG 求值，减少依赖 PythonAnywhere / 下载 exe。

候选方案：

| 选项 | 描述 |
|------|------|
| A | **Pyodide** — 打包 Python 计算栈进浏览器 |
| B | **Rust/TS 重写** — 完整移植 DAG + 终末地公式 |
| C | **混合** — TS 曲线烘焙 + 轻量 DAG/WASM 求值，分阶段交付 |

---

## 2. 决策

**采用选项 C（混合），分三子阶段交付。**

| 子阶段 | 范围 | 产出 |
|--------|------|------|
| **4.1**（已完成） | `floor_linear` 曲线物化 TS 实现 + golden 夹具 + `calc_backend` 开关 | 公式层与 Python 对齐；canonical loadout golden |
| **4.2**（已完成） | TS `CallNode` 展开 + DAG 拓扑求值 + `loadout-context` API | 浏览器内 `evaluate-loadout` 全输出（任意配装） |
| **4.3** | 可选 Rust WASM 加速热点 / Worker 并行 | 体积与冷启动优化 |

**明确拒绝（4.1）**：

- **Pyodide 全栈**：首包 >15MB、冷启动 >3s，不符合 PA 静态托管与移动弱网场景。
- **4.1 内完整重写 1200+ 行 DAG**：维护成本与 Python 双轨风险过高。

---

## 3. 架构

```mermaid
flowchart TB
  subgraph client [浏览器]
    FE[ComputePage]
    MAT[TS curveMaterialize]
    DAG[TS dagEval 4.2+]
    FLAG[calc_backend api|wasm]
  end
  subgraph server [FastAPI]
    API["/api/compute/evaluate-loadout"]
  end
  FE --> FLAG
  FLAG -->|api 默认| API
  FLAG -->|wasm| MAT
  MAT --> CTX["/api/compute/loadout-context"]
  CTX --> DAG
  DAG --> OUT[outputs]
  FLAG -->|失败回退| API
```

### 3.1 Golden 契约

- 脚本：`web/wasm/export_loadout_golden.py` 从 Python `evaluate_loadout` 导出 `payload`、`context`、`outputs`、`dag`。
- 验收：曲线物化误差 ≤ 1e-6；canonical `outputs` 在 4.2 前由 Python golden 锁定，TS 回归不得回退。
- 校验：`web/wasm/verify_golden.mjs`（Node）+ `web/backend/tests/test_wasm_golden.py`。

### 3.2 特性开关

- 环境变量：`VITE_CALC_BACKEND=api|wasm`（默认 `api`）。
- 前端：`getCalcBackend()` → `evaluateLoadout()` 在 `wasm` 时先尝试本地路径，失败回退 API。

---

## 4. 体积与性能预算（4.1）

| 指标 | 目标 |
|------|------|
| 新增 JS（calc 模块） | ≤ 30 KB gzip |
| Golden JSON | ≤ 500 KB（随 DAG 导出，仅开发/CI） |
| FCP 影响 | 懒加载 `calc/*`，默认 `api` 零影响 |

---

## 5. 后果

**正面**

- 公式层先对齐，避免 WASM 与 Python 分叉。
- 默认 API 路径不变，PA 部署无回归风险。
- 4.2 可在 golden 保护下增量移植 `CallNode`。

**负面**

- 4.2 `wasm` 模式对任意配装本地求值；context 仍依赖 API（4.2b 可端口离线 context）。
- 短期内存在 TS/Python 双实现（曲线 + DAG 层），需 golden 守护。

---

## 6. 相关文档

- [`docs/plans/web-compact-wasm-plan.md`](../plans/web-compact-wasm-plan.md)
- ADR-0024 通用逆推抽象
- ADR-0011 DAG 六块架构
