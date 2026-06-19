# SPDX-License-Identifier: AGPL-3.0
<#
.SYNOPSIS
    act wrapper — 自动检测代理端口 + 避免端口冲突，在 Docker 容器中运行 CI 测试。

.DESCRIPTION
    GitHub Actions 本地运行器。自动扫描 host.docker.internal 上的代理端口，
    以 --env 参数传给 act 并执行。

    用法:
      .\scripts\act.ps1 -- -j test -W .github/workflows/ci.yml
      .\scripts\act.ps1 -- -j test -W .github/workflows/framework-ci.yml
      .\scripts\act.ps1 -- -j test -W .github/workflows/web-ci.yml
      .\scripts\act.ps1 -- --list

    注意：参数前的 -- 是必需的（避免 PowerShell 误解析 act 的 -W / -j 等参数）。
#>

$REPO_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

# ── 1. 清理旧 act 进程（避免端口 34567 冲突） ─────
$oldAct = Get-Process -Name "act" -ErrorAction SilentlyContinue
if ($oldAct) {
    Write-Host "🧹 清理残留 act 进程 (PID $($oldAct.Id)) ..." -ForegroundColor Yellow
    $oldAct | Stop-Process -Force
    Start-Sleep 2
}

# ── 2. 自动检测代理端口 ──────────────────────────
$PROXY_HOST = "host.docker.internal"
$PROXY_PORT = $null
$COMMON_PORTS = @(6518, 7890, 7891, 1080, 1081, 10809, 3128, 8080, 8118, 9090, 8899)

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
    # 也扫描 localhost（可能代理只绑 127.0.0.1）
    Write-Host "  ⚠️  host.docker.internal 无响应，扫描 localhost ..." -ForegroundColor Yellow
    foreach ($port in $COMMON_PORTS) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $async = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
            $wait = $async.AsyncWaitHandle.WaitOne(300, $false)
            if ($wait -and $tcp.Connected) {
                $tcp.EndConnect($async)
                $PROXY_PORT = $port
                $tcp.Dispose()
                break
            }
            $tcp.Dispose()
        } catch { continue }
    }
    if ($PROXY_PORT) {
        Write-Host "  ✅ 检测到本地代理: 127.0.0.1:$PROXY_PORT（尝试 host.docker.internal）" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  未检测到代理端口。Docker 容器将无法访问外网，拉取依赖会失败。"
        Write-Host "  请启动你的代理工具（Clash/V2Ray/AtlasVPN 等），或设置系统 HTTP_PROXY 后再试。" -ForegroundColor Yellow
        Write-Host "  如果确认代理已运行，可手动指定：`$env:HTTP_PROXY='http://host.docker.internal:端口'" -ForegroundColor Gray
        $PROXY_PORT = $null
    }
}

# ── 3. 如果没检测到代理，用无代理模式运行 ──────────
if (-not $PROXY_PORT) {
    Write-Host "`n⚠️  无代理，Docker 内的网络请求将直连（可能超时）" -ForegroundColor Yellow
    $actEnvArgs = @(
        "--env", "NODE_TLS_REJECT_UNAUTHORIZED=0",
        "--env", "PIP_CERT=/etc/ssl/certs/ca-certificates.crt",
        "--env", "REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt"
    )
} else {
    Write-Host "  代理: $PROXY_HOST`:$PROXY_PORT" -ForegroundColor Gray
    $actEnvArgs = @(
        "--env", "HTTP_PROXY=http://${PROXY_HOST}:${PROXY_PORT}",
        "--env", "HTTPS_PROXY=http://${PROXY_HOST}:${PROXY_PORT}",
        "--env", "NO_PROXY=localhost,127.0.0.1,.local,${PROXY_HOST}",
        "--env", "NODE_TLS_REJECT_UNAUTHORIZED=0",
        "--env", "PIP_CERT=/etc/ssl/certs/ca-certificates.crt",
        "--env", "REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt"
    )
}

# ── 4. 收集透传参数 ──────────────────────────────
$passthruArgs = @()
$afterDoubleDash = $false
foreach ($arg in $args) {
    if ($arg -eq "--") { $afterDoubleDash = $true; continue }
    if ($afterDoubleDash) { $passthruArgs += $arg }
}

if ($passthruArgs.Count -eq 0) {
    $passthruArgs = $args
}

if ($passthruArgs.Count -eq 0) {
    Write-Host "❌ 请指定要运行的 job，例如：.\scripts\act.ps1 -- -j test -W .github/workflows/ci.yml" -ForegroundColor Red
    Write-Host "   查看所有 job：.\scripts\act.ps1 -- --list" -ForegroundColor Gray
    exit 1
}

# ── 5. 执行 act ──────────────────────────────────
$allArgs = $actEnvArgs + $passthruArgs
Write-Host "🚀 act $($passthruArgs -join ' ')" -ForegroundColor Cyan
Write-Host "  代理: $PROXY_HOST`:$PROXY_PORT" -ForegroundColor Gray
Write-Host ""

& act @allArgs
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host ""
    Write-Host "✅ 全部通过" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ 失败 (exit code: $exitCode)" -ForegroundColor Red
}
exit $exitCode
