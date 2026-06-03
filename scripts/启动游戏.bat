@echo off
chcp 65001 >nul
title 游戏计算器 - 启动器

echo ========================================
echo   游戏计算器 — 启动器
echo   选择游戏 → 启动桌面版计算器
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 Python
    echo    请先安装 Python 3.10+
    echo    下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] %%i

:: 设置 PYTHONPATH
set PYTHONPATH=%CD%\framework\src;%CD%;%CD%\tools;%CD%\games\endfield

:: 启动启动器
echo.
echo [启动中] 正在打开启动器窗口...
echo.
python scripts/main_launcher.py

if %errorlevel% neq 0 (
    echo.
    echo [!] 启动失败，请检查上方错误信息
    pause
)
pause
