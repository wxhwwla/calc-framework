# SPDX-License-Identifier: AGPL-3.0
<#
.SYNOPSIS
    act wrapper — 自动检测代理端口 + 避免端口冲突，在 Docker 容器中运行 CI 测试。

.DESCRIPTION
    GitHub Actions 本地运行器。自动扫描 host.docker.internal 上的代理端口，
    生成临时 .actrc 配置并执行 act。

    用法:
      .\scripts\act.ps1 -j test -W .github/workflows/ci.yml
      .\scripts\act.ps1 -j test -W .github/workflows/framework-ci.yml
      .\scripts\act.ps1 -j test -W .github/workflows/web-ci.yml
      .\scripts\act.ps1 --list                        # 列出所有可用 job

.PARAMETER PassthruArgs
    透传给 act 的参数（-j, -W, --list 等）。
#>

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PassthruArgs
)

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$ACT_RC = Join-Path $REPO_ROOT ".actrc"

# ── 1. 自动检测代理端口 ──────────────────────────
$PROXY_HOST = "host.docker.internal"
$PROXY_PORT = $null
$COMMON_PORTS = @(6518, 7890, 7891, 1080, 1081, 10809, 3128, 8080, 8118, 9090)

Write-Host "🔍 检测代理: $PROXY_HOST ..." -ForegroundColor Cyan
foreach ($port in $COMMON_PORTS) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $async = $tcp.BeginConnect($PROXY_HOST, $port, $null, $null)
        $wait = $async.AsyncWaitHandle.WaitOne(300, $false)
        if ($wait -and $tcp.Connected) {
            $tcp.EndConnect($async)
            $PROXY_PORT = $port
            $tcp.Dispose()
            break
        }
        $tcp.Dispose()
    } catch {
        continue
    }
}

if ($PROXY_PORT) {
    Write-Host "  ✅ 检测到代理: $PROXY_HOST`:$PROXY_PORT" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  未检测到代理，使用默认 6518（可能无法拉取远程资源）" -ForegroundColor Yellow
    $PROXY_PORT = 6518
}

# ── 2. 清理旧 act 进程（避免端口 34567 冲突） ─────
$oldAct = Get-Process -Name "act" -ErrorAction SilentlyContinue
if ($oldAct) {
    Write-Host "🧹 清理残留 act 进程 (PID $($oldAct.Id)) ..." -ForegroundColor Yellow
    $oldAct | Stop-Process -Force
    Start-Sleep 2
}

# ── 3. 生成临时 actrc ────────────────────────────
$tmpActrc = New-TemporaryFile
@"
-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest
-P ubuntu-22.04=ghcr.io/catthehacker/ubuntu:act-22.04
--artifact-server-path /tmp/artifacts
--no-cache-server
--env HTTP_PROXY=http://${PROXY_HOST}:${PROXY_PORT}
--env HTTPS_PROXY=http://${PROXY_HOST}:${PROXY_PORT}
--env NO_PROXY=localhost,127.0.0.1,.local,${PROXY_HOST}
--env NODE_TLS_REJECT_UNAUTHORIZED=0
--env PIP_CERT=/etc/ssl/certs/ca-certificates.crt
--env REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
"@ | Set-Content -Path $tmpActrc.FullName -Encoding UTF8

Write-Host "📄 使用临时配置: $($tmpActrc.FullName)" -ForegroundColor Cyan

# ── 4. 执行 act ──────────────────────────────────
try {
    if ($PassthruArgs.Count -eq 0) {
        Write-Host "❌ 请指定要运行的 job，例如: -j test -W .github/workflows/ci.yml" -ForegroundColor Red
        Write-Host "   查看所有可用的 job： --list" -ForegroundColor Gray
        exit 1
    }

    $actArgs = @("--actrc", $tmpActrc.FullName) + $PassthruArgs
    Write-Host "🚀 act $($PassthruArgs -join ' ')" -ForegroundColor Cyan
    Write-Host ""

    & act @actArgs
    $exitCode = $LASTEXITCODE
} finally {
    if ($tmpActrc -and (Test-Path $tmpActrc.FullName)) {
        Remove-Item -Path $tmpActrc.FullName -Force -ErrorAction SilentlyContinue
    }
}

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 全部通过" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 失败 (exit code: $exitCode)" -ForegroundColor Red
}
exit $exitCode
