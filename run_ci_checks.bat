@echo off
REM 在推送前本地运行 CI 核心检查
REM 用法：.\run_ci_checks.bat

echo ===== 1. ruff lint (Python) =====
python -m ruff check games/endfield/ framework/src/ web/backend/ scripts/ tools/ || exit /b 1

echo ===== 2. Web 后端测试 =====
python -m pytest web/backend/tests/ -q --tb=short || exit /b 1

echo ===== 3. Web 前端 TypeScript =====
cd web\frontend
call npx tsc --noEmit || exit /b 1

echo ===== 4. Web 前端 ESLint =====
call npx eslint "src/**/*.{ts,tsx}" --max-warnings 50 || exit /b 1

echo ===== 5. Web 前端构建 =====
call npx vite build || exit /b 1
cd ..

echo ===== 6. 框架核心测试 =====
cd framework
python -m pytest tests/ -q --tb=short || exit /b 1
cd ..

echo ===== 所有 CI 检查通过 =====
