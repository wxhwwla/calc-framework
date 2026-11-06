# Calc Framework — Web 版

> Calc Framework 的 Web 端实现，包括 FastAPI 后端和 React 前端。

---

## 目录结构

```
web/
├── backend/           FastAPI 后端
│   ├── api/           REST API 路由（compute/search/data/admin 等）
│   ├── hub/           配置包市场存储
│   ├── main.py        FastAPI 入口 + 路由注册 + 中间件
│   ├── bridge.py      日志/工具函数
│   ├── asgi.py        WSGI/ASGI 适配入口
│   └── run_packaged_main.py  PyInstaller 打包入口
├── frontend/          React + TypeScript + Vite 前端
│   ├── src/
│   │   ├── pages/     页面（ComputePage / DesignerPage / PackDesignerPage 等）
│   │   ├── components/ 组件（calculator / designer / pack_designer）
│   │   ├── api/        TypeScript API 封装
│   │   ├── store/      Zustand 状态管理
│   │   └── utils/     工具函数
│   └── package.json
├── hub/               静态 Calc Hub 页面（配置包/插件市场）
├── wasm/              WebAssembly 曲线计算模块
└── scripts/           部署/构建脚本
```

---

## 快速开始

### 后端

```bash
cd web/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8180
```

API 文档：启动后访问 `http://localhost:8180/api/docs`（手动 `uvicorn` 启动需 `CALC_ENABLE_API_DOCS=1`；`web/run_local.py` 会自动开启）

### 前端

```bash
cd web/frontend
npm install
npm run dev
```

开发服务器：`http://localhost:5173`（默认代理后端 `localhost:8180`）

### 生产构建

```bash
cd web/frontend
npm run build       # → dist/
npm run check:build # 校验 PWA 预缓存与首屏 modulepreload
```

### 前端加载策略（避免首访拉全量）

- **PWA 预缓存只含应用外壳**：`index.html` + `assets/index-*.js` + 图标。
  `local-backend.zip`、`sql-wasm/`、`wasm-golden/` 不进预缓存。
- **懒加载 chunk 按需缓存**：页面/图表/编辑器 chunk 首次访问时由 `/assets/*` 的
  `CacheFirst` 运行时缓存保存，不在首访预取。
- **分包规则**：`echarts`/`zrender` 单独成 chunk；不要手动拆 `@xyflow`——
  否则 React 会被绑进该 chunk，入口被迫静态引用，首屏多下 300+ KB。
- `npm run check:build` 在 CI 中守住以上约束（`web-ci.yml` 的 build 之后执行）。

### 移动端适配

- **数值输入统一用 `components/common/NumberField.tsx`**，不要再用受控
  `<TextField type="number">` + `parseFloat(...) || 0`。后者在手机上清空后会立刻回填
  `0`、继续输入变成 `025`；`NumberField` 用 `type="text"` + `inputMode` 保留输入草稿，
  支持清空、小数中间态、全角数字，失焦时按 min/max 归一。
- 纯逻辑在 `src/utils/numericDraft.ts`（`sanitizeNumericDraft` / `parseNumericDraft` /
  `clampNumber` / `formatNumberDraft`），由 `npm test` 覆盖。
- `WebComputeSheet` 的输入/输出网格在 `xs` 下强制单列；滑块行旁通常配一个
  64~88px 的 `NumberField`，方便手机上直接键入等级/倍率。
- `index.html` 已声明 `viewport-fit=cover`；底部导航与主内容区用
  `env(safe-area-inset-bottom)` 避开 iPhone 手势条；≤600px 有专用骨架屏。

---

