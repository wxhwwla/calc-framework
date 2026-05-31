# PythonAnywhere 免费部署 FastAPI + React 前端完整指南

> 适用场景：在 PythonAnywhere 免费套餐上部署 FastAPI 后端 + React/Vue 前端，前后端同源服务。
> 不使用 Docker，纯手动配置，零花费。全流程已验证。

---

## 目录

1. [注册账号](#1-注册账号)
2. [准备项目代码](#2-准备项目代码)
3. [上传代码到 PythonAnywhere](#3-上传代码到-pythonanywhere)
4. [创建虚拟环境并安装 Python 依赖](#4-创建虚拟环境并安装-python-依赖)
5. [构建前端](#5-构建前端)
6. [创建 Web 应用](#6-创建-web-应用)
7. [配置 WSGI 文件（关键步骤）](#7-配置-wsgi-文件关键步骤)
8. [Reload 并验证](#8-reload-并验证)
9. [部署后更新代码](#9-部署后更新代码)
10. [附录：完整 WSGI 模板](#10-附录完整-wsgi-模板)

---

## 1. 注册账号

1. 打开 [pythonanywhere.com](https://www.pythonanywhere.com)
2. 点 **Pricing & Signup** → **Create a Beginner account**（免费套餐）
3. 注册时填用户名（例如 `yourname`），最终网址为 `https://yourname.pythonanywhere.com`
4. 注册后进入 Dashboard，记下你的用户名

---

## 2. 准备项目代码

在本地确保项目已推送到 GitHub。项目结构要求：

```
your-project/
├── backend/
│   ├── main.py              # FastAPI 应用入口，含 `app = FastAPI()`
│   ├── requirements.txt     # Python 依赖列表
│   ├── _path_setup.py       # （可选）sys.path 配置
│   └── api/                 # （可选）API 路由模块
├── frontend/
│   ├── package.json         # 含 build 脚本
│   ├── src/
│   └── vite.config.ts       # 开发时 proxy /api → 后端
└── ...（其他目录）
```

### 关键约定

| 项目 | 要求 |
|------|------|
| **后端入口** | `main.py` 中必须有 `app = FastAPI()` 的 `app` 变量 |
| **前端构建** | `package.json` 中有 `"build": "tsc -b && vite build"` 脚本 |
| **前端构建产物** | 输出到 `frontend/dist/` 目录 |
| **Python 依赖** | 写在 `requirements.txt` 中 |
| **自定义 Python 包** | 如果项目目录本身是可安装包，用 `pip install -e .` 安装 |

---

## 3. 上传代码到 PythonAnywhere

### 方式 A：git clone（推荐，方便后续更新）

在 PythonAnywhere 的 **Bash 控制台**（Dashboard → Consoles → Bash）中执行：

```bash
git clone https://github.com/你的用户名/你的仓库.git ~/your-project
```

### 方式 B：手动上传文件

Dashboard → **Files** → 导航到目标目录 → 点 **Upload a file** 逐个上传。

> 注：PythonAnywhere 免费套餐没有 Node.js，前端必须在本地构建后上传 zip 包。

---

## 4. 创建虚拟环境并安装 Python 依赖

在 Bash 中：

```bash
# 创建虚拟环境
mkvirtualenv your-project --python=/python3.12

# 激活虚拟环境
workon your-project

# 安装依赖
pip install -r ~/your-project/backend/requirements.txt

# 如果项目有自定义 Python 包（如 framework/）
pip install -e ~/your-project/framework/

# 安装 WSGI/ASGI 桥接库（关键！）
pip install a2wsgi
```

---

## 5. 构建前端

### 5.1 在本地构建

```powershell
cd your-project/frontend
npm install
npm run build
```

### 5.2 打包为 zip

```powershell
# PowerShell:
Compress-Archive -Path "dist\*" -DestinationPath "dist.zip" -Force

# 或者右键 dist/ 文件夹 → 发送到 → 压缩(zipped)文件夹
```

### 5.3 上传并解压

在 PythonAnywhere **Files** 页面上传到 `/home/yourname/your-project/frontend/`，然后在 Bash 中解压：

```bash
cd ~/your-project/frontend
rm -rf dist
unzip ~/your-project/frontend/dist.zip -d dist
rm ~/your-project/frontend/dist.zip
```

验证解压成功：

```bash
ls ~/your-project/frontend/dist/
# 应该看到 index.html, assets/ 等
```

> ⚠️ 注意：解压后检查是否有多余的嵌套目录（如 `dist/dist/index.html`），如果是则修正：
> ```bash
> cd ~/your-project/frontend/dist
> cp -r dist/* .
> rm -rf dist
> ```

---

## 6. 创建 Web 应用

1. 登录 PythonAnywhere → **Web** → **Add a new web app**
2. 点 **Manual configuration**
3. 选择 **Python 3.12** → **Next**
4. 创建后进入配置页面，填写：

| 字段 | 值 |
|------|-----|
| **Working directory** | `/home/yourname/your-project/backend` |
| **Python version** | 3.12 |
| **Virtualenv** | `/home/yourname/.virtualenvs/your-project` |

---

## 7. 配置 WSGI 文件（关键步骤）

FastAPI 是 ASGI 框架，但 PythonAnywhere 免费套餐只支持 WSGI 协议。需要用 `a2wsgi` 库做桥接。

### 在 Bash 中执行：

```bash
cat > /var/www/yourname_pythonanywhere_com_wsgi.py << 'WSGICODE'
import sys
import json
from pathlib import Path

# ===== 路径配置 =====
_BASE = Path("/home/yourname/your-project")
sys.path.insert(0, str(_BASE / "framework" / "src"))   # 自定义 Python 包路径
sys.path.insert(0, str(_BASE))
sys.path.insert(0, str(_BASE / "backend"))              # 后端 main.py 所在目录

# ===== 激活虚拟环境 =====
VENV_ACTIVATE = Path("/home/yourname/.virtualenvs/your-project/bin/activate_this.py")
if VENV_ACTIVATE.exists():
    exec(open(str(VENV_ACTIVATE)).read(), {"__file__": str(VENV_ACTIVATE)})

# ===== 加载 FastAPI 应用 =====
from a2wsgi import ASGIMiddleware
from main import app

_fastapi = ASGIMiddleware(app)
_DIST = _BASE / "frontend" / "dist"

# ===== WSGI 入口 =====
def application(environ, start_response):
    path = environ.get("PATH_INFO", "")

    # API 请求走 FastAPI
    if path.startswith("/api/"):
        return _fastapi(environ, start_response)

    # 静态文件（前端构建产物）
    if path == "/" or path == "":
        fp = _DIST / "index.html"
    else:
        fp = _DIST / path.lstrip("/")

    if fp.is_file():
        body = fp.read_bytes()
        ct = "text/html"
        if fp.suffix == ".js": ct = "application/javascript"
        elif fp.suffix == ".css": ct = "text/css"
        elif fp.suffix == ".svg": ct = "image/svg+xml"
        elif fp.suffix == ".json": ct = "application/json"
        start_response("200 OK", [("Content-Type", ct), ("Content-Length", str(len(body)))])
        return [body]

    # SPA 路由：没找到文件就返回 index.html
    fp = _DIST / "index.html"
    if fp.is_file():
        body = fp.read_bytes()
        start_response("200 OK", [("Content-Type", "text/html"), ("Content-Length", str(len(body)))])
        return [body]

    start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
    return [b"Not Found"]
WSGICODE
```

### 重要说明

| 部分 | 说明 |
|------|------|
| `sys.path` 配置 | 必须把 `backend/` 目录加到 path 中，否则 `from main import app` 会找到错误的文件 |
| `a2wsgi.ASGIMiddleware` | 将 FastAPI（ASGI）转换为 WSGI 可调用的对象 |
| `application` 函数 | 手动分发请求：`/api/*` 走 FastAPI，其他走静态文件 |
| SPA 路由 | React/Vue 的路由模式，非 API 路径返回 `index.html` |

---

## 8. Reload 并验证

1. 回到 PythonAnywhere **Web** 页面
2. 点绿色的 **Reload** 按钮
3. 访问 `https://yourname.pythonanywhere.com`

### 验证方式

| 测试 | 预期结果 |
|------|----------|
| 访问首页 `https://yourname.pythonanywhere.com/` | 显示前端页面 |
| 访问 API `https://yourname.pythonanywhere.com/api/health` | 返回 JSON |
| 访问静态文件 `https://yourname.pythonanywhere.com/assets/index-xxx.js` | 返回 JS 文件 |

---

## 9. 部署后更新代码

### 更新后端

```bash
# 在 Bash 中
cd ~/your-project
git pull

# 如果有新的 Python 依赖
workon your-project
pip install -r backend/requirements.txt

# 回到 Web 页面点 Reload
```

### 更新前端

```powershell
# 在本地
cd your-project/frontend
npm install
npm run build
Compress-Archive -Path "dist\*" -DestinationPath "dist.zip" -Force
```

上传 `dist.zip` 到 PythonAnywhere，然后：

```bash
cd ~/your-project/frontend
rm -rf dist
unzip ~/dist.zip -d dist
rm ~/dist.zip
# 回到 Web 页面点 Reload
```

---

## 10. 附录：完整 WSGI 模板

可直接复制使用的通用模板（将 `yourname` 和 `your-project` 替换为实际值）：

```python
import sys
import json
from pathlib import Path

# ===== 修改这两个变量 =====
YOUR_USERNAME = "yourname"
YOUR_PROJECT = "your-project"
# =========================

_BASE = Path(f"/home/{YOUR_USERNAME}/{YOUR_PROJECT}")

# 如果有自定义包目录（如 framework/src/），加在下面
CUSTOM_PACKAGE_PATHS = [
    _BASE / "framework" / "src",
]
for p in CUSTOM_PACKAGE_PATHS:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

sys.path.insert(0, str(_BASE))
sys.path.insert(0, str(_BASE / "backend"))

VENV_ACTIVATE = Path(f"/home/{YOUR_USERNAME}/.virtualenvs/{YOUR_PROJECT}/bin/activate_this.py")
if VENV_ACTIVATE.exists():
    exec(open(str(VENV_ACTIVATE)).read(), {"__file__": str(VENV_ACTIVATE)})

from a2wsgi import ASGIMiddleware
from main import app

_fastapi = ASGIMiddleware(app)
_DIST = _BASE / "frontend" / "dist"

_MIME_TYPES = {
    ".js": "application/javascript",
    ".css": "text/css",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".html": "text/html",
    ".json": "application/json",
    ".woff2": "font/woff2",
    ".webp": "image/webp",
}

def application(environ, start_response):
    path = environ.get("PATH_INFO", "")

    if path.startswith("/api/"):
        return _fastapi(environ, start_response)

    fp = _DIST / (path.lstrip("/") if path not in ("", "/") else "index.html")
    if not fp.is_file():
        fp = _DIST / "index.html"

    if fp.is_file():
        body = fp.read_bytes()
        ct = _MIME_TYPES.get(fp.suffix, "application/octet-stream")
        start_response("200 OK", [("Content-Type", ct), ("Content-Length", str(len(body)))])
        return [body]

    start_response("404 NOT FOUND", [("Content-Type", "text/plain")])
    return [b"Not Found"]
```

---

## 常见问题

### Q: Reload 后还是旧代码？
A: 浏览器缓存问题，按 `Ctrl+F5` 强制刷新。

### Q: 错误日志在哪看？
A: PythonAnywhere Web 页面 → **Logs** → **Error log**。

### Q: `ImportError: cannot import name 'app' from 'main'`
A: WSGI 文件中 `sys.path.insert(0, str(_BASE / "backend"))` 路径不正确，或者 `backend/` 下没有 `main.py`。

### Q: `TypeError: FastAPI.__call__() missing 1 required positional argument: 'send'`
A: 没有使用 `ASGIMiddleware` 包装，直接 `from main import app; application = app` 会报此错。必须用 `a2wsgi.ASGIMiddleware` 桥接。

### Q: 页面转圈但 HTML 能加载
A: 前端 JS 发起的 API 请求卡住了。先在浏览器访问 `/api/health` 测试，如果也转圈，说明 `a2wsgi` 的 async 处理有问题。在 WSGI 文件中用同步方式直接处理 `/api/health` 可以绕过。

### Q: 前端显示 "Not Found"
A: `frontend/dist/` 目录不存在或文件不完整。检查 `ls ~/your-project/frontend/dist/` 是否有 `index.html` 和 `assets/` 目录。

### Q: PythonAnywhere 显示 "Your webapp took a long time to reload"
A: 这是正常提示，实际可能已生效。刷新页面或稍等几秒再试。
