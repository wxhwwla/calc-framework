# Web 后端限速与多 Worker 部署说明

> **关联缺陷**：H8（进程内 `defaultdict` 限速）、M23（Redis 限速未实现）。  
> **代码位置**：`web/backend/api/admin.py` → `RateLimitMiddleware`。

---

## 1. 当前实现（单进程内存）

| 组件 | 存储 | 作用域 |
|------|------|--------|
| 滑动窗口计数 | `RateLimitMiddleware._window`（内存） | **当前 worker 进程**；按 API Key 或客户端 IP 分桶，仅 `/api/*` 计数 |
| API Key 元数据 | `.data/admin/api_keys.json` | 磁盘（多 worker 并发写可能竞态） |
| 用量统计 | `.data/admin/usage.json` | 磁盘（多 worker 各自累加，统计不完整） |

**tier 默认限额**（每分钟）：

| tier | 限额 |
|------|------|
| 无 Key / 匿名 | 20（按客户端 IP 分桶） |
| free | 30 |
| pro | 300 |
| enterprise | 3000 |

请求头：`X-API-Key`（客户端） / 管理写操作另需 `X-Admin-Token`（见 [`PythonAnywhere-部署指南.md`](PythonAnywhere-部署指南.md) §11.3）。

---

## 2. 推荐部署模式

### 2.1 单 worker（默认推荐）

适用于反向代理 / tunnel、Docker 默认 CMD、本地 `uvicorn main:app`：

```bash
# 仓库根目录执行（web/backend/main.py 以 `api.*` 顶层包导入，必须让 web/backend 在 sys.path）
python -m uvicorn main:app --app-dir web/backend --host 127.0.0.1 --port 8000 \
  --proxy-headers --forwarded-allow-ips 127.0.0.1
# 等价：cd web/backend && uvicorn main:app --host 127.0.0.1 --port 8000 \
#   --proxy-headers --forwarded-allow-ips 127.0.0.1
# 无反向代理/tunnel、需要直接对外时才用 --host 0.0.0.0
# 注意：uvicorn web.backend.main:app 形式会因找不到 api 包而启动失败
```

- 内存限速与 usage 统计行为与代码设计一致。
- **仅 `/api` 与 `/api/*` 参与限速和 usage**；`/`、`/assets/*`、前端路由等静态请求不计入（否则 SPA 首屏 20+ 个 chunk 会直接耗尽额度并白屏）。
- **匿名额度按客户端 IP 分桶**（`anon:<client.host>`）。本机 ngrok / cloudflared 都从 `127.0.0.1` 连入，`--proxy-headers --forwarded-allow-ips 127.0.0.1` 让 uvicorn 信任其 `X-Forwarded-For`；不加时所有访客会被视为同一个 IP，共享 20 次/分钟。
- 无需额外环境变量。

### 2.2 多 worker + 反向代理限速

若必须使用 `uvicorn --workers N` 或 gunicorn 多 worker：

1. **禁用应用层限速**（避免每进程独立计数导致限额放大 N 倍）：

   ```bash
   export CALC_DISABLE_RATE_LIMIT=1
   ```

2. **在反向代理层统一限速**，例如 nginx：

   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

   location /api/ {
       limit_req zone=api burst=10 nodelay;
       proxy_pass http://127.0.0.1:8000;
   }
   ```

3. **用量统计**：当前 `.data/admin/usage.json` 在多 worker 下仅为近似值；精确统计需外部存储（Redis / 日志聚合），尚未实现。

### 2.3 生产环境变量速查

| 变量 | 说明 |
|------|------|
| `CALC_DISABLE_RATE_LIMIT` | `1` / `true` 时关闭 `RateLimitMiddleware` |
| `WEB_CONCURRENCY` / `UVICORN_WORKERS` / `CALC_WEB_WORKERS` | >1 时启动日志会警告（见 `main.py`） |
| `CALC_ADMIN_TOKEN` | 管理 API 与 data 写操作 |
| `CALC_API_KEY_PEPPER` | API Key scrypt pepper（生产必配） |

---

## 3. 测试与开发

```python
# 单元/集成测试中全局关闭限速
from api.admin import RateLimitMiddleware
RateLimitMiddleware.enabled = False
```

---

## 4. 未来扩展（未实现）

- Redis 滑动窗口 + 集中式 usage（替代进程内 `_window` 与 JSON 文件）
- 按 `X-API-Key` 在边缘/CDN 限速

---

*最后更新：2026-11-05（自托管：仅 `/api/*` 限速、匿名按 IP 分桶、tunnel 代理头）*
