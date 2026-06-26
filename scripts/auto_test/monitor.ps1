# 监控脚本：每5分钟检查一次 done.md
$projectRoot = "E:\endfield_damage_calculator"
$doneFile = "$projectRoot\.trae\plans\done.md"
$screenshotDir = "$projectRoot\scripts\auto_test\screenshots"
$logFile = "$screenshotDir\monitor.log"

# 确保目录存在
New-Item -ItemType Directory -Force -Path $screenshotDir | Out-Null

function Log($msg) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $msg" | Out-File -Append -FilePath $logFile -Encoding utf8
    Write-Host "$timestamp - $msg"
}

Log "Monitor started. Checking every 5 minutes..."

while ($true) {
    if (Test-Path $doneFile) {
        Log "DONE FILE FOUND! Reading..."
        $content = Get-Content $doneFile -Raw -Encoding utf8
        Log "Content: $content"

        # 检查截图目录
        $screenshots = Get-ChildItem -Path $screenshotDir -Recurse -Include "*.png"
        Log "Screenshots found: $($screenshots.Count)"

        Log "Task completed. Exiting monitor."
        exit 0
    } else {
        Log "Waiting... (done.md not found yet)"
    }

    Start-Sleep -Seconds 300  # 5分钟
}
