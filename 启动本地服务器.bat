@echo off
chcp 65001 >nul
title 终末地伤害计算器 - 本地服务器

echo ========================================
echo   终末地伤害计算器 - 本地服务器
echo   双击启动，浏览器自动打开
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

:: 检查 Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到 Node.js
    echo    请先安装 Node.js 18+
    echo    下载地址：https://nodejs.org/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version 2^>^&1') do echo [OK] Node.js %%i

:: 启动本地服务器
echo.
echo [启动中] 正在启动本地服务器...
echo   浏览器窗口将自动打开
echo   关闭此窗口即可停止服务器
echo.
echo ========================================
echo.
call python web/run_local.py

if %errorlevel% neq 0 (
    echo.
    echo [!] 服务器启动失败，请检查上方错误信息
    pause
)
