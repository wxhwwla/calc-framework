# 隐私与 AI 数据处理

> 适用对象：使用 Web 版（含 Docker / 自托管 / 反向代理部署）的访客与部署者。
> 相关代码：[`web/backend/api/ai.py`](../web/backend/api/ai.py)、[`web/backend/api/admin.py`](../web/backend/api/admin.py)、[`web/frontend/src/components/calculator/AiRecommendDialog.tsx`](../web/frontend/src/components/calculator/AiRecommendDialog.tsx)。

## 1. AI 功能的数据流

「AI 配装助手」在填写 API Key 后会调用**用户自己配置的 OpenAI 兼容服务**（默认 `https://api.openai.com/v1`，模型 `gpt-4o-mini`）：

| 发送内容 | 说明 |
|----------|------|
| 用户查询 / 对话历史 | 最近 10 条消息，用于多轮对话与意图理解 |
| 角色名、当前武器名 | 用于生成推荐上下文 |
| 系统提示词 | 固定文本，不含用户数据 |
| API Key | 通过 `Authorization: Bearer` 头随请求发送 |

数据先到**本项目的 Web 后端**，再由后端转发给上述第三方服务；第三方如何存储和处理，取决于该服务自己的隐私政策，本项目无法控制。

**未填写 API Key 时**：推荐与搜索只在本地完成（本地 DAG 求值 / 关键词匹配），不会向任何外部服务发送数据。

## 2. 本项目保存什么

| 数据 | 位置 | 保留策略 |
|------|------|----------|
| 用户填写的 AI API Key | 仅当前浏览器页面内存（React state） | 刷新或关闭页面即清空；不写入 localStorage，不写入后端磁盘 |
| 对话内容、提示词 | 仅当前请求内存 | 请求结束即丢弃，不持久化 |
| 应用日志 | 标准错误 / 容器日志 | 只记录异常摘要；不记录 API Key、`Authorization` 头或对话内容 |
| 鉴权失败记录 | 后端进程内存 | 按 IP 记录，60 秒窗口后自动清理 |
| 用量统计 | `.data/admin/usage.json` | 最近 1 小时的请求时间戳 + 按端点累计计数（不含请求内容） |
| 管理端发放的 SaaS API Key | `.data/admin/api_keys.json` | 只保存 scrypt 哈希与前缀，不保存明文 |
| 用户主动保存的计算历史 | `web/backend/api/data/` | 由用户自行保存与删除；Docker 部署下位于 `calc_api_data` 卷 |

## 3. 保留期限与删除方式

- **自动清理**：IP 锁定 60 秒后失效；用量时间戳只保留最近 1 小时。
- **吊销 Key**：管理员调用 `DELETE /api/admin/keys/{key_prefix}`（需 `X-Admin-Token`）。
- **清空用量**：删除 `web/backend/.data/admin/usage.json`。
- **清空历史**：删除 `web/backend/api/data/` 下对应 JSON 文件。
- **Docker**：数据在具名卷中；`docker compose down -v` 会删除全部状态（不可恢复，慎用）。备份与恢复见 [`Docker部署与数据运维.md`](Docker部署与数据运维.md)。

## 4. 给访客的建议

- 不要在公共或不可信的部署中填入生产环境 API Key；建议使用限额、可随时吊销的 Key。
- 第三方接收者由你填写的 API Base 决定，请确认其可信度。
- 本项目为开源软件：**自托管部署者即为数据处理者**，需自行向访客披露并承担合规责任。

## 5. 给部署者的检查清单

- [ ] 通过 HTTPS 提供服务，避免 Key 在传输中泄露。
- [ ] 不把 `.env`、日志、备份文件提交到仓库或公开目录。
- [ ] 定期轮换 `CALC_ADMIN_TOKEN` 与 `CALC_API_KEY_PEPPER`。
- [ ] 在站点显著位置链接本页。
