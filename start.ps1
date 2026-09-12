Param([switch]$Headless, [switch]$BackendOnly, [switch]$FrontendOnly, [switch]$NoBrowser)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
. "$PSScriptRoot/scripts/FleetStartMode.ps1"
$mode = Initialize-FleetStartMode -Headless:$Headless -BackendOnly:$BackendOnly -FrontendOnly:$FrontendOnly -NoBrowser:$NoBrowser
if ($mode.RunBackend) { Stop-FleetPortSquatters -Ports @(11974) -Label "rss-mcp" }
if ($mode.RunFrontend) { Stop-FleetPortSquatters -Ports @(11975) -Label "rss-mcp" }
if ($mode.RunBackend) {
    $be = Start-FleetDetachedShell -Label "rss-mcp-backend" -Exe "uv" -Args @("run", "python", "-m", "rss_mcp", "--serve") -WorkingDirectory $PSScriptRoot -WindowStyle $mode.WindowStyle
}
if ($mode.RunFrontend) {
    $fe = Start-FleetDetachedShell -Label "rss-mcp-frontend" -Exe "bun" -Args @("run", "dev", "--port", "11975") -WorkingDirectory "$PSScriptRoot/webapp" -WindowStyle $mode.WindowStyle
}
if (-not $mode.SkipBrowser) { Start-Process "http://127.0.0.1:11975" }
Write-Host "rss-mcp started. Backend 11974 Frontend 11975" -ForegroundColor Green
