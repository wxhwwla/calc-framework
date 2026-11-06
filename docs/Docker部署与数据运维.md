# Docker 部署与数据运维

> 适用对象：使用 `docker-compose.yml` 部署 Web 服务的维护者。
> 相关文件：[`Dockerfile`](../Dockerfile)、[`docker-compose.yml`](../docker-compose.yml)、[`web/backend/healthcheck.py`](../web/backend/healthcheck.py)。

---

## 1. 状态目录清单

容器重建不会丢失以下具名卷中的数据：

| 卷 | 容器内路径 | 内容 | 性质 |
|----|-----------|------|------|
| `calc_hub_data` | `/app/web/backend/data/hub` | `catalog.db`、`packs/`（配置包市场） | **权威数据**，丢失不可重建 |
| `calc_admin_data` | `/app/web/backend/.data` | `.data/admin/api_keys.json`、`usage.json`、`.data/staging/`（贡献暂存） | **权威数据**，丢失后 API Key 与用量不可恢复 |
| `calc_api_data` | `/app/web/backend/api/data` | 用户历史、搜索历史 JSON | 可重建，但保留可避免丢失用户记录 |

说明：

- `docker compose down` 会删除容器但**保留具名卷**；`docker compose down -v` 会**连同卷一起删除**，除非确认要清空数据，否则不要加 `-v`。
- 容器内其他目录（镜像层）在重建时恢复为构建内容；运行时写入镜像层的文件会丢失，因此新增持久化目录时必须同步加入 `docker-compose.yml` 卷列表。
- 明日方舟干员数据默认只读挂载（`docker-compose.yml` 中已注释的 `parsed` 卷），不属于运行时状态。

---

## 2. 健康检查

`Dockerfile` 已声明 `HEALTHCHECK`，调用 `web/backend/healthcheck.py`：

1. 对三个状态目录逐个执行写入-删除探针，发现**只读卷、权限错误、磁盘写满**；
2. 请求 `http://127.0.0.1:8000/api/health`，确认进程可响应。

```bash
# 查看健康状态
docker compose ps

# 查看最近一次检查详情（含输出）
docker inspect --format '{{json .State.Health}}' "$(docker compose ps -q web)"
```

`/api/health` 只证明进程存活；健康检查额外证明**存储可写**。

---

## 3. 启动与停止

```bash
docker compose up --build -d     # 构建并后台启动
docker compose logs -f web       # 查看日志
docker compose stop web          # 停止但保留容器与卷
docker compose down              # 删除容器，保留卷
```

管理接口需要 `CALC_ADMIN_TOKEN`（未设置时管理写接口返回 503）。启用 SaaS API Key 时还需要 `CALC_API_KEY_PEPPER`（**≥32 字符**，缺失或过短会导致 Key 哈希请求报错）：

```bash
# .env（与 docker-compose.yml 同目录，勿提交）
CALC_ADMIN_TOKEN=change-me-to-a-long-random-value
CALC_API_KEY_PEPPER=another-long-random-value-at-least-32-chars
```

---

## 4. 备份

```bash
# 备份三个状态卷到单个 tar.gz（在宿主机执行）
docker compose exec -T web tar czf - -C /app/web/backend data/hub .data api/data \
  > "calcweb-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
```

建议在升级前与每日定时任务中各备份一次，并把备份文件复制到另一台机器。

---

## 5. 恢复到干净环境

```bash
# 1. 停止应用，避免恢复期间写入
docker compose stop web

# 2. 用同一 compose 文件挂载卷，把备份内容写回容器
docker compose run --rm --no-deps -T --entrypoint sh web \
  -c "tar xzf - -C /app/web/backend" < calcweb-backup-YYYYMMDD-HHMMSS.tar.gz

# 3. 启动并确认健康
docker compose up -d web
docker compose ps
```

恢复后验证：

```bash
# 市场数据可读
curl -s http://localhost:8000/api/hub/packs | head -c 200

# 管理接口可读（需要 Token）
curl -s -H "X-Admin-Token: $CALC_ADMIN_TOKEN" http://localhost:8000/api/admin/keys
```

---

## 6. 升级

1. 按第 4 节备份。
2. 拉取新代码并构建（先在旧镜像上打标签，便于回滚）：

   ```bash
   docker tag "$(docker compose images -q web)" calc-web:before-upgrade
   docker compose build --pull
   docker compose up -d
   ```

3. 确认 `docker compose ps` 为 `healthy`，并完成一次真实计算与市场读取。
4. 确认新版本稳定后再删除旧镜像。

---

## 7. 回滚

```bash
# 方式 A：用升级前的镜像标签
docker tag calc-web:before-upgrade "$(docker compose images -q web)"
docker compose up -d

# 方式 B：切回旧提交并重建
git checkout <上一个可用提交>
docker compose build
docker compose up -d
```

卷不会随回滚改变，数据保持升级后的状态；如果新版本改过数据结构，回滚前先用第 4 节备份。

---

## 8. 故障排查

| 现象 | 排查 |
|------|------|
| `docker compose ps` 显示 `unhealthy` | 查看 `docker inspect` 的健康输出；多为状态卷权限或磁盘写满 |
| 健康检查通过但管理接口 503 | 未设置 `CALC_ADMIN_TOKEN` |
| 重建后市场/API Key 丢失 | 确认使用 `docker compose down`（不带 `-v`），且卷仍存在（`docker volume ls`） |
| 容器内写入报 `Read-only file system` | 检查卷挂载是否改为 `:ro`，或宿主机磁盘/权限 |
| 健康检查探针残留 `.healthcheck` | 正常情况会被删除；若残留说明删除阶段失败，检查卷权限 |
