# SPDX-License-Identifier: AGPL-3.0
# Docker 多阶段构建 — Web 前端 + FastAPI 后端
#
# Phase 3 Step 3.5：非 root 运行 + slim 复制（仅 Web 运行面，见 .dockerignore）
#
# 构建：docker compose build
# 运行：docker compose up -d  → http://localhost:8000

# ── Stage 1：前端静态资源 ─────────────────────────────────────────────
FROM node:18-alpine AS frontend-build
WORKDIR /app/web/frontend
COPY web/frontend/package*.json ./
RUN npm ci
COPY web/frontend/ ./
RUN npm run build

# ── Stage 2：Python 运行时 ────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# 非 root 用户（M3）
RUN groupadd --gid 10001 calcweb \
    && useradd --uid 10001 --gid 10001 --home-dir /app --shell /usr/sbin/nologin calcweb

COPY --from=frontend-build /app/web/frontend/dist /app/web/frontend/dist

# Web 后端
COPY web/backend/ /app/web/backend/

# 框架核心 + 适配器包
COPY framework/src/ /app/framework/src/
COPY framework/adapters/ /app/framework/adapters/

# 终末地 Web 运行面（calc / 数据 / GUI 桥接，不含 tests）
COPY games/__init__.py /app/games/
COPY games/endfield/__init__.py games/endfield/framework_bridge.py /app/games/endfield/
COPY games/endfield/calc/ /app/games/endfield/calc/
COPY games/endfield/data/ /app/games/endfield/data/
COPY games/endfield/data_loading/ /app/games/endfield/data_loading/
COPY games/endfield/gui/ /app/games/endfield/gui/

# 明日方舟 Web 面（operators.json 可选，见下方 mkdir + volume）
COPY games/arknights/ /app/games/arknights/

# 计算器生成器 API
COPY tools/__init__.py /app/tools/
COPY tools/generator/ /app/tools/generator/

COPY utils/ /app/utils/
COPY resources/ /app/resources/

COPY requirements-web.txt requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 运行时 writable 目录 + 可选明日方舟数据挂载点
RUN mkdir -p \
    /app/web/backend/api/data \
    /app/web/backend/api/.admin_data \
    /app/web/backend/api/packaging/.staging \
    /app/web/backend/data/hub/packs \
    /app/tools/arknights_scout/output/parsed \
    && chown -R calcweb:calcweb /app

ENV PYTHONPATH=/app/web/backend
ENV HOME=/app

EXPOSE 8000

USER calcweb

CMD ["python", "-m", "uvicorn", "web.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
