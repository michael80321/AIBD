# BD 攻堅名單 — 每日自動執行(Windows PowerShell)
# 由 Windows 工作排程器(schtasks)每日 08:00 呼叫,見 README.md

$ErrorActionPreference = "Stop"

# 專案根目錄(本腳本位於 scripts/ 下)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# 執行 /bd-daily,只允許必要工具
claude -p "/bd-daily" --allowedTools "WebSearch,WebFetch,Read,Write,Edit,Glob,Grep"

# 執行紀錄
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
"$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') bd-daily exit code: $LASTEXITCODE" |
    Out-File -Append -Encoding utf8 (Join-Path $LogDir "run-daily.log")

exit $LASTEXITCODE
