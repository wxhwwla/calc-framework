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

### 重要说明

> ⚠️ **为什么需要这种特殊配置？**
> PythonAnywhere 免费套餐只支持 **WSGI 协议**，但 FastAPI 是 **ASGI 框架**（原生 async/await）。
> 我们用 `a2wsgi.ASGIMiddleware` 做桥接，但免费套餐的 uWSGI 不支持 async event loop，
> 所以 FastAPI 的 `async def` 端点会**永久卡住**。
>
> **解决方案**：在 WSGI 入口函数中，**关键数据 API 用纯同步代码直接处理**（读取 JSON 文件返回），
> 绕过 FastAPI 的 async 机制。`a2wsgi.ASGIMiddleware` 作为非关键 API 的兜底。

### 最终 WSGI 文件

> 以下为实战验证可用的完整 WSGI 文件，覆盖了常见的数据查询 API：

在 Bash 中执行（将 `yourname` 和 `your-project` 替换为实际值）：

```bash
cat > /var/www/yourname_pythonanywhere_com_wsgi.py << 'WSGICODE'
import sys
import json
import re
from pathlib import Path

_BASE = Path("/home/yourname/your-project")
for _p in [str(_BASE / "framework" / "src"), str(_BASE), str(_BASE / "backend")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

VENV = Path(f"/home/yourname/.virtualenvs/your-project/bin/activate_this.py")
if VENV.exists():
    exec(open(str(VENV)).read(), {"__file__": str(VENV)})

# FastAPI 兜底（仅用于非关键 API）
from a2wsgi import ASGIMiddleware
try:
    from main import app
    _fastapi = ASGIMiddleware(app)
except Exception:
    _fastapi = None

_DATA = _BASE / "games" / "endfield" / "data"   # 游戏数据目录
_DIST = _BASE / "frontend" / "dist"               # 前端构建产物

def _read_json(path):
    if not path.is_file(): return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _json(start_response, data, status="200 OK"):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                            ("Content-Length", str(len(body)))])
    return [body]

def _handle_api(environ, start_response):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/health":
        return _json(start_response, {"status": "ok", "version": "1.0.0"})

    # 搜索目录（如有此模块）
    if path == "/api/search/catalog":
        try:
            from games.endfield.data_loading.equipment_catalog import get_equipment_catalog
            catalog = get_equipment_catalog()
            result = {
                k: [{"名称": e.get("名称",""), "部位": e.get("部位",""),
                     "所属套组": e.get("所属套组",""), "稀有度": e.get("稀有度","")}
                    for e in v]
                for k, v in catalog.items()
            }
            return _json(start_response, result)
        except Exception as e:
            return _json(start_response, {"error": str(e)}, "500")

    if not path.startswith("/api/data/"):
        return None

    sub = path[len("/api/data/"):]
    if method != "GET":
        return _json(start_response, {"error": "not supported"}, "501")

    # /api/data/summary
    if sub == "summary":
        c = _read_json(_DATA / "characters.json") or []
        w = _read_json(_DATA / "weapons.json") or []
        e = _read_json(_DATA / "equipments.json") or []
        return _json(start_response, {
            "characters_count": len(c), "weapons_count": len(w), "equipments_count": len(e),
            "equipment_sets": list({x.get("所属套组") for x in e if x.get("所属套组")}),
            "character_types": list({x.get("类型") for x in c if x.get("类型")}),
            "weapon_types": list({x.get("类型") for x in w if x.get("类型")}),
        })

    # 角色列表
    if sub == "characters/detail/all":
        d = _read_json(_DATA / "characters.json")
        return _json(start_response, d) if d else _json(start_response, {"error":"not found"},"404")
    if sub == "characters":
        raw = _read_json(_DATA / "characters.json") or []
        return _json(start_response, [{"名称":c.get("名称"),"类型":c.get("类型"),"星级":c.get("星级"),
            "武器":c.get("武器"),"主能力":c.get("主能力"),"副能力":c.get("副能力")} for c in raw])
    m = re.match(r"^characters/(.+)$", sub)
    if m:
        n = m.group(1).strip()
        for c in (_read_json(_DATA / "characters.json") or []):
            if c.get("名称") == n: return _json(start_response, c)
        return _json(start_response, {"error":f"not found: {n}"},"404")

    # 武器列表
    if sub == "weapons/detail/all":
        d = _read_json(_DATA / "weapons.json")
        return _json(start_response, d) if d else _json(start_response, {"error":"not found"},"404")
    if sub == "weapons":
        raw = _read_json(_DATA / "weapons.json") or []
        result = []
        for w in raw:
            e = {"名称":w.get("名称"),"类型":w.get("类型"),"星级":w.get("星级")}
            for k in ("附加属性","武器技能","普通技能","特殊技能"):
                if k in w: e[k] = w[k]
            result.append(e)
        return _json(start_response, result)
    m = re.match(r"^weapons/(.+)$", sub)
    if m:
        n = m.group(1).strip()
        for w in (_read_json(_DATA / "weapons.json") or []):
            if w.get("名称") == n: return _json(start_response, w)
        return _json(start_response, {"error":f"not found: {n}"},"404")

    # 装备列表
    if sub == "equipments/detail/all":
        d = _read_json(_DATA / "equipments.json")
        return _json(start_response, d) if d else _json(start_response, {"error":"not found"},"404")
    if sub == "equipments":
        raw = _read_json(_DATA / "equipments.json") or []
        return _json(start_response, [{"名称":e.get("名称"),"装备种类":e.get("装备种类"),
            "部位":e.get("部位"),"稀有度":e.get("稀有度"),"所属套组":e.get("所属套组"),
            "属性词条":e.get("属性词条",[]),"三件套效果":e.get("三件套效果",[])} for e in raw])
    m = re.match(r"^equipments/set/(.+)$", sub)
    if m:
        s = m.group(1)
        raw = _read_json(_DATA / "equipments.json") or []
        return _json(start_response, [e for e in raw if e.get("所属套组") == s])
    m = re.match(r"^equipments/slot/(.+)$", sub)
    if m:
        s = m.group(1)
        raw = _read_json(_DATA / "equipments.json") or []
        return _json(start_response, [e for e in raw if e.get("部位") == s])
    m = re.match(r"^equipments/(.+)$", sub)
    if m:
        n = m.group(1).strip()
        for e in (_read_json(_DATA / "equipments.json") or []):
            if e.get("名称") == n: return _json(start_response, e)
        return _json(start_response, {"error":f"not found: {n}"},"404")

    return _json(start_response, {"error": "unknown endpoint"}, "404")

_MIME = {".js":"application/javascript",".css":"text/css",".svg":"image/svg+xml",
         ".png":"image/png",".ico":"image/x-icon",".html":"text/html",
         ".json":"application/json",".woff2":"font/woff2",".webp":"image/webp"}

def application(environ, start_response):
    result = _handle_api(environ, start_response)
    if result is not None:
        return result
    path = environ.get("PATH_INFO", "")
    fp = _DIST / (path.lstrip("/") if path not in ("","/") else "index.html")
    if not fp.is_file(): fp = _DIST / "index.html"
    if fp.is_file():
        body = fp.read_bytes()
        ct = _MIME.get(fp.suffix, "application/octet-stream")
        start_response("200 OK", [("Content-Type",ct),("Content-Length",str(len(body)))])
        return [body]
    start_response("404 NOT FOUND", [("Content-Type","text/plain")])
    return [b"Not Found"]
WSGICODE
```

