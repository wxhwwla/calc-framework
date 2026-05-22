# 项目审计 Issues（2026-05-20）

由 `/to-issues` 根据代码库检查生成。确认粒度后待发布到 GitHub。

发布方式（需先 `gh auth login`）：

```powershell
cd e:\endfield_damage_calculator
.\scripts\create_audit_issues.ps1
```

---

## Issue 1 — 轮换 Git 凭据并清理 remote URL

**Labels:** `ready-for-human`

### What to build

`git remote` 的 `origin` URL 中嵌入了 GitHub Personal Access Token。任何能访问本机或仓库克隆的人都有可能看到该 token。需要撤销已暴露的 token，并将 remote 改为不含凭据的 HTTPS 或 SSH URL，后续通过凭据管理器或 `gh auth` 认证。

### Acceptance criteria

- [ ] 在 GitHub Settings → Developer settings 中撤销/轮换已暴露的 PAT
- [ ] `git remote -v` 显示的 URL 不再包含 token 或密码
- [ ] `git fetch` / `git push` 在清理后仍可正常工作（SSH 或 Git Credential Manager）
- [ ] 确认 token 未提交进 git 历史（若曾提交需按 GitHub 指南处理）

### Blocked by

None - can start immediately

---

## Issue 2 — 添加 CI：自动运行 pytest

**Labels:** `ready-for-agent`

### What to build

仓库目前没有 GitHub Actions。添加工作流，在 push/PR 时在 `endfield_damage_calculator` 目录下执行 `python -m pytest tests/`，防止回归。工作流应使用 Python 3.10+，安装 `pyproject.toml` 中的运行时依赖。

### Acceptance criteria

- [ ] `.github/workflows/` 中存在 CI 工作流
- [ ] PR 或 push 到默认分支时自动运行测试
- [ ] 当前 59 个测试在 CI 中通过
- [ ] README 或文档中简要说明如何本地运行相同命令

### Blocked by

None - can start immediately

---

## Issue 3 — 游戏 JSON 数据契约测试

**Labels:** `ready-for-agent`

### What to build

`characters.json` 与 `weapons.json` 是 GUI 与计算引擎的数据源，但缺少针对「整库数据形状」的自动化校验。新增契约测试：每条记录具备必填字段；`基础攻击力` 为 90 级曲线；以 `+` 结尾的潜能属性长度符合约定；`特殊能力` 启用时结构为 `[true, name, curve]` 且 curve 长度合法。测试失败时 CI 应明确报告武器/角色名称。

### Acceptance criteria

- [ ] 新增测试模块覆盖全部角色与武器条目（非仅抽样）
- [ ] 故意损坏 JSON 时测试失败且错误信息可定位到条目名称
- [ ] 与 Issue 2 的 CI 集成后自动运行
- [ ] 不修改现有合法数据的数值，仅校验结构

### Blocked by

None - can start immediately

---

## Issue 4 — 统一数据加载路径并移除导入副作用

**Labels:** `ready-for-agent`

### What to build

当前存在双路径：`data.loader` 与 `character_data.py` / `weapon_data.py` 在模块导入时执行 `load_and_process_*` 并可能触发 `check_json_to_save`。`main.py` 预加载同时 import 两套模块。应统一为仅通过 `data.loader` 读取与缓存；移除模块级自动加载与自动写回 JSON 的副作用；GUI 与测试仍能从缓存获得相同数据。

### Acceptance criteria

- [ ] 启动应用与运行测试不再因 import `weapon_data` 而隐式改写 JSON
- [ ] `get_characters()` / `get_weapons()` 为唯一推荐数据入口
- [ ] 现有 59 个测试仍通过
- [ ] 文档（README 或 `docs/算法与架构.md`）说明数据加载约定

### Blocked by

None - can start immediately

---

## Issue 5 — 重构武器录入工具（CLI + 无副作用）

**Labels:** `ready-for-agent`

### What to build

`add_weapon()` 对 `bonus_attrs` 内字典使用 `pop('special')`，会修改调用方传入的对象；`__main__` 中硬编码多把武器的批量添加，不利于可重复的数据维护。重构为：函数不 mutate 入参；示例/批量配置与库代码分离（CLI 参数或独立配置文件）；录入后新武器可在 GUI 中选择并显示正确属性与曲线。

### Acceptance criteria

- [ ] 单元测试证明相同 `bonus_attrs` 字典在调用前后一致
- [ ] 可通过 CLI 或独立配置添加一把武器，无需编辑 `add_weapon.py` 主体
- [ ] 新录入武器通过 Issue 3 的契约测试
- [ ] GUI 中可选中并展示新武器的基础攻击与附加属性

### Blocked by

- BLOCKER_ISSUE_4（统一数据加载路径）

---

## Issue 6 — 数据加载失败时可见报错

**Labels:** `ready-for-agent`

### What to build

`data.loader` 在 JSON 缺失、解析失败或其它异常时返回空列表且不提示，GUI 表现为「没有角色/武器」难以排查。应在开发/运行时记录可诊断的错误（日志或一次性警告），并区分「文件不存在」与「JSON 损坏」；可选在启动时向用户显示简短错误信息。

### Acceptance criteria

- [ ] 故意损坏 JSON 时，启动或 `get_weapons()` 不会产生静默空数据（至少有日志或用户可见提示）
- [ ] 正常数据路径行为不变
- [ ] 测试覆盖至少一种失败场景（临时坏文件或 mock）
- [ ] 与统一加载层（Issue 4）的实现一致

### Blocked by

- BLOCKER_ISSUE_4（统一数据加载路径）

---

## Issue 7 — 打包与仓库卫生

**Labels:** `ready-for-agent`

### What to build

根目录生成的 `终末地伤害计算器.exe` 未列入 `.gitignore`，易被误提交。打包脚本已捆绑 `characters.json` / `weapons.json`，需确认流程文档化并可选增加轻量冒烟（打包后或模拟 frozen 路径能加载数据）。

### Acceptance criteria

- [ ] `.gitignore` 忽略项目根及 `dist/` 下的 `*.exe`（或明确命名的发布 exe）
- [ ] `build.py` 文档说明输出位置与版本号来源
- [ ] 至少一种自动化或文档化步骤验证打包产物能加载角色/武器数据
- [ ] 仓库中不包含已构建的 exe 二进制（若已跟踪则移除）

### Blocked by

None - can start immediately

---

## Issue 8 — 开发依赖与项目元数据

**Labels:** `ready-for-agent`

### What to build

`pyproject.toml` 中作者为占位信息；`pytest` 未声明为开发依赖，新贡献者需自行发现测试命令。补充 `[project.optional-dependencies] dev`（含 pytest 等），修正作者/描述元数据，并在 README 中写明 `pip install -e ".[dev]"` 与测试命令。

### Acceptance criteria

- [ ] `pyproject.toml` 含 dev 可选依赖且可安装
- [ ] 作者/邮箱占位符已替换为真实信息或移除敏感占位
- [ ] README 记载本地开发与测试的一键命令
- [ ] 与 Issue 2 CI 使用的依赖方式一致或文档说明差异

### Blocked by

None - can start immediately
