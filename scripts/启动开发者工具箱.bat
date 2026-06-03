@echo off
chcp 65001 >nul
title 开发者工具箱 (已整合)

echo ========================================
echo   💡 启动开发者工具箱.bat 已整合到 启动.bat
echo.
echo   推荐直接使用：启动.bat 工具箱
echo ========================================
echo.
echo   正在自动转发…
echo.
call "%~dp0启动.bat" 工具箱
