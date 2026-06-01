#!/bin/bash
# 终末地伤害计算器 — PythonAnywhere 服务器端部署脚本
#
# 在 PythonAnywhere Bash 控制台中执行:
#   cd ~/calc-framework
#   bash web/scripts/deploy_server.sh
#
# 前提条件:
#   1. ~/dist.zip 已通过本地脚本或 Files 页面上传
#   2. git remote 已配置 SSH 方式（推荐）或 HTTPS + token
#
# 使用方法:
#   bash deploy_server.sh             标准部署（git pull + pip + unzip）
#   bash deploy_server.sh --no-pull   跳过 git pull（仅 pip + unzip）
#   bash deploy_server.sh --no-pip    跳过 pip install（仅 git pull + unzip）
#   bash deploy_server.sh --zip path  指定 zip 文件路径

set -e

PROJECT="calc-framework"
ZIP_PATH=""
DO_PULL=true
DO_PIP=true

# 解析参数
for arg in "$@"; do
    case "$arg" in
        --no-pull) DO_PULL=false ;;
        --no-pip)  DO_PIP=false  ;;
        --zip=*)   ZIP_PATH="${arg#--zip=}" ;;
        --help)
            echo "用法: bash $0 [--no-pull] [--no-pip] [--zip=路径]"
            echo ""
            echo "  --no-pull    跳过 git pull"
            echo "  --no-pip     跳过 pip install"
            echo "  --zip=路径   指定 zip 文件路径（默认自动查找）"
            exit 0
            ;;
    esac
done

echo "========================================"
echo "终末地伤害计算器 — PythonAnywhere 部署"
echo "========================================"

# 1/4: 拉取最新代码
if [ "$DO_PULL" = true ]; then
    echo ""
    echo "=== 1/4: 拉取最新代码 ==="
    cd ~/$PROJECT
    git pull
    echo "  ✅ git pull 完成"
else
    echo ""
    echo "=== 1/4: 跳过 git pull ==="
fi

# 2/4: 安装 Python 依赖
if [ "$DO_PIP" = true ]; then
    echo ""
    echo "=== 2/4: 安装 Python 依赖 ==="
    source ~/.virtualenvs/calc-framework/bin/activate
    pip install -q -r web/backend/requirements.txt
    pip install -q -e framework/
    pip install -q python-multipart a2wsgi
    echo "  ✅ Python 依赖安装完成"
else
    echo ""
    echo "=== 2/4: 跳过 pip install ==="
fi

# 3/4: 解压前端构建产物
echo ""
echo "=== 3/4: 解压前端构建产物 ==="
cd ~/$PROJECT/web/frontend

# 确定 zip 路径
if [ -z "$ZIP_PATH" ]; then
    # 自动查找
    if [ -f ~/dist.zip ]; then
        ZIP_PATH=~/dist.zip
    elif [ -f ~/$PROJECT/frontend/dist.zip ]; then
        ZIP_PATH=~/$PROJECT/frontend/dist.zip
    elif [ -f dist.zip ]; then
        ZIP_PATH=dist.zip
    else
        echo "  ❌ 未找到 dist.zip！"
        echo "  请先通过本地脚本或 Files 页面上传 dist.zip"
        exit 1
    fi
fi

echo "  使用: $ZIP_PATH"

# 删除旧 dist/，创建新目录
rm -rf dist
mkdir -p dist
cd dist

# 解压（确保不产生 dist/dist/ 嵌套）
unzip -q "$ZIP_PATH"
echo "  ✅ 解压完成"

# 检查是否有嵌套的 dist/ 目录
if [ -d dist ]; then
    echo "  ⚠ 检测到 dist/dist/ 嵌套，正在修复..."
    cp -r dist/* .
    rm -rf dist
    echo "  ✅ 嵌套已修复"
fi

cd ..
echo "  目录结构:"
ls -la dist/
echo "  JS 文件:"
ls -lh dist/assets/*.js 2>/dev/null || echo "  (无 assets 目录)"

# 4/4: 清理临时文件
echo ""
echo "=== 4/4: 清理临时文件 ==="
rm -f "$ZIP_PATH"
echo "  ✅ 临时文件已清理"

echo ""
echo "========================================"
echo "✅ 服务器端部署完成！"
echo "========================================"
echo ""
echo "下一步:"
echo "  1) 更新 WSGI（首次或报错 missing 'send' 时必做）:"
echo "     cp ~/$PROJECT/web/wsgi_pythonanywhere.py /var/www/\${USER}_pythonanywhere_com_wsgi.py"
echo "  2) 请在 PythonAnywhere Web 页面点击 Reload"
echo "  或从本地执行: python web/scripts/deploy_pythonanywhere.py --reload"
echo ""
