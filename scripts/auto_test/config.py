# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0
"""
自动化测试配置

所有路径、超时、参数集中管理。
"""

from __future__ import annotations

from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 路径配置
# ──────────────────────────────────────────────────────────────

# 项目根目录
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Web 前端目录
WEB_FRONTEND_DIR = REPO_ROOT / "web" / "frontend"

# 桌面应用入口
DESKTOP_ENTRY = REPO_ROOT / "games" / "endfield" / "main.py"

# 打包脚本
BUILD_SCRIPT = REPO_ROOT / "scripts" / "main_build.py"

# 打包输出目录
DIST_DIR = REPO_ROOT / "dist"

# 截图输出目录
SCREENSHOT_DIR = Path(__file__).resolve().parent / "screenshots"
SCREENSHOT_WEB_DIR = SCREENSHOT_DIR / "web"
SCREENSHOT_DESKTOP_DIR = SCREENSHOT_DIR / "desktop"
SCREENSHOT_PACKAGED_DIR = SCREENSHOT_DIR / "packaged"

# ──────────────────────────────────────────────────────────────
# 超时配置（秒）
# ──────────────────────────────────────────────────────────────

# 应用启动等待时间
APP_STARTUP_TIMEOUT = 10

# 页面加载等待时间
PAGE_LOAD_TIMEOUT = 5

# 操作间隔（避免操作过快）
ACTION_DELAY = 0.5

# 测试单步超时
STEP_TIMEOUT = 30

# 打包超时
BUILD_TIMEOUT = 600  # 10 分钟

# ──────────────────────────────────────────────────────────────
# Web 测试配置
# ──────────────────────────────────────────────────────────────

# Vite dev server 端口
VITE_PORT = 5173

# Cypress 配置
CYPRESS_CONFIG = WEB_FRONTEND_DIR / "cypress.config.ts"

# ──────────────────────────────────────────────────────────────
# 桌面应用配置
# ──────────────────────────────────────────────────────────────

# 应用窗口标题（用于查找窗口）
APP_WINDOW_TITLE = "终末地伤害计算器"

# 应用类名（Qt 窗口类名）
APP_CLASS_NAME = "EndfieldApp"

# 打包后 exe 名称
PACKAGED_EXE_NAME = "终末地伤害计算器.exe"

# ──────────────────────────────────────────────────────────────
# 测试场景配置
# ──────────────────────────────────────────────────────────────

# 要测试的页面/功能列表
TEST_SCENARIOS = {
    "desktop": [
        {
            "name": "启动检查",
            "description": "检查应用能否正常启动",
            "steps": ["启动应用", "等待主窗口", "截图"],
        },
        {
            "name": "计算页功能",
            "description": "检查计算页基本功能",
            "steps": [
                "切换到计算页",
                "选择角色",
                "选择武器",
                "点击确认",
                "检查属性展示",
                "截图",
            ],
        },
        {
            "name": "高级页功能",
            "description": "检查高级页基本功能",
            "steps": [
                "切换到高级页",
                "检查搜索面板",
                "检查多技能面板",
                "截图",
            ],
        },
        {
            "name": "数据设计器",
            "description": "检查数据设计器功能",
            "steps": [
                "打开设计器",
                "检查数据浏览",
                "检查公式反推",
                "截图",
            ],
        },
    ],
    "packaged": [
        {
            "name": "exe 启动检查",
            "description": "检查打包后 exe 能否正常启动",
            "steps": ["启动 exe", "等待主窗口", "截图"],
        },
        {
            "name": "exe 功能完整性",
            "description": "检查打包后功能是否完整",
            "steps": [
                "切换计算页",
                "切换高级页",
                "检查基本功能",
                "截图",
            ],
        },
    ],
}


def ensure_dirs() -> None:
    """创建所有必要的目录。"""
    for d in [
        SCREENSHOT_DIR,
        SCREENSHOT_WEB_DIR,
        SCREENSHOT_DESKTOP_DIR,
        SCREENSHOT_PACKAGED_DIR,
    ]:
        d.mkdir(parents=True, exist_ok=True)