## API 概览

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/api/compute` | `compute.py` | DAG 求值/快照/配装对比 |
| `/api/search` | `search.py` | 全量搜索/预估/结果浏览 |
| `/api/data` | `data.py` | 角色/武器/装备 CRUD |
| `/api/admin` | `admin.py` | API Key 管理/速率限制/用量统计 |
| `/api/ai` | `ai.py` | AI 智能配装/语义搜索/对话 |
| `/api/adapters` | `adapters.py` | 适配器查询/注册 |
| `/api/layout` | `layout.py` | UI 布局定义 |
| `/api/hub` | `hub.py` | 配置包市场 |
| `/api/survival` | `survival.py` | 生存估算 |
| `/api/manual_buff` | `manual_buff.py` | 手动 Buff 微调 |
| `/api/arknights` | `arknights.py` | 明日方舟适配器 |
| `/api/generator` | `generator.py` | 适配器自动生成 |
| `/api/ocr` | `ocr.py` | OCR 截图识装 |
| `/api/pack` | `pack.py` | 配置包管理 |

---

## 部署

### 限速与 Worker 数

应用层限速（`RateLimitMiddleware`）为**进程内内存**实现，默认 **单 worker** 即可。仅 `/api/*` 计入限速与 usage，静态资源与前端路由不限速；匿名额度按客户端 IP 分桶。经 tunnel / 反向代理部署时用 `uvicorn ... --proxy-headers --forwarded-allow-ips 127.0.0.1` 取真实 IP。多 worker 时请设置 `CALC_DISABLE_RATE_LIMIT=1` 并在 nginx / 网关层限速。详见 [`docs/Web后端限速与多Worker.md`](../docs/Web后端限速与多Worker.md)。

CSRF 校验默认放行同源请求（Origin 与请求 `scheme://host` 一致）与 Vite 开发源；测试环境可用 `CALC_DISABLE_CSRF=1` 关闭。

### 安全响应头与 API 文档

后端对所有响应附加 CSP、`X-Content-Type-Options: nosniff`、`X-Frame-Options: DENY`、
`Referrer-Policy`、`Permissions-Policy` 与 HSTS（`web/backend/api/internal/security_headers.py`）。

- CSP 允许 `'wasm-unsafe-eval'`（sql.js / wasm-curve 实例化 WASM）与 `'unsafe-inline'` 样式
  （骨架屏 + MUI emotion 运行时注入），但禁止 `eval` 与第三方脚本。
- **API 文档默认关闭**：`/api/docs`、`/api/redoc`、`/openapi.json` 返回 404。
  `python web/run_local.py` 自动开启；手动启动时设置 `CALC_ENABLE_API_DOCS=1`
  （或 `CALC_DEBUG=1`）。开放文档时不附加 CSP，以兼容 Swagger UI 的 CDN 脚本。
- 生产构建不生成 source map（Vite 默认），不要把 `.map` 部署到 `dist/`。

### 请求体大小

默认 JSON API 请求体上限 **1 MiB**（`ContentSizeLimitMiddleware`）。上传路径放宽：`/api/ocr/` 5 MiB、`/api/hub/` 15 MiB。环境变量 `CALC_MAX_BODY_BYTES` / `CALC_DISABLE_BODY_LIMIT`。nginx 可配置 `client_max_body_size` 作为外层限制。

### 隐私与 AI 数据处理

AI 对话内容与 API Key 会经后端转发给用户配置的第三方服务；本项目不持久化 Key 与对话。数据流、保留期限与删除方式见 [`docs/隐私与AI数据处理.md`](../docs/隐私与AI数据处理.md)。

### PythonAnywhere（WSGI，已弃用）

项目已不再部署到 PythonAnywhere。当前由维护者本机 + ngrok 固定域名自托管：

```bash
python -m uvicorn main:app --app-dir web/backend --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips 127.0.0.1
ngrok http 8000
```

详见 [`docs/操作指令集.md`](../docs/操作指令集.md) §6 与 [`docs/Web后端限速与多Worker.md`](../docs/Web后端限速与多Worker.md)。

### Docker

```bash
docker compose up -d --build
```

运行数据（Hub 市场、API Key/用量、历史记录）保存在具名卷中；健康检查同时验证
状态目录可写与 `/api/health`。备份、恢复、升级与回滚见
[`docs/Docker部署与数据运维.md`](../docs/Docker部署与数据运维.md)。

### 本地打包（PyInstaller）

```bash
python web/build_local_backend.py
```

生成自包含 exe，无需 Python/Node 环境即可运行搜索服务器。
