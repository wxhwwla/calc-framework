# Phase 4 Step 4.5 — 代码签名与自动更新生产验证

> 创建：2026-06-17  
> 状态：基础设施 ✅；OV/EV 证书采购与全链路人工验收 ⏳

---

## 目标

1. Windows Authenticode 签名（消除 SmartScreen 警告）
2. 自动更新 HTTPS + SHA256 完整性校验
3. Release CI 发布 checksum 侧车文件

---

## 1. 代码签名（本地 / CI）

### 前置

- 购买 OV 或 EV 代码签名证书（Sectigo / DigiCert 等）
- 安装 Windows SDK（含 `signtool.exe`）或将 `SIGNTOOL_PATH` 指向 signtool

### 环境变量

| 变量 | 说明 |
|------|------|
| `CODE_SIGN_ENABLED=1` | 启用签名 |
| `CODE_SIGN_CERT_SHA1` | 证书存储区指纹（`/sha1`） |
| `CODE_SIGN_PFX_PATH` + `CODE_SIGN_PFX_PASSWORD` | 或 PFX 文件路径 |
| `CODE_SIGN_TIMESTAMP_URL` | 时间戳服务器（默认 DigiCert） |
| `SIGNTOOL_PATH` | 可选，signtool 绝对路径 |

### 本地打包并签名

```powershell
$env:CODE_SIGN_ENABLED = "1"
$env:CODE_SIGN_CERT_SHA1 = "<指纹>"
python scripts/main_build.py --target launcher --sign --no-bump
```

### GitHub Actions（可选）

在仓库 Secrets 配置：

- `CODE_SIGN_CERT_SHA1` — 使用 Windows 运行器证书存储中的指纹  
- 或 `CODE_SIGN_PFX_BASE64` + `CODE_SIGN_PFX_PASSWORD`

`release.yml` 中 **Code sign release PE (optional)** 步骤会在 Secret 存在时签名 `dist/Game Calc Platform/` 内 PE；未配置则跳过。

### 验收

- [ ] `signtool verify /pa "dist/Game Calc Platform/Game Calc Platform.exe"` 通过
- [ ] 未签名机器首次运行无 SmartScreen（需 EV + 声誉累积）

---

## 2. 自动更新校验

### Release 产物

CI 为每个 `dist/*.zip` 生成同名 `.sha256` 侧车（单行 hex），随 Release 上传。

启动器 `auto_update.py` 会：

1. 优先选择 `GameCalcPlatform_v*.zip` 资产
2. 拒绝非 HTTPS 下载 URL
3. ZIP `testzip()` 完整性检查
4. 若存在 `.sha256` 侧车，校验 SHA256 后替换 exe

### 本地验证

```powershell
python -m pytest framework/tests/utils/test_checksums.py framework/tests/utils/test_code_sign.py framework/tests/utils/test_updater.py framework/tests/ui/launcher/test_auto_update.py -q
```

### 生产验收清单

- [ ] 发布 tag 后 Release 含 `GameCalcPlatform_vX.zip` 与 `.sha256`
- [ ] 旧版启动器「检查更新」能发现新版本并下载
- [ ] 篡改 ZIP 或 checksum 后更新失败（SHA256 不匹配）
- [ ] 网络中断 / 磁盘满时有明确错误提示（人工）

---

## 3. 相关文件

| 文件 | 职责 |
|------|------|
| `utils/code_sign.py` | signtool 封装 |
| `utils/checksums.py` | SHA256 侧车读写 |
| `utils/updater.py` | 旧版更新 API（HTTPS + 启动器 ZIP 优先） |
| `framework/.../launcher/auto_update.py` | 启动器更新 UI 链路 |
| `scripts/main_build.py` | `--sign` 打包后签名 |
| `.github/workflows/release.yml` | checksum + 可选签名 |

---

## 未完成（需人工）

- OV/EV 证书采购与 CI Secret 配置
- 核心用户 Beta 群端到端更新实测（见 `improvement-roadmap.md` §自动更新生产验证）
