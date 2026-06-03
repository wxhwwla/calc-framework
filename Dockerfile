# SPDX-License-Identifier: AGPL-3.0
# Docker 多阶段构建 — Web 前端 + FastAPI 后端
# 构建阶段：Node 18 编译前端
FROM node:18-alpine AS frontend-build
WORKDIR /app/web/frontend
COPY web/frontend/package*.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

# 运行阶段：Python 3.12 slim
FROM python:3.12-slim
WORKDIR /app

# 复制前端构建产物
COPY --from=frontend-build /app/web/frontend/dist /app/web/frontend/dist

# 复制后端代码
COPY web/backend/ /app/web/backend/

# 复制框架、游戏数据、工具、资源、工具库
COPY framework/ /app/framework/
COPY games/ /app/games/
COPY tools/ /app/tools/
COPY resources/ /app/resources/
COPY utils/ /app/utils/

# 复制依赖并安装
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# api.* 等本地模块通过 PYTHONPATH 可导入
ENV PYTHONPATH=/app/web/backend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
