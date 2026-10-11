# ==============================================================================
# InBoost LongRun Evaluation Runtime - Windows PowerShell Installer
# Privacy: Runs 100% locally on your machine. Does not transmit code externally.
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    InBoost LongRun Evaluation Runtime Installer (Windows)  " -ForegroundColor Cyan
Write-Host "    Privacy: InBoost LongRun выполняется локально           " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$InboostHome = Join-Path $HOME ".inboost"
$BinDir = Join-Path $InboostHome "bin"
if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetBin = Join-Path $BinDir "inboost-longrun.exe"
$SourceCandidate = Join-Path $ScriptDir "bin\inboost-longrun-windows-amd64.exe"

if (-not (Test-Path $SourceCandidate)) {
    $SourceCandidate = Join-Path $ScriptDir "bin\inboost-longrun.exe"
}

if (Test-Path $SourceCandidate) {
    Write-Host "Copying binary from $SourceCandidate to $TargetBin..." -ForegroundColor Green
    Copy-Item -Path $SourceCandidate -Destination $TargetBin -Force
} else {
    Write-Host "Downloading inboost-longrun-windows-x86_64.zip..." -ForegroundColor Yellow
    $TempZip = Join-Path $env:TEMP "inboost-longrun-windows.zip"
    $TempExtract = Join-Path $env:TEMP "inboost-extract"
    $DownloadUrl = "https://github.com/inboost-dev/inboost-ai-longrun-runtime/releases/latest/download/inboost-longrun-windows-x86_64.zip"

    Invoke-WebRequest -Uri $DownloadUrl -OutFile $TempZip
    Expand-Archive -Path $TempZip -DestinationPath $TempExtract -Force
    Copy-Item -Path (Join-Path $TempExtract "inboost-longrun.exe") -Destination $TargetBin -Force
    Remove-Item -Path $TempZip, $TempExtract -Recurse -Force -ErrorAction SilentlyContinue
}

# License installation
$LicCandidate = Join-Path $ScriptDir "inboost.lic"
$TargetLic = Join-Path $InboostHome "inboost.lic"
if (Test-Path $LicCandidate) {
    Copy-Item -Path $LicCandidate -Destination $TargetLic -Force
    Write-Host "License installed: $TargetLic" -ForegroundColor Green
}

# Update User PATH if needed
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($CurrentPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$BinDir", "User")
    $env:Path = "$env:Path;$BinDir"
    Write-Host "Added $BinDir to User PATH." -ForegroundColor Yellow
}

Write-Host "`nVerifying inboost-longrun installation:" -ForegroundColor Cyan
& "$TargetBin" version

Write-Host "`nInstallation successful!" -ForegroundColor Green
Write-Host "Binary:  $TargetBin"
Write-Host "License: $TargetLic"
Write-Host "Privacy: InBoost LongRun выполняется локально и не передает код вовне." -ForegroundColor Green
Write-Host "`nAI Agent Integration:"
Write-Host "  Cursor:       Add inboost-longrun to .cursor/mcp.json"
Write-Host "  Claude Code:  claude mcp add inboost-longrun -- inboost-longrun serve"
Write-Host "  Antigravity:  agy mcp add inboost-longrun inboost-longrun serve"
