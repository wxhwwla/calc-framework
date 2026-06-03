@echo off
chcp 65001 >nul
title 游戏计算器 — 统一启动器

setlocal enabledelayedexpansion

:: ========================================
::   游戏计算器 — 统一启动器
::   用法：
::     启动.bat               — 显示菜单
::     启动.bat 游戏          — 直接打开游戏启动器
::     启动.bat 工具箱        — 直接打开开发者工具箱
::     启动.bat 服务器        — 直接启动本地 Web 服务器
:: ========================================

:: --- 检查 Python ---
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

:: --- 检查参数，决定启动模式 ---
set MODE=%1
if /i "%MODE%"=="游戏" goto :launch_launcher
if /i "%MODE%"=="工具箱" goto :launch_toolkit
if /i "%MODE%"=="服务器" goto :launch_server
if /i "%MODE%"=="launcher" goto :launch_launcher
if /i "%MODE%"=="toolkit" goto :launch_toolkit
if /i "%MODE%"=="server" goto :launch_server

:: --- 无参数：显示菜单 ---
:menu
cls
echo ========================================
echo   游戏计算器 — 统一启动器
echo ========================================
echo.
echo   1. 游戏启动器（选择游戏 → 桌面版计算器）
echo   2. 开发者工具箱（数据设计/图编辑/调试/AI生成）
echo   3. 本地 Web 服务器（浏览器中使用）
echo   4. 退出
echo.
set /p CHOICE="请选择 [1-4]："

if "%CHOICE%"=="1" goto :launch_launcher
if "%CHOICE%"=="2" goto :launch_toolkit
if "%CHOICE%"=="3" goto :launch_server
if "%CHOICE%"=="4" goto :eof
echo 无效输入，请重新选择。
timeout /t 2 >nul
goto :menu

:: --- 模式 1：游戏启动器 ---
:launch_launcher
echo.
echo [启动中] 正在打开游戏启动器...
echo.
set PYTHONPATH=%CD%\framework\src;%CD%;%CD%\tools;%CD%\games\endfield
python scripts/main_launcher.py
if %errorlevel% neq 0 (
    echo [!] 启动失败，请检查上方错误信息
    pause
)
goto :eof

:: --- 模式 2：开发者工具箱 ---
:launch_toolkit
echo.
echo [启动中] 正在打开开发者工具箱...
echo.
set PYTHONPATH=%CD%\framework\src;%CD%;%CD%\tools;%CD%\games\endfield
python scripts/main_dev_toolkit.py
if %errorlevel% neq 0 (
    echo [!] 启动失败，请检查上方错误信息
    pause
)
goto :eof

:: --- 模式 3：本地 Web 服务器 ---
:launch_server
echo.
echo [启动中] 正在启动本地 Web 服务器...
echo   浏览器窗口将自动打开
echo.
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
echo.
python web\run_local.py
if %errorlevel% neq 0 (
    echo [!] 服务器启动失败，请检查上方错误信息
    pause
)
goto :eof
