# 外部缺陷报告核实总结（2026-06-17）

> **来源**：Trae Work 生成的 `calc-framework-defects.html`（分析日期 2026-06-16，基于 **v3.26.13**）。  
> **核实对象**：本仓库当前代码 **v3.27.16**（2026-06-17 逐项对照源码 + 实测覆盖率）。  
> **关联计划**：分步修复任务见 [`.trae/plans/当前任务计划.md`](../../.trae/plans/当前任务计划.md)。

---

## 1. Executive Summary

| 维度 | 报告声称 | 核实结论 |
|------|----------|----------|
| Critical | 2 项安全/CI 缺陷 | **2/2 属实** |
| High | 12 项 | **约 10/12 属实**；H3 影响夸大，H7 数据过时 |
| Medium | 24 项 | **约 20/24 方向正确**；M10/M22 为演示适配器非空桩 |
| Low | 15 项 | **基本属实**；L12 行数 642（报告写 749） |
| Open Issues | 13 项 Slice 未实现 | **段落过时**——Slice 1–10 核心搜索已在 §4 会话手册记录完成 |

**总体评价**：报告作为**静态代码审查**质量较高，安全与工程债务项可直接采纳；**覆盖率 15%** 与 **Open Issues 功能缺失** 两处与当前仓库不符，修复优先级应以上文核实为准。

---

## 2. Critical — 全部属实

### C1 · 管理 API 与数据写接口无认证 `[SEV-HIGH]`

| 项 | 内容 |
|----|------|
| **位置** | `web/backend/api/admin.py`（`/api/admin/keys` CRUD）；`web/backend/api/data.py`（characters/weapons/equipments POST/PUT/DELETE） |
| **现象** | 路由无 `Depends`、Admin Token 或 API Key 校验 |
| **影响** | 公网部署时：任意人可创建/吊销 Key、篡改游戏 JSON，污染计算结果 |
| **缓解语境** | 仅 localhost / 内网 / PA 单用户部署时实际风险较低，**不能抵消代码缺陷** |

### C2 · 安全审计 CI 形同虚设 `[SEV-HIGH]`

| 项 | 内容 |
|----|------|
| **位置** | `.github/workflows/security-audit.yml` |
| **现象** | `npm audit` 设 `continue-on-error: true`；`pip-audit \|\| true`；`detect-secrets scan` 无 baseline、无 `--fail-on-unaudited`；触发路径未含根 `requirements.txt` |
| **影响** | 依赖漏洞与新增密钥泄露不会阻断 CI |

---

## 3. High — 逐项核实

| ID | 结论 | 说明 |
|----|:----:|------|
| H1 | ✅ | `inverse/engine.py` `fit_auto()` → `except Exception: continue`，无日志 |
| H2 | ✅ | `search/parallel.py` `run_parallel()` → `except Exception: pass` |
| H3 | ⚠️ | `dag/block_cache.py` 使用 `hash()`；**纯内存缓存**，重启即清空，跨进程错误命中风险被夸大；仍建议改 `hashlib` |
| H4 | ✅ | `RateLimitMiddleware` 在 async 中同步读写 JSON |
| H5 | ✅ | 明日方舟 `calc/` ~12 模块 vs 终末地 118+；无独立伤害引擎/配装搜索 |
| H6 | ✅* | 根 `requirements.txt` 仅 6 项，**不能**跑桌面 GUI；* intentional for Docker/Web，见 `docs/依赖说明.md` |
| H7 | ❌ | 报告 ~15%；实测 `api/` **69%**、`web/backend` **66%**（142 passed, 2026-06-17） |
| H8 | ✅ | 限速用进程内 `defaultdict`；注释写明单 worker |
| H9 | ✅ | `data.py` async 路由中同步 `json.load/dump` |
| H10 | ✅ | `inverse/base.py` `_search()` 三重循环，无超时 |
| H11 | ✅ | `inverse/registry.py` 两处 `except ImportError: pass` |
| H12 | ✅ | `compute.py` 多处 `HTTPException(detail=str(e))` 可能泄露内部信息 |

---

## 4. Medium / Low — 摘要

### 4.1 安全与 Web（Medium M1–M4, M16–M17, M23）

- **M1** ✅ API Key salt 来自 key 前 16 字符，前缀固定 `cf_`
- **M2** ✅ 未发现 POST 请求体大小限制
- **M3** ✅ Dockerfile 无 `USER`，容器以 root 运行
- **M4** ⚠️ `allow_methods/headers=["*"]`；`allow_origins` 限 localhost
- **M16–M17、M23** ✅ 无数据缓存、Docker 复制多余目录、Redis 限速未实现

### 4.2 异常与一致性（M5–M9, M24）

- **M5** ✅ `DAGError` 未继承 `CalcFrameworkError`
- **M6** ✅ `mod` 除零返回 0.0，与其它运算符不一致
- **M7–M9** ✅ 全局 500 无诊断；compare 吞异常；搜索 import 失败直接 500
- **M24** ✅ `search/engine.py` 死代码表达式 `processed_count + skipped`

