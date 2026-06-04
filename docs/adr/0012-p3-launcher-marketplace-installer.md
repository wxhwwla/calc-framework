# ADR-0012：P3 多游戏启动器 + 应用商店 + 安装包

**状态**：已批准（Phase 1-3 已完成，Phase 4-5 待办）  
**日期**：2026-05-30  
**决策者**：维护者  

---

## 上下文

项目已完成 P0-P2 全部任务：数据管线打通、设计-打包链路、通用展示层、块级封装、OCR 截图识装、插件系统。当前有 4 个独立的 exe 入口（计算器、设计器、布局编辑器、图编辑器），分发方式为 ZIP 压缩包。

P3 的目标是将项目从「开发者工具集」升级为「闭箱即用的通用计算平台」：
- **B 方向**：多游戏启动器 + 适配包在线市场
- **C 方向**：产品化收尾（单 exe + 自动更新 + 安装包）

两者天然互补，合并为一个阶段。

---

## 决策

P3 按以下 5 个阶段推进：

### Phase 1：统一启动器 GUI

**问题**：目前 4 个独立 entry point（`main.py` / `main_designer.py` / `main_editor.py` / `main_graph_editor.py`），用户需要知道启动哪个文件。

**方案**：创建 `main_launcher.py`，一个 PySide6 窗口作为唯一入口：

```
┌────────────────────────────────────────────┐
│  Game Calc Launcher  v1.0.0                │
├────────────────────────────────────────────┤
│  选择游戏适配器                              │
│                                            │
│  ┌─────────────────────────────────┐       │
│  │ [终末地]      已安装 v2.3.0    │       │
│  │ [卡牌RPG]     已安装 v1.0.0    │       │
│  │ [MOBA]        已安装 v0.9.0    │       │
│  │ [+] 从商店安装更多...          │       │
│  └─────────────────────────────────┘       │
│                                            │
│  工具                                      │
│  [图编辑器] [布局编辑器] [数据设计器] [插件管理器]│
│                                            │
│  设置                                      │
│  [主题] [语言] [检查更新] [关于]             │
└────────────────────────────────────────────┘
```

- 自动发现 `framework/adapters/` 下的所有适配包
- 加载适配包 → 启动 CalcPackViewer 或 ComputeSheet
- 工具按钮直接打开对应编辑器
- 支持 `.calcpack` 文件关联（双击打开）

### Phase 2：单 exe 打包

**问题**：当前 `main_build.py` 分 3 个目标打包（calculator / designer / layout-editor），输出 3 个独立 exe。

**方案**：改为**单 exe + 插件式子命令**：

- 新入口点替换所有旧入口点
- `main_build.py` 改为只有一个打包目标 `launcher`
- 用户从启动器内选择功能，而不是启动不同 exe

**打包结构**：单 exe（~80MB）内含框架 + 终末地适配包 + 工具入口。其他游戏适配包通过商店按需下载。

### Phase 3：自动更新机制

**问题**：用户需要手动下载新版 ZIP 替换。

**方案**：启动器内置更新检查：

1. 启动时后台请求 `https://api.github.com/repos/.../releases/latest`
2. 比较本地 `_VERSION` vs 远程 tag
3. 有新版本 → 弹窗通知，可选：
   - 下载更新（后台下载 .exe，替换当前文件）
   - 忽略此版本
   - 查看发布说明
4. 更新下载使用带进度的 HTTP 流式下载，完成前做 SHA256 校验

### Phase 4：Calc Hub 在线市场

**问题**：当前 Calc Hub 是本地静态 HTML，只展示内置插件。

**方案**：升级为完整的适配包在线市场：

**后端**（FastAPI，`web/backend/` 已有骨架）：
```
POST /api/adapters/upload    — 上传适配包
GET  /api/adapters/          — 浏览所有适配包
GET  /api/adapters/{id}      — 查看详情
GET  /api/adapters/download/{id} — 下载
POST /api/adapters/{id}/rate — 评分
```

**前端**（`web/hub/` 现有页面升级）：
- 适配包列表（支持搜索/筛选/排序）
- 详情页（描述/版本/截图/评分/评价）
- 一键下载按钮（启动器内调用自动安装）
- 上传页（打包上传适配包目录）

**集成**：启动器的「从商店安装」按钮调用 Hub API。

**部署**：可选 GitHub Pages + Cloudflare Workers 或 Vercel。

### Phase 5：安装包

**问题**：分发方式是手动解压 ZIP。

**方案**：使用 NSIS 制作 Windows 安装包（Inno Setup 备选）：

