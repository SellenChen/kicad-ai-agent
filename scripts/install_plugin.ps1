$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $Root "app\kicad_plugin\kicad_ai_agent_launcher"
$Target = Join-Path $env:APPDATA "kicad\10.0\scripting\plugins\kicad_ai_agent_launcher"
$LauncherScript = Join-Path $Root "scripts\Start-KiCadAIAgent.ps1"
$DesktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "KiCad AI Agent.lnk"

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Plugin source directory not found: $Source"
}

if (Test-Path -LiteralPath $Target) {
    Remove-Item -LiteralPath $Target -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null
Copy-Item -Path (Join-Path $Source "*") -Destination $Target -Recurse -Force

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($DesktopShortcut)
$shortcut.TargetPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherScript`""
$shortcut.WorkingDirectory = $Root
$shortcut.IconLocation = "C:\Program Files\KiCad\10.0\bin\kicad.exe,0"
$shortcut.Description = "Launch KiCad AI Agent for the last KiCad project or select a project."
$shortcut.Save()

[PSCustomObject]@{
    Installed = $true
    Source = $Source
    Target = $Target
    Shortcut = $DesktopShortcut
    Hint = "Restart KiCad PCB Editor, then click Tools > KiCad AI Agent. In Schematic Editor, use the desktop shortcut."
}
