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

API 文档：启动后访问 `http://localhost:8180/api/docs`

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
```

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

应用层限速（`RateLimitMiddleware`）为**进程内内存**实现，默认 **单 worker** 即可。多 worker 时请设置 `CALC_DISABLE_RATE_LIMIT=1` 并在 nginx / 网关层限速。详见 [`docs/Web后端限速与多Worker.md`](../docs/Web后端限速与多Worker.md)。

### 请求体大小

默认 JSON API 请求体上限 **1 MiB**（`ContentSizeLimitMiddleware`）。上传路径放宽：`/api/ocr/` 5 MiB、`/api/hub/` 15 MiB。环境变量 `CALC_MAX_BODY_BYTES` / `CALC_DISABLE_BODY_LIMIT`。nginx 可配置 `client_max_body_size` 作为外层限制。

### PythonAnywhere（WSGI）

```bash
python web/scripts/deploy_pythonanywhere.py --all
```

详见 [`docs/操作指令集.md`](../docs/操作指令集.md)。

### Docker

```bash
docker compose up
```

### 本地打包（PyInstaller）

```bash
python web/build_local_backend.py
```

生成自包含 exe，无需 Python/Node 环境即可运行搜索服务器。
