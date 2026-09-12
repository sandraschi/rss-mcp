#Requires -Version 7.0
# mcpb-pack.ps1 - pack rss-mcp to .mcpb (MCPB only, no Tauri in v1)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$repo = "rss-mcp"
$sysPath = "assets/prompts/system.md"
$userPath = "assets/prompts/user.md"
$exPath = "assets/prompts/examples.json"
function Count-Words([string]$p) {
    $t = Get-Content -LiteralPath $p -Raw
    return ($t -split '\s+' | Where-Object { $_ -ne '' }).Count
}
$sysWords = Count-Words $sysPath
$userWords = Count-Words $userPath
$exCount = (Get-Content -LiteralPath $exPath -Raw | ConvertFrom-Json).Count
Write-Host "system.md words: $sysWords (need >=3000)"
Write-Host "user.md words: $userWords (need >=4000)"
Write-Host "examples.json objects: $exCount (need >=100)"
if ($sysWords -lt 3000) { throw "system.md too short" }
if ($userWords -lt 4000) { throw "user.md too short" }
if ($exCount -lt 100) { throw "examples.json too few" }
# wipe + recopy src -> mcpb/src so stale twin never ships
if (Test-Path "mcpb/src") { Remove-Item -Recurse -Force "mcpb/src" }
New-Item -ItemType Directory -Path "mcpb/src" -Force | Out-Null
Copy-Item -Recurse -Force "src/*" "mcpb/src/"
if (Test-Path "mcpb/src/__pycache__") { Remove-Item -Recurse -Force "mcpb/src/__pycache__" }
Write-Host "Fresh copy src -> mcpb/src done."
if (Get-Command mcpb -ErrorAction SilentlyContinue) {
    mcpb pack
} else {
    Write-Host "mcpb CLI not found - staging verified, skipping pack."
}
