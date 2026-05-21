# 终末地伤害计算小工具

> 《明日方舟：终末地》配装与乘区辅助工具（CustomTkinter GUI）

## 文档分层

| 层级 | 文件 | 适合谁 |
|------|------|--------|
| **门面（本页）** | 仓库根 `README.md` | 第一次打开仓库、GitHub 首页 |
| **详细开发** | [`endfield_damage_calculator/README.md`](endfield_damage_calculator/README.md) | 安装、GUI、测试、API、数据格式 |
| **操作速查** | [`docs/操作指令集.md`](docs/操作指令集.md) | 日常命令与 `[根]` / `[包]` 目录约定 |
| **领域术语** | [`CONTEXT.md`](CONTEXT.md) | Issue、测试、文档统一用语 |
| **算法说明** | [`PROJECT_DOCUMENTATION.md`](PROJECT_DOCUMENTATION.md) | 公式与架构细节 |

## 目录约定

| 名称 | 路径 | 典型操作 |
|------|------|----------|
| **仓库根** `[根]` | 本目录 | `github_upload_module.py`、`github_download_module.py` |
| **Python 包** `[包]` | `endfield_damage_calculator/` | `main.py`、`pytest`、`build.py` |

## 快速开始

```powershell
# [包] 安装并启动 GUI
cd endfield_damage_calculator
pip install -e ".[dev]"
python main.py
```

```powershell
# [根] 推送 GitHub（版本号由脚本维护，见包内 please_read_me.py）
python github_upload_module.py
```

更多命令（测试、打包、SSH、拉取覆盖本地）见 [`docs/操作指令集.md`](docs/操作指令集.md)。

## 功能概览

- 角色 / 武器选择，分列展示属性与技能倍率
- 确认选择后刷新右侧乘区（能力、攻击力等）
- 角色与武器 JSON 数据、公式反推与录入脚本

细节与布局说明见 [**详细 README**](endfield_damage_calculator/README.md)。

## 许可证

**GPL-3.0 + 附加条款**（禁止商用；B 站充电等自愿创作者支持除外）。  
全文见仓库根目录 [`LICENSE`](LICENSE)。
