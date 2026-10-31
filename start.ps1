Param([switch]$Headless, [switch]$BackendOnly, [switch]$FrontendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot/scripts/FleetStartMode.ps1"
$mode = Initialize-FleetStartMode -Headless:$Headless -BackendOnly:$BackendOnly -FrontendOnly:$FrontendOnly -NoBrowser:$NoBrowser
if ($mode.RunBackend) { Stop-FleetPortSquatters -Ports @(11974) -Label "rss-mcp" }
if ($mode.RunFrontend) { Stop-FleetPortSquatters -Ports @(11975) -Label "rss-mcp" }
# Fleet standard: NEVER naked uv/bun - Start-Process under start.bat (powershell -NoProfile)
# does not see user PATH additions, so bare names fail with "cannot find the file specified".
$UvExe = "C:\Users\sandr\.local\bin\uv.exe"
if (-not (Test-Path -LiteralPath $UvExe)) {
    $found = Get-Command uv.exe -ErrorAction SilentlyContinue
    if ($found) { $UvExe = $found.Source } else { $UvExe = "uv" }
}
$BunExe = "C:\Users\sandr\.bun\bin\bun.exe"
if (-not (Test-Path -LiteralPath $BunExe)) {
    $found = Get-Command bun.exe -ErrorAction SilentlyContinue
    if ($found) { $BunExe = $found.Source } else { $BunExe = "bun" }
}
if ($mode.RunBackend) {
    $be = Start-FleetDetachedShell -Label "rss-mcp-backend" -Exe $UvExe -Args @("run", "python", "-m", "rss_mcp", "--serve") -WorkingDirectory $PSScriptRoot -WindowStyle $mode.WindowStyle
}
if ($mode.RunFrontend) {
    $fe = Start-FleetDetachedShell -Label "rss-mcp-frontend" -Exe $BunExe -Args @("run", "dev", "--port", "11975") -WorkingDirectory "$PSScriptRoot/webapp" -WindowStyle $mode.WindowStyle
}
if ($mode.RunBackend -and (-not $mode.SkipBrowser)) {
    Write-Host "Waiting for backend readiness on 11974..." -NoNewline
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", 11974)
            $tcp.Close()
            $ready = $true
            break
        } catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if ($ready) { Write-Host " Ready." -ForegroundColor Green } else { Write-Host " Timed out waiting." -ForegroundColor Yellow }
}
if (-not $mode.SkipBrowser) { Start-Process "http://127.0.0.1:11975" }
Write-Host "rss-mcp started. Backend 11974 Frontend 11975" -ForegroundColor Green
