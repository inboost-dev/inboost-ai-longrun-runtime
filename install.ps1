# ==============================================================================
# InBoost LongRun Evaluation Runtime - Windows PowerShell Installer
# Privacy: Runs 100% locally on your machine. Does not transmit code externally.
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "    InBoost LongRun Evaluation Runtime Installer (Windows)  " -ForegroundColor Cyan
Write-Host "    Privacy: InBoost LongRun выполняется локально           " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Pre-flight dependency check for Local Offload
Write-Host "`nChecking system dependencies for Local Offload:" -ForegroundColor Cyan

$MandatoryTools = @("find", "grep", "diff", "patch", "git", "python3")
$MissingTools = @()

foreach ($tool in $MandatoryTools) {
    $found = $null
    $GitDirs = @(
        "$env:ProgramFiles\Git\usr\bin",
        "${env:ProgramFiles(x86)}\Git\usr\bin",
        "$env:LOCALAPPDATA\Programs\Git\usr\bin"
    )

    if ($tool -eq "python3") {
        $cmd = Get-Command "python3" -ErrorAction SilentlyContinue
        if (-not $cmd) { $cmd = Get-Command "python" -ErrorAction SilentlyContinue }
        if (-not $cmd) { $cmd = Get-Command "py" -ErrorAction SilentlyContinue }
        if ($cmd) { $found = $cmd.Source }
    } elseif ($tool -eq "find") {
        foreach ($gdir in $GitDirs) {
            $gitFind = Join-Path $gdir "find.exe"
            if (Test-Path $gitFind) {
                $found = $gitFind
                break
            }
        }
        if (-not $found) {
            $cmd = Get-Command "find" -ErrorAction SilentlyContinue
            if ($cmd -and $cmd.Source -notlike "*System32*") {
                $found = $cmd.Source
            }
        }
    } else {
        $cmd = Get-Command $tool -ErrorAction SilentlyContinue
        if ($cmd) {
            $found = $cmd.Source
        } else {
            foreach ($gdir in $GitDirs) {
                $candidate = Join-Path $gdir "$tool.exe"
                if (Test-Path $candidate) {
                    $found = $candidate
                    break
                }
            }
        }
    }

    if ($found) {
        Write-Host "  [✓] $tool ($found)" -ForegroundColor Green
    } else {
        Write-Host "  [✗] $tool (missing)" -ForegroundColor Red
        $MissingTools += $tool
    }
}

$RecommendedTools = @(
    @{ Name = "ast-grep"; Fallback = "sg" },
    @{ Name = "ruff"; Fallback = $null },
    @{ Name = "biome"; Fallback = $null },
    @{ Name = "docker"; Fallback = $null }
)

foreach ($rec in $RecommendedTools) {
    $recFound = $null
    $recCmd = Get-Command $rec.Name -ErrorAction SilentlyContinue
    if ($recCmd) {
        $recFound = $recCmd.Source
    } elseif ($rec.Fallback) {
        $fbCmd = Get-Command $rec.Fallback -ErrorAction SilentlyContinue
        if ($fbCmd) { $recFound = $fbCmd.Source }
    }

    if ($recFound) {
        Write-Host "  [✓] $($rec.Name) ($recFound) [recommended acceleration]" -ForegroundColor Green
    } else {
        Write-Host "  [○] $($rec.Name) (optional, recommended for <2ms local linting)" -ForegroundColor Yellow
    }
}

# Target AI Coding Agents & IDEs
Write-Host "`nChecking AI Coding Agents & IDEs:" -ForegroundColor Cyan
$AgentTools = @(
    @{ Name = "Claude Code"; Cmd = "claude"; Hint = "claude mcp add inboost-longrun -- inboost-longrun serve" },
    @{ Name = "Google Antigravity"; Cmd = "agy"; Hint = "agy mcp add inboost-longrun inboost-longrun serve" },
    @{ Name = "Cursor IDE"; Cmd = "cursor"; Hint = "inboost-longrun init (configures .cursor/mcp.json)" },
    @{ Name = "VS Code"; Cmd = "code"; Hint = "add to .vscode/mcp.json or workspace rules" }
)

foreach ($agent in $AgentTools) {
    $foundAgent = $null
    $agentCmd = Get-Command $agent.Cmd -ErrorAction SilentlyContinue
    if ($agentCmd) {
        $foundAgent = $agentCmd.Source
    } elseif ($agent.Cmd -eq "cursor" -and ((Test-Path ".cursor") -or (Test-Path "$HOME\.cursor"))) {
        $foundAgent = "detected via .cursor/ directory"
    }

    if ($foundAgent) {
        Write-Host "  [✓] $($agent.Name) ($foundAgent)" -ForegroundColor Green
        Write-Host "       Integration: $($agent.Hint)" -ForegroundColor DarkGray
    } else {
        Write-Host "  [○] $($agent.Name) (optional, not found in PATH)" -ForegroundColor Yellow
    }
}

if ($MissingTools.Count -gt 0) {
    Write-Host "`nError: Required tools missing for InBoost LongRun Local Offload: $($MissingTools -join ', ')" -ForegroundColor Red
    Write-Host "InBoost LongRun requires these tools locally to inspect outlines, calculate AST diffs, and filter test traces."
    Write-Host "Please install the missing tools before proceeding:"
    Write-Host "  winget install --id Git.Git (provides find, grep, diff, patch)" -ForegroundColor Cyan
    if ($MissingTools -contains "python3") {
        Write-Host "  winget install --id Python.Python.3.12" -ForegroundColor Cyan
    }

    if ($env:INBOOST_IGNORE_MISSING_DEPS -ne "1") {
        Write-Host "`nTo bypass this check (not recommended), set `$env:INBOOST_IGNORE_MISSING_DEPS='1'" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "`nProceeding anyway (INBOOST_IGNORE_MISSING_DEPS=1 is set)..." -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ All core offload tools verified.`n" -ForegroundColor Green
}

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
    $DownloadUrl = "https://github.com/inboost-dev/inboost-longrun/releases/latest/download/inboost-longrun-windows-x86_64.zip"

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
