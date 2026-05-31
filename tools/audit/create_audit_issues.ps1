# 将 docs/agents/audit-issues-2026-05-20.md 中的 8 个审计项发布为 GitHub Issues
# 用法: gh auth login 后，在仓库根目录执行 .\scripts\create_audit_issues.ps1

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "未找到 gh CLI。请先安装 GitHub CLI 并执行: gh auth login"
}

$auth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "gh 未登录。请执行: gh auth login"
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, (New-Object System.Text.UTF8Encoding $false))
}

function New-Issue {
    param(
        [string]$Title,
        [string]$BodyFile,
        [string[]]$Labels
    )
    $createArgs = @("issue", "create", "--title", $Title, "--body-file", $BodyFile)
    if ($Labels.Count -gt 0) {
        foreach ($label in $Labels) {
            $createArgs += @("-l", $label)
        }
    }
    $prevEap = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & gh @createArgs 2>&1 | Tee-Object -Variable outLines | Out-Null
    $exitCode = $LASTEXITCODE
    $out = ($outLines | Out-String)
    if ($exitCode -ne 0 -and $Labels.Count -gt 0) {
        Write-Warning "带标签创建失败，重试不带标签: $Title"
        & gh issue create --title $Title --body-file $BodyFile 2>&1 | Tee-Object -Variable outLines | Out-Null
        $exitCode = $LASTEXITCODE
        $out = ($outLines | Out-String)
    }
    $ErrorActionPreference = $prevEap
    if ($exitCode -ne 0) {
        throw "创建 issue 失败: $Title`n$out"
    }
    if ($out -match 'issues/(\d+)') {
        $num = [int]$Matches[1]
        Write-Host "Created #$num : $Title"
        return $num
    }
    throw "创建 issue 失败（无法解析编号）: $Title`n$out"
}

$tmp = Join-Path $env:TEMP "endfield-audit-issues"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null

# Issue 1
$body01 = @'
## What to build

`git remote` 的 `origin` URL 中嵌入了 GitHub Personal Access Token。需要撤销已暴露的 token，并将 remote 改为不含凭据的 HTTPS 或 SSH URL。

## Acceptance criteria

- [ ] 在 GitHub 撤销/轮换已暴露的 PAT
- [ ] `git remote -v` 不再显示 token
- [ ] `git fetch` / `git push` 清理后仍可用
- [ ] 确认 token 未留在 git 历史中

## Blocked by

None - can start immediately
'@
Write-Utf8NoBom (Join-Path $tmp "01.txt") $body01

$n1 = New-Issue -Title "安全：轮换 Git 凭据并清理 remote URL" -BodyFile (Join-Path $tmp "01.txt") -Labels @("ready-for-human")

# Issue 2
@'
## What to build

添加 GitHub Actions，在 push/PR 时对 `games/endfield` 运行 `python -m pytest tests/`。

## Acceptance criteria

- [ ] CI 工作流存在且可触发
- [ ] 59 个测试在 CI 通过
- [ ] 文档说明本地等价命令

## Blocked by

None - can start immediately
'@ | Set-Content -Path (Join-Path $tmp "02.txt") -Encoding utf8

$n2 = New-Issue -Title "CI：push/PR 自动运行 pytest" -BodyFile (Join-Path $tmp "02.txt") -Labels @("ready-for-agent")

# Issue 3
@'
## What to build

为 `characters.json` / `weapons.json` 添加全量契约测试：必填字段、90 级攻击曲线、潜能属性长度、`特殊能力` 结构。

## Acceptance criteria

- [ ] 覆盖全部角色与武器条目
- [ ] 坏数据失败时可定位条目名称
- [ ] 接入 CI

## Blocked by

None - can start immediately
'@ | Set-Content -Path (Join-Path $tmp "03.txt") -Encoding utf8

$n3 = New-Issue -Title "测试：角色与武器 JSON 数据契约" -BodyFile (Join-Path $tmp "03.txt") -Labels @("ready-for-agent")

# Issue 4
@'
## What to build

统一经 `data.loader` 加载数据；移除 `weapon_data` / `character_data` 模块导入时的自动加载与 `check_json_to_save` 副作用。

## Acceptance criteria

- [ ] import 不再隐式改写 JSON
- [ ] `get_characters` / `get_weapons` 为唯一推荐入口
- [ ] 59 个测试仍通过

## Blocked by

None - can start immediately
'@ | Set-Content -Path (Join-Path $tmp "04.txt") -Encoding utf8

$n4 = New-Issue -Title "重构：统一数据加载路径并去掉导入副作用" -BodyFile (Join-Path $tmp "04.txt") -Labels @("ready-for-agent")

# Issue 5
$body05 = @'
## What to build

`add_weapon` 不 mutate 入参；示例与 `__main__` 分离；支持 CLI/配置录入；GUI 可展示新武器。

## Acceptance criteria

- [ ] 调用前后 `bonus_attrs` 字典不变
- [ ] CLI 或配置可添加武器
- [ ] 通过数据契约测试且在 GUI 可选中

## Blocked by

- #{0}
'@ -f $n4
Write-Utf8NoBom (Join-Path $tmp "05.txt") $body05

$n5 = New-Issue -Title "重构：武器录入工具（CLI + 无副作用）" -BodyFile (Join-Path $tmp "05.txt") -Labels @("ready-for-agent")

# Issue 6
$body06 = @'
## What to build

JSON 缺失或损坏时不再静默返回空列表；记录日志或向用户显示可诊断错误。

## Acceptance criteria

- [ ] 损坏 JSON 时有日志或可见提示
- [ ] 正常路径不变
- [ ] 测试覆盖失败场景

## Blocked by

- #{0}
'@ -f $n4
Write-Utf8NoBom (Join-Path $tmp "06.txt") $body06

$n6 = New-Issue -Title "修复：数据加载失败时可见报错" -BodyFile (Join-Path $tmp "06.txt") -Labels @("ready-for-agent")

# Issue 7
@'
## What to build

`.gitignore` 忽略构建 exe；文档化 `build.py`；验证打包产物能加载游戏数据。

## Acceptance criteria

- [ ] exe 不会被误提交
- [ ] 打包流程有文档
- [ ] 冒烟或文档验证数据可加载

## Blocked by

None - can start immediately
'@ | Set-Content -Path (Join-Path $tmp "07.txt") -Encoding utf8

$n7 = New-Issue -Title "工程：打包与仓库卫生（gitignore + 冒烟）" -BodyFile (Join-Path $tmp "07.txt") -Labels @("ready-for-agent")

# Issue 8
@'
## What to build

`pyproject.toml` 添加 dev 依赖（pytest）；修正占位作者；README 写明安装与测试命令。

## Acceptance criteria

- [ ] `pip install -e ".[dev]"` 可用
- [ ] 元数据已更新
- [ ] README 有开发说明

## Blocked by

None - can start immediately
'@ | Set-Content -Path (Join-Path $tmp "08.txt") -Encoding utf8

$n8 = New-Issue -Title "工程：开发依赖与 pyproject 元数据" -BodyFile (Join-Path $tmp "08.txt") -Labels @("ready-for-agent")

Write-Host ""
Write-Host "Done. Created issues: #$n1 #$n2 #$n3 #$n4 #$n5 #$n6 #$n7 #$n8"
Write-Host "View: gh issue list"
