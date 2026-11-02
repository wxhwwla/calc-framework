# 自动化测试框架

> 终末地计算器自动化测试 — Web + 桌面应用 + 打包后 exe

## 目录结构

```
scripts/auto_test/
├── README.md                 # 本文件
├── requirements.txt          # Python 依赖
├── config.py                 # 配置（路径、超时、截图目录等）
├── web_test.py               # Web 前端测试（Cypress 封装）
├── desktop_test.py           # 桌面应用测试（pywinauto）
├── packaged_test.py          # 打包后 exe 测试
├── run_all.py                # 一键运行所有测试
├── utils/
│   ├── __init__.py
│   ├── screenshot.py         # 截图工具
│   ├── qt_inspector.py       # Qt 控件检查器
│   └── report.py             # 测试报告生成
└── screenshots/              # 截图输出目录
    ├── web/
    ├── desktop/
    └── packaged/
```

## 快速开始

```powershell
# 1. 安装依赖
pip install -r scripts/auto_test/requirements.txt

# 2. 运行所有测试
python scripts/auto_test/run_all.py

# 3. 只运行某一层
python scripts/auto_test/web_test.py        # Web 测试
python scripts/auto_test/desktop_test.py    # 桌面应用测试
python scripts/auto_test/packaged_test.py   # 打包后测试
```

## 测试流程

### 第 1 层：Web 前端
- 启动 Vite dev server
- 运行 Cypress E2E 测试
- 截图失败页面
- 输出测试报告

### 第 2 层：Python 桌面应用
- 启动 `games/endfield/main.py`
- 用 pywinauto 识别 Qt 控件
- 自动点击、输入、截图
- 检查功能完整性

### 第 3 层：打包后 exe
- 运行 `scripts/main_build.py --target launcher`
- 直接启动 `Game Calc Platform.exe`（不带参数），验证启动器 → 自动拉起终末地链路
- 等待启动器与终末地真实窗口，记录启动耗时
- 点击「确认选择」，等待按钮变为「已确认」后读取乘区表
- 乘区表内容输出到 `screenshots/packaged/zone_table.txt`

## 输出

- 截图：`scripts/auto_test/screenshots/`
- 报告：`scripts/auto_test/screenshots/summary_report.md`（分层报告在 `screenshots/{web,desktop,packaged}/report.md`）

## 注意事项

1. **桌面测试需要显示器** — pywinauto 需要实际的 GUI 环境
2. **首次运行需安装 Cypress** — `cd web/frontend && npx cypress install`
3. **打包测试耗时较长** — PyInstaller 打包可能需要 5-10 分钟
4. **不要用不读取的管道承接 exe 输出** — 冻结版 windowed exe 仍会向 stdout 写 INFO 日志；`subprocess.PIPE` 写满后 UI 线程会阻塞在 logging 锁上，窗口变成「未响应」。`packaged_test.py` 使用 `DEVNULL`，应用日志见 `logs/`
