# 维护者与责任分工

本文件登记评审、发布、安全和数据合规的责任人。当前为**单维护者模式**，角色由同一人兼任；新增协作者时按本文件模板拆分，并同步更新 [`.github/CODEOWNERS`](.github/CODEOWNERS)。

## 责任人

| 角色 | 责任人 | 覆盖范围 | 主要职责 |
|------|--------|----------|----------|
| 项目维护者 | @wxhwwla | 全仓 | 架构决策、代码评审、Issue 分诊、合并 `develop` |
| 发布负责人 | @wxhwwla | `release_bundle/`、`scripts/`、`.github/workflows/` | 版本号、标签、构建、制品校验与回滚记录 |
| 安全响应 | @wxhwwla | `SECURITY.md`、`web/backend/api/internal/` | 私密接收漏洞报告、48 小时确认、修复与披露 |
| 数据与合规 | @wxhwwla | `DATA_LICENSE`、`NOTICES.md`、`games/*/data/` | 数据来源、第三方许可、NOTICES 与 SBOM 复核 |

**联系邮箱**：wxhwwla@gmail.com（安全漏洞请优先使用 GitHub Security Advisory，勿公开提交 Issue）。

## 决策与评审

- 普通变更：至少 1 名维护者评审；涉及发布、安全、许可的变更按 [`.github/CODEOWNERS`](.github/CODEOWNERS) 指定复核。
- 架构或公共 API 变更：先写 ADR（`docs/adr/`），再实现；讨论结论记录在 PR/Issue。
- 无法达成一致时由项目维护者决定，并在对应 Issue 记录理由与复审日期。
- 单人维护期间，`develop` 上的变更仍须通过 CI（Game / Framework / Web / Security Audit）后才合并到 `main`。

## 发布责任

发布前按 `docs/操作指令集.md` 的上传与打包流程执行，并保留：

1. 版本号来源（`scripts/_version.py`）；
2. CI 运行结果（测试、lint、安全审计）；
3. 制品校验值（checksum）；
4. 已知问题与回滚方式。

发布记录与开放债务的关联见 [`docs/开放问题与治理.md`](docs/开放问题与治理.md)。

## 角色变更

- 新增维护者：由现有维护者提名，完成至少 3 次被合并的实质性 PR，并在本文件与 CODEOWNERS 中登记。
- 退出或长期不可用：转移 CODEOWNERS 与密钥/发布权限，更新 `SECURITY.md` 的联系方式。
- 任何角色变更都需在 `docs/开放问题与治理.md` 的「治理变更记录」中留痕。