```
终末地计算器_Setup_v2.3.0.exe
├── 安装到 Program Files\Game Calc Platform\
├── 桌面快捷方式
├── 开始菜单目录
├── .calcpack 文件关联
├── 卸载程序
└── 可选添加 PATH（devtool.py）
```

CI 中自动生成安装包作为 Release artifact 之一。

---

## 影响分析

| 组件 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 |
|------|---------|---------|---------|---------|---------|
| `main_launcher.py` | **新建** | 更新 | 更新 | 更新 | 不动 |
| `main_build.py` | 不动 | **重构** | 不动 | 不动 | **扩展** |
| `release_layout.py` | 不动 | **重构** | 不动 | 不动 | 不动 |
| `framework/launcher.py` | **参考** | 不动 | 不动 | 不动 | 不动 |
| `web/backend/` | 不动 | 不动 | 不动 | **重写** | 不动 |
| `web/hub/` | 不动 | 不动 | 不动 | **升级** | 不动 |
| `.github/workflows/release.yml` | 不动 | **更新** | 不动 | 不动 | **更新** |
| `devtool.py` | 不动 | 更新 | 不动 | 更新 | 不动 |
| `docs/` | 更新 | 更新 | 更新 | 更新 | 更新 |

---

## 备选方案

### 不合并 B 和 C

分开做的话，B（多游戏）需要先做完才能做 C（单 exe）——因为单 exe 就是为了把多个游戏入口合并。顺序反了会返工。

### 不做在线市场，只做本地启动器

Phase 4 可以延后，不影响 Phase 1-3 的价值。短期内适配包通过 GitHub 手动下载也能工作。

### 不做安装包，只维持 ZIP 分发

ZIP 分发对技术用户够用。安装包的价值在于面向非技术玩家的分发。

---

## 后续决策

- Phase 1-3 自动连续，不做中间验收 ✅（2026-06-04 已完成）
- Phase 4（在线市场）在 Phase 3 完成后由维护者决定是否立即开始
- Phase 5（安装包）与 Phase 4 无依赖，可并行

## 实现总结（2026-06-04）

### Phase 1：统一启动器 GUI ✅

`framework/src/calc_framework/ui/launcher/window.py` + `runtime.py` 已实现：
- 自动发现 `framework/adapters/` 下的所有适配包
- 游戏卡片 + 启动按钮（子进程启动游戏或 ComputeSheet）
- 开发者工具箱入口
- 本地 Web 服务器控制
- 打开 .calcpack 文件

### Phase 2：单 exe 打包 ✅

新增/修改文件：

| 文件 | 说明 |
|------|------|
| `release_bundle/launcher_entry.py` | 统一 exe 入口，路由 `--game` / `--tool` / `--calcpack` / `--version` |
| `release_bundle/release_layout.py` | 新增 `launcher` build target（app name: Game Calc Platform） |
| `scripts/main_build.py` | 新增 `--target launcher` 打包配置，内嵌框架 + 双游戏 + 工具 + 适配器 |
| `framework/src/calc_framework/ui/launcher/runtime.py` | 支持 `sys.frozen` 检测，冻结模式用同一 exe 带参数启动 |
| `.github/workflows/release.yml` | 构建命令改为 `main_build.py --target launcher`，发布 `GameCalcPlatform_v*.zip` |
| `installer/endfield_calculator_setup.nsi` | 优先安装新版 launcher exe，兼容旧版分体 exe |
| `installer/build_installer.py` | 新增 launcher 目录校验 |

打包命令：
```bash
python scripts/main_build.py --target launcher --no-bump
```

使用方式：
```bash
Game Calc Platform.exe                      # 启动器
Game Calc Platform.exe --game endfield      # 直接终末地
Game Calc Platform.exe --game arknights     # 直接明日方舟
Game Calc Platform.exe --tool dev_toolkit   # 直接工具箱
Game Calc Platform.exe --version             # 版本号
```

### Phase 3：自动更新 ✅

新增 `framework/src/calc_framework/ui/launcher/auto_update.py`，集成到启动器 GUI：

- 启动时后台检查 GitHub Release 版本
- 比较 `_EXE_VERSION` vs 远程 tag
- 新版本弹窗通知（`_UpdateDialog`）
- 带进度条下载 ZIP + SHA256 校验 + 解压替换
- 手动「检查更新」按钮触发
- 更新完成提示重启

### Phase 4：Calc Hub 在线市场 ⏳ 待办

依赖项：启动器已预留「Calc Hub」按钮和 `_HUB_URL` 常量，后端 API 和前端页面待开发。

### Phase 5：安装包 ✅（已有基础，NSIS 脚本已更新）

安装包已支持新版 launcher 结构，`GameCalcPlatform_Setup_v*.exe` 作为发布产物。