### 4.3 架构与文档差距（M10–M13, M20–M22）

- **M10/M22** ⚠️ `card_rpg` / `genshin_like` 为 **DAG 演示适配器**（有 JSON + README），非完全空桩
- **M13** ✅ 明日方舟数据在 `framework/adapters/arknights/` + scout 输出；终末地在 `games/endfield/data/`（ADR-0023 不一致）
- **M20–M21** ⚠️ endfield `fail_under=75` vs 文档 80%+；「乘区层 ~99%」与 web 覆盖率是不同维度

### 4.4 性能与代码质量（M14–M15, M18–M19, L1–L15）

- **M14–M15** ✅ BlockCache 无淘汰；SQLite 多 worker 写入无 WAL/锁策略（需运行时验证）
- **M18–M19、L1–L15** ✅ 报告描述与源码一致（`web/backend/api/` 现 **27** 文件，超 ADR-0001 上限 20）

---

## 5. 报告过时 / 夸大项（勿照搬）

| 报告内容 | 当前事实 |
|----------|----------|
| Web 后端覆盖率 ~15% | **66–69%**（`pytest web/backend/tests --cov`） |
| 13 Open Issue = 核心搜索未实现 | Slice 1–10 / MVP 搜索已在 v3.27.x 实现，见会话手册 §4 |
| hash 不稳定 → 缓存错误命中 | 内存缓存在单进程内稳定；重启清空，主要为设计债 |
| 「双游戏支持名不副实」 | 方向正确但需限定：**明日方舟缺伤害/配装引擎**，非「完全无支持」 |

---

## 6. 分步修复计划（总览）

详细任务拆解、验收标准与 TDD 顺序见 [`.trae/plans/当前任务计划.md`](../../.trae/plans/当前任务计划.md)。

### Phase 0 — 安全与 CI（P0，1–2 天）

1. **Admin 认证**：环境变量 `CALC_ADMIN_TOKEN` + `Depends(verify_admin_token)` 保护 `/api/admin/*` 与 `data.py` 全部写操作
2. **安全 CI**：移除 `continue-on-error` / `|| true`；添加 `.secrets.baseline` + `detect-secrets audit --fail-on-unaudited`；扩展 workflow `paths` 含 `requirements*.txt`
3. **异常泄露**：`compute.py` 生产模式返回通用错误，详细异常仅写日志

### Phase 1 — 稳定性（P1，2–3 天）

4. **静默吞异常**：H1/H2/H11 改为 `logger.warning/exception` + 可选 debug 计数
5. **hash 确定性**：`block_cache.py` 改用 `hashlib.sha256`
6. **requirements 文档化**：根 `requirements.txt` 顶部注释指向 `docs/依赖说明.md`；或拆 `requirements-web.txt` / `requirements-dev.txt`

### Phase 2 — Web 后端可靠性（P2，3–5 天）

7. **异步 I/O**：admin/data 文件读写迁 `asyncio.to_thread` 或 `aiofiles`
8. **限速多 worker**：Redis 后端（可选）或文档明确「单 worker + 反向代理限速」
9. **请求体限制**：Starlette `ContentSizeLimitMiddleware` 或 nginx 层限制
10. **测试补强**：admin 认证、data 写保护、异常路径；目标 `api/` ≥75%

### Phase 3 — 框架质量（P3，按需）

11. **异常层级**：`DAGError(CalcFrameworkError)`
12. **BlockCache LRU/TTL**
13. **inverse 搜索超时** + `_search` 早停配置
14. **api/ 目录拆分**：27→≤20（ADR-0001）
15. **Dockerfile**：非 root `USER`、 slim 复制范围

### Phase 4 — 生态与文档（长期）

16. 明日方舟伤害/配装能力（见 `arknights-desktop-web-parity.md` 后续）
17. ADR-0023 数据路径统一
18. 代码签名、Desktop i18n、自动更新生产验证（见 `improvement-roadmap.md`）

---

## 7. 验证记录

| 验证项 | 命令 / 方法 | 结果 | 日期 |
|--------|-------------|:----:|:----:|
| admin 无认证 | 源码 grep + 阅读路由 | ✅ 确认 | 2026-06-17 |
| security-audit.yml | 阅读 workflow | ✅ 确认 | 2026-06-17 |
| Web 后端覆盖率 | `pytest web/backend/tests --cov=api --cov-report=term` | **69%** | 2026-06-17 |
| fit_auto / run_parallel 吞异常 | 源码 | ✅ 确认 | 2026-06-17 |
| requirements.txt 6 项 | 读文件 | ✅ 确认 | 2026-06-17 |

---

## 8. 参考

- 原始报告：`calc-framework-defects.html`（Trae Work, 2026-06-16）
- 改进路线图：[`improvement-roadmap.md`](improvement-roadmap.md)
- 依赖说明：[`docs/依赖说明.md`](../依赖说明.md)
- 架构约束：[`docs/adr/0001-code-layout-constraints.md`](../adr/0001-code-layout-constraints.md)