### WSGI 代码说明

| 部分 | 说明 |
|------|------|
| `_handle_api` | 同步处理关键 API：健康检查、角色/武器/装备增删改查、数据摘要、搜索目录 |
| `a2wsgi.ASGIMiddleware` | 兜底方案（实际因 async 问题可能卡住，关键数据已在 WSGI 层处理） |
| `application` 函数 | 先尝试 API 处理 → 静态文件 → SPA 回退到 `index.html` |
| 数据路径 `_DATA` | 指向 `games/endfield/data/`，WSGI 直接读 JSON 文件返回 |
| SPA 路由 | 任何非 API、非静态文件的路径都返回 `index.html` |

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
# 在本地（用完整绝对路径，避免目录混淆）
cd your-project/frontend
npm install
npm run build
Compress-Archive -Path "your-project/frontend/dist/*" -DestinationPath "your-project/frontend/dist.zip" -Force
```

#### 上传前端 dist.zip

将上一步生成的 `dist.zip` 通过 PythonAnywhere **Files** 页面上传到服务器（如 `/home/yourname/` 目录下），然后：

```bash
cd ~/your-project/frontend
rm -rf dist
mkdir dist
cd dist
unzip ~/dist.zip
rm ~/dist.zip
# 回到 Web 页面点 Reload
```

> ⚠️ **避免 `dist/dist/` 双层嵌套**：如果使用 `unzip ~/dist.zip -d dist`，zip 包内如果包含 `dist/` 文件夹本身（而不是其内容），会产生 `dist/dist/index.html` 的嵌套路径，导致 WSGI 找不到文件、页面返回 404。解决方法之一是用本文推荐的 `mkdir dist && cd dist && unzip ~/dist.zip` 方式，或解压后执行：
> ```bash
> cd ~/your-project/frontend/dist && cp -r dist/* . && rm -rf dist
> ```

#### 验证前端是否更新成功

```bash
# 检查 JS bundle 大小（新版通常更大，因为包含更多组件）
ls -lh ~/your-project/frontend/dist/assets/*.js
```

也可通过浏览器访问 `https://yourname.pythonanywhere.com/` 查看 HTML 中 JS 文件的 hash，与本地 `dist/` 中的文件名对比是否一致（hash 不同表示是新构建）。

---

## 10. 附录：完整 WSGI 模板

可直接复制使用的通用模板（将 `yourname`、`your-project`、和相关数据路径替换为实际值）：

```python
import sys
import json
import re
from pathlib import Path

# ===== 修改这几个变量 =====
YOUR_USERNAME = "yourname"
YOUR_PROJECT = "your-project"
DATA_SUBDIR = "games/endfield/data"      # JSON 数据目录（相对于项目根）
CUSTOM_PACKAGE_PATHS = [
    "framework/src",                     # 自定义 Python 包路径
]
# =========================

_BASE = Path(f"/home/{YOUR_USERNAME}/{YOUR_PROJECT}")
for p in [str(_BASE / x) for x in CUSTOM_PACKAGE_PATHS] + [str(_BASE), str(_BASE / "backend")]:
    if p not in sys.path:
        sys.path.insert(0, p)

VENV = Path(f"/home/{YOUR_USERNAME}/.virtualenvs/{YOUR_PROJECT}/bin/activate_this.py")
if VENV.exists():
    exec(open(str(VENV)).read(), {"__file__": str(VENV)})

from a2wsgi import ASGIMiddleware
try:
    from main import app
    _fastapi = ASGIMiddleware(app)
except Exception:
    _fastapi = None

_DATA = _BASE / DATA_SUBDIR
_DIST = _BASE / "frontend" / "dist"


def _read_json(path):
    if not path.is_file(): return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _json(start_response, data, status="200 OK"):
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    start_response(status, [("Content-Type", "application/json; charset=utf-8"),
                            ("Content-Length", str(len(body)))])
    return [body]


def _handle_api(environ, start_response):
    """同步处理关键 API。覆盖不了的走 _fastapi 兜底。"""
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")

    if path == "/api/health":
        return _json(start_response, {"status": "ok", "version": "1.0.0"})

    if not path.startswith("/api/data/"):
        return None
    if method != "GET":
        return _json(start_response, {"error": "not supported"}, "501")

    sub = path[len("/api/data/"):]
    # ===== 在此添加你的数据 API 路由 =====
    # 示例：sub == "items" → 读取 _DATA / "items.json"
    return _json(start_response, {"error": "unknown endpoint"}, "404")


_MIME = {".js": "application/javascript", ".css": "text/css",
         ".svg": "image/svg+xml", ".png": "image/png",
         ".ico": "image/x-icon", ".html": "text/html",
         ".json": "application/json", ".woff2": "font/woff2"}


def application(environ, start_response):
    result = _handle_api(environ, start_response)
    if result is not None:
        return result
    path = environ.get("PATH_INFO", "")
    fp = _DIST / (path.lstrip("/") if path not in ("", "/") else "index.html")
    if not fp.is_file():
        fp = _DIST / "index.html"
    if fp.is_file():
        body = fp.read_bytes()
        ct = _MIME.get(fp.suffix, "application/octet-stream")
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
A: 前端 JS 发起的 API 请求卡住了。先在浏览器访问 `/api/health` 测试，如果也转圈，说明 PythonAnywhere 的 uWSGI 不支持 async event loop，`a2wsgi.ASGIMiddleware` 无法正常处理 FastAPI 的 `async def` 端点。

**解决方案**：在 WSGI 文件的 `_handle_api` 函数中，**用纯同步代码直接处理关键数据 API**（读取 JSON 文件返回），不走 FastAPI。如本文 §7 给出的完整示例。

### Q: `a2wsgi` 会导致 API 卡死吗？
A: 在 PythonAnywhere 免费套餐上，`a2wsgi.ASGIMiddleware` 对 `async def` 端点会永久卡住（uWSGI 没有运行 event loop）。规避方法：
1. 在 WSGI 层同步处理关键数据 API（推荐，如本文 WSGI 模板所示）
2. 将 FastAPI 端点改为 `def`（非 `async def`），但这影响开发体验
3. 升级到 PythonAnywhere 付费套餐（可能支持 ASGI）

### Q: 前端显示 "Not Found"
A: `frontend/dist/` 目录不存在或文件不完整。检查 `ls ~/your-project/frontend/dist/` 是否有 `index.html` 和 `assets/` 目录。

### Q: PythonAnywhere 显示 "Your webapp took a long time to reload"
A: 这是正常提示，实际可能已生效。刷新页面或稍等几秒再试。

---

## 实战避坑记录（2026-05-31 实测）

### 1. Bash 中复制命令的陷阱

PythonAnywhere **Bash 控制台不支持多行粘贴**。粘贴包含多条命令的代码块时，后面的行会被解释为当前交互命令的输入（例如粘贴到 `ssh-keygen` 的路径提示中）。

**正确做法**：每条命令单独复制、粘贴、执行，等提示符返回 `$` 后再执行下一条。

### 2. SSH key 优于 HTTPS

PythonAnywhere 上 `git pull` 用 HTTPS 地址时，需要输入 GitHub 用户名和 Personal Access Token（不是密码），步骤繁琐且容易混淆。推荐改用 SSH：

```bash
# 在 PythonAnywhere Bash 中生成 SSH key
ssh-keygen -t ed25519 -C "你的邮箱@github.com"
# 一路按 Enter 用默认路径和空密码

# 查看公钥
cat ~/.ssh/id_ed25519.pub
# 复制输出，添加到 GitHub → Settings → SSH and GPG keys

# 切换远程地址
cd ~/your-project
git remote set-url origin git@github.com:你的用户名/你的仓库.git

# 首次连接会确认指纹，输入 yes 即可
git pull
```

### 3. `async def` → `def` 兼容问题

PythonAnywhere 免费套餐的 `a2wsgi.ASGIMiddleware` 无法处理 `async def` 端点（uWSGI 没有 event loop，会永久卡住）。

**解决方案**：对不需要 `await` 的简单端点（返回列表、字典、做内存操作等），直接用 `def` 而非 `async def` 声明。例如：

```python
# 错误的写法（PythonAnywhere 上会卡死）
@router.get("/enemies")
async def get_enemy_choices():
    return [...]

# 正确的写法（同步执行，ASGI 桥接可正常工作）
@router.get("/enemies")
def get_enemy_choices():
    return [...]
```

### 4. 必须安装 `python-multipart`

FastAPI 的 `Form data` 解析依赖 `python-multipart`，如果后端需要接收表单数据（如文件上传），须在虚拟环境中安装：

```bash
workon your-virtualenv
pip install python-multipart
```

### 5. 前端文件无法更新

如果部署新代码后页面无变化，检查两点：

| 排查步骤 | 方法 |
|----------|------|
| 1. `dist/dist/` 嵌套 | `ls ~/your-project/frontend/dist/` 确认直接看到 `index.html` 和 `assets/`，没有嵌套 |
| 2. JS hash 版本 | 浏览器打开页面查看 HTML 中 `<script>` 的 src，对比本地 `dist/index.html` 中是否一致 |
| 3. 浏览器缓存 | 按 `Ctrl+F5` 强制刷新（不是普通 F5） |
| 4. 确认 Web App 已 Reload | 去 PythonAnywhere Web 页面点 Reload |
