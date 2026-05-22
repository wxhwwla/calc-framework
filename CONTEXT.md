# 终末地伤害计算器 — 领域上下文

本文件定义项目内统一术语，供 Issue、测试与文档引用。

## 核心对象

| 术语 | 含义 |
|------|------|
| **角色** | `characters.json` 中的一条记录，含类型、星级、等级曲线、四维属性、战技/连携/终结技倍率等 |
| **武器** | `weapons.json` 中的一条记录，含基础攻击力曲线、以 `+` 结尾的附加属性、可选**特殊能力** |
| **等级曲线** | 与角色/武器等级列表等长的数值数组（通常 90 级），由 JSON 预存，运行时直接读取 |
| **潜能** | 武器精炼等级序列（`talent`，0–5），不是角色天赋 |

## 属性与计算

| 术语 | 含义 |
|------|------|
| **主能力 / 副能力** | 角色四维（力量、敏捷、智识、意志）中的主、副属性名称 |
| **信赖** | 角色信赖加成，影响能力乘区 |
| **乘区** | `calculation/multiplicative_zones/` 中的乘法区链：能力乘区、能力值加成、最终攻击力等 |
| **成长公式** | `value(lv) = base + floor((growth * (lv - 1) + offset) / divisor)`，用于反推与数据生成 |
| **特殊能力** | 武器字段 `[是否启用, "属性名+", [各潜能等级数值…]]` |

## 数据管道

| 术语 | 含义 |
|------|------|
| **统一加载层** | `data.loader`：`get_characters()` / `get_weapons()`，带缓存，`strict` 失败抛 `DataLoadError` |
| **预烘焙 JSON** | 已写入完整曲线的 JSON；GUI 不再在运行时调用 `process_*` |
| **录入脚本** | `add_weapon.py`、`add_character.py`、`scripts/seed_weapons.py`，可用 `process_*` 规范化后写回 JSON |

## 工程

| 术语 | 含义 |
|------|------|
| **仓库根目录** | Git 克隆顶层（含 `CONTEXT.md`、`.github/`、`github_upload_module.py`） |
| **Python 包目录** | `endfield_damage_calculator/`（`main.py`、`tests/`、`pip install -e` 的工作目录） |
| **打包路径** | PyInstaller 下通过 `utils.path_utils.get_resource_path` 解析 bundled 数据 |
| **右侧乘区** | GUI 最右列（第 7 列），展示防御减伤、能力乘区与最终攻击力；**总伤结算**仍为后续产品功能 |
| **角色属性列** | GUI 第 3 列，展示角色等级曲线属性（力量、敏捷等）及战技/连携技/终结技倍率明细（等级取自选择区滑块）；不含选择摘要 |
| **武器属性列** | GUI 第 5 列，仅展示武器基础攻击与附加属性明细，不含选择摘要 |
| **上传流程** | 根目录 `github_upload_module.py`；`_VERSION` 自动 bump；可选提交签名；说明见 `please_read_me.UPLOAD_WORKFLOW` |
| **下载覆盖** | 根目录 `github_download_module.py`；须输入确认词 `覆盖本地`；会丢弃未提交与未跟踪文件 |
| **数据来源与许可** | GUI 按钮 + `docs/数据来源与许可.md`；软件 AGPL/商业双许可，数据见 `DATA_LICENSE` |
| **BWIKI 侦察** | `scripts/bwiki_scout/` 阶段 C 拉取 Wiki、阶段 B 解析草案；产出在 `output/`（gitignore），不写入正式 JSON |
