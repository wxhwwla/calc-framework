# 全面审查第三批修复实现计划

> **面向 AI 代理的工作者：** 使用 executing-plans 逐任务实现；先写失败测试。项目禁止代理直接 git add/commit/push。

**目标：** 修复 Hub/适配器 ID、管理认证、下载制品、方舟连发、搜索 Buff 和标准快照剩余问题。

**架构：** 本地适配器与市场包 ID 分离；管理 Token 由前端会话设置并统一注入；下载失败显式返回 404；搜索请求复用普通配装的 Buff 字段；标准快照通过现有同步工具生成。

**技术栈：** FastAPI、React、TypeScript、Zustand、pytest、Vitest/Cypress。

**规格：** `docs/项目全面审查记录.md` A-10、A-13、A-15、A-26、A-27、A-30。

## 全局约束

- 最小 diff，公共 API 向后兼容，每项 RED→GREEN。
- Token 只保存在用户主动选择的浏览器存储，不写日志、不进 URL。
- 缺制品不得伪装成可运行 zip 下载成功。
- 不上传、不提交、不提升版本。

## 审查重点（Review Focus）

- 任意上传文件名都能从市场下载，本地适配器显示名不能作为 pack ID。
- 配置 Token 后写接口真正携带认证，未配置时错误可读。
- 下载内容必须包含真实后端制品，不得返回 README 占位。
- hitCount=2 的结果与单发明确区分或正确翻倍。
- 手动 Buff 改变搜索评分；标准快照与运行数据条数一致。

---

### 任务 1：Hub 与适配器 ID
- [x] 测试任意文件名下载和本地目录 ID schema。
- [x] Hub 元数据保存真实 filename；本地下载移除错误市场动作或改接真实市场 ID。

### 任务 2：管理 Token UI 与请求头
- [x] 测试 Token 注入 data/hub/contribute 写请求。
- [x] 增加用户可填 Token 的设置入口，统一请求头，不记录密钥。

### 任务 3：本地后端下载与方舟连发
- [x] 缺制品返回明确 404，存在 public dist zip 时使用真实文件。
- [x] hitCount 进入 Web 请求/后端模型，结果按总伤害计算。

### 任务 4：搜索手动 Buff
- [x] 测试 loadout→search 请求保留 manual_buffs，后端模型接受并参与评分。

### 任务 5：标准数据快照
- [x] 用现有同步工具更新终末地标准快照，验证角色/武器/装备条数和缺失项。

## 验收
- 相关 Python/TS 测试通过；真实 Hub 下载、认证、连发和 Buff 对照通过。
- 更新审查账本、错误集和接续手册，其他开放项继续保留。

## 完成记录（2026-11-25）

- 工具链 249 passed；Web 后端 253 passed / 2 skipped；终末地搜索 88 passed / 7 skipped；前端 113 passed。
- TypeScript、ESLint、生产构建、产物检查、Ruff、OpenAPI、活跃链接和布局门禁通过。
- 标准快照与运行数据均为角色/武器/装备 27/75/163，名称缺失集合为空。
- A-15、A-26 仅部分完成；其他开放项保留在 `docs/项目全面审查记录.md`。
- 本批未提交、未上传，等待用户明确执行上传脚本。
- 独立最终审查的 3 个 Important（真实 occurrence 键、单技能跨键混入、异常 Buff）均已 RED→GREEN 修复；搜索套件最终为 88 passed / 7 skipped。
- 延后的 Minor：Hub 创建/上传只显示 HTTP 状态码，未展开后端认证 detail；不影响认证安全失败。
