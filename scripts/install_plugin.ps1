$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $Root "app\kicad_plugin\kicad_ai_agent_launcher"
$LauncherScript = Join-Path $Root "scripts\Start-KiCadAIAgent.ps1"
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "KiCad AI Agent.lnk"

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Plugin source directory not found: $Source"
}

function Find-KiCadPluginsDir {
    $appdataKicad = Join-Path $env:APPDATA "kicad"
    if (Test-Path -LiteralPath $appdataKicad) {
        $candidates = @(Get-ChildItem -LiteralPath $appdataKicad -Directory |
            Where-Object { Test-Path (Join-Path $_.FullName "scripting\plugins") } |
            Sort-Object Name -Descending)
        foreach ($candidate in $candidates) {
            $kicadExe = "C:\Program Files\KiCad\$($candidate.Name)\bin\kicad.exe"
            if (Test-Path -LiteralPath $kicadExe) {
                return @{
                    PluginsDir = Join-Path $candidate.FullName "scripting\plugins"
                    KiCadPath  = "C:\Program Files\KiCad\$($candidate.Name)"
                }
            }
        }
        if ($candidates.Count -gt 0) {
            return @{
                PluginsDir = Join-Path $candidates[0].FullName "scripting\plugins"
                KiCadPath  = "C:\Program Files\KiCad\$($candidates[0].Name)"
            }
        }
    }

    $defaultPluginsDir = Join-Path $env:APPDATA "kicad\10.0\scripting\plugins"
    Write-Host "Auto-detection failed, falling back to default: $defaultPluginsDir" -ForegroundColor Yellow
    return @{
        PluginsDir = $defaultPluginsDir
        KiCadPath  = "C:\Program Files\KiCad\10.0"
    }
}

function Get-KiCadPythonPath {
    param([string]$KiCadPath)

    $candidate = Join-Path $KiCadPath "bin\python.exe"
    if (Test-Path -LiteralPath $candidate) {
        return $candidate
    }
    return "C:\Program Files\KiCad\10.0\bin\python.exe"
}

function Write-PluginConfig {
    param(
        [string]$TargetPluginDir,
        [string]$RepoRoot,
        [string]$KiCadPath
    )

    $config = @"
from pathlib import Path


REPO_ROOT = Path(r"$RepoRoot")
APP_ROOT = REPO_ROOT / "app"
KICAD_PYTHON = Path(r"$(Get-KiCadPythonPath -KiCadPath $KiCadPath)")
"@
    Set-Content -LiteralPath (Join-Path $TargetPluginDir "config.py") -Value $config -Encoding UTF8
}

$detected = Find-KiCadPluginsDir
$TargetPluginsDir = $detected.PluginsDir
$KiCadPath = $detected.KiCadPath
$Target = Join-Path $TargetPluginsDir "kicad_ai_agent_launcher"

Write-Host "KiCad path : $KiCadPath" -ForegroundColor Cyan
Write-Host "Plugins dir: $TargetPluginsDir" -ForegroundColor Cyan

if (Test-Path -LiteralPath $Target) {
    Remove-Item -LiteralPath $Target -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Path (Join-Path $Source "*") -Destination $Target -Recurse -Force
Write-PluginConfig -TargetPluginDir $Target -RepoRoot $Root -KiCadPath $KiCadPath

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($DesktopShortcut)
$shortcut.TargetPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherScript`""
$shortcut.WorkingDirectory = $Root
$kicadIcon = Join-Path $KiCadPath "bin\kicad.exe"
if (Test-Path -LiteralPath $kicadIcon) {
    $shortcut.IconLocation = "$kicadIcon,0"
}
$shortcut.Description = "Launch KiCad AI Agent for the last KiCad project or select a project."
$shortcut.Save()

[PSCustomObject]@{
    Installed   = $true
    Source      = $Source
    Target      = $Target
    KiCadPath   = $KiCadPath
    Shortcut    = $DesktopShortcut
    Hint        = "Restart KiCad PCB Editor, then click Tools > KiCad AI Agent. In Schematic Editor, use the desktop shortcut."
}
