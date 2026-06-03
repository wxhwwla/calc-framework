@echo off
chcp 65001 >nul
title 本地服务器 (已整合)

echo ========================================
echo   💡 启动本地服务器.bat 已整合到 启动.bat
echo.
echo   推荐直接使用：启动.bat 服务器
echo ========================================
echo.
echo   正在自动转发…
echo.
call "%~dp0启动.bat" 服务器
