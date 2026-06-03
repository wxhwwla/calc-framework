@echo off
chcp 65001 >nul
title 开发者工具箱

echo ========================================
echo   开发者工具箱
echo   数据设计 / 布局编辑 / 图编辑器 / 调试器
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 Python
    echo    请先安装 Python 3.10+
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo [OK] %%i

:: 设置 PYTHONPATH
set PYTHONPATH=%CD%\framework\src;%CD%;%CD%\tools;%CD%\games\endfield

:: 启动开发者工具箱
echo.
echo [启动中] 正在打开开发者工具箱...
echo.
python scripts/main_dev_toolkit.py

if %errorlevel% neq 0 (
    echo.
    echo [!] 启动失败，请检查上方错误信息
    pause
)
pause
