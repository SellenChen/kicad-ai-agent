#Requires -Version 5.1
$ErrorActionPreference = "Stop"

if ([System.Threading.Thread]::CurrentThread.GetApartmentState() -ne "STA") {
    $powershell = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
    Start-Process -FilePath $powershell -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-STA",
        "-File",
        "`"$PSCommandPath`""
    )
    exit
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$ScriptDir = Split-Path -Parent $PSCommandPath
$RepoRoot = Split-Path -Parent $ScriptDir
$PluginSource = Join-Path $RepoRoot "app\kicad_plugin\kicad_ai_agent_launcher"
$LauncherScript = Join-Path $RepoRoot "scripts\Start-KiCadAIAgent.ps1"

function Find-KiCadInstallations {
    $results = @()
    $appdataKicad = Join-Path $env:APPDATA "kicad"
    if (Test-Path -LiteralPath $appdataKicad) {
        foreach ($versionDir in Get-ChildItem -LiteralPath $appdataKicad -Directory | Sort-Object Name -Descending) {
            $pluginsDir = Join-Path $versionDir.FullName "scripting\plugins"
            $installDir = "C:\Program Files\KiCad\$($versionDir.Name)"
            $kicadExe = Join-Path $installDir "bin\kicad.exe"
            $valid = Test-Path -LiteralPath $kicadExe
            $results += [PSCustomObject]@{
                Version = $versionDir.Name
                PluginsPath = $pluginsDir
                InstallPath = if ($valid) { $installDir } else { "" }
                Valid = $valid
                DisplayText = "KiCad $($versionDir.Name) " + $(if ($valid) { "[Verified]" } else { "[Config only]" }) + " -- $pluginsDir"
            }
        }
    }

    $programFilesRoots = @()
    if ($env:ProgramFiles) { $programFilesRoots += $env:ProgramFiles }
    if (${env:ProgramFiles(x86)} -and ${env:ProgramFiles(x86)} -ne $env:ProgramFiles) {
        $programFilesRoots += ${env:ProgramFiles(x86)}
    }
    foreach ($pf in $programFilesRoots) {
        $kicadRoot = Join-Path $pf "KiCad"
        if (-not (Test-Path -LiteralPath $kicadRoot)) { continue }
        foreach ($versionDir in Get-ChildItem -LiteralPath $kicadRoot -Directory | Sort-Object Name -Descending) {
            $kicadExe = Join-Path $versionDir.FullName "bin\kicad.exe"
            if (-not (Test-Path -LiteralPath $kicadExe)) { continue }
            $pluginsDir = Join-Path $env:APPDATA "kicad\$($versionDir.Name)\scripting\plugins"
            if ($results | Where-Object { $_.PluginsPath -eq $pluginsDir }) { continue }
            $results += [PSCustomObject]@{
                Version = $versionDir.Name
                PluginsPath = $pluginsDir
                InstallPath = $versionDir.FullName
                Valid = $true
                DisplayText = "KiCad $($versionDir.Name) [Detected] -- $pluginsDir"
            }
        }
    }
    return @($results | Sort-Object Version -Descending)
}

function Get-KiCadPythonPath {
    param([string]$KiCadInstallPath)

    if ($KiCadInstallPath) {
        $candidate = Join-Path $KiCadInstallPath "bin\python.exe"
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return "C:\Program Files\KiCad\10.0\bin\python.exe"
}

function Write-PluginConfig {
    param(
        [string]$TargetPluginDir,
        [string]$RepoRoot,
        [string]$KiCadInstallPath
    )

    $pythonPath = Get-KiCadPythonPath -KiCadInstallPath $KiCadInstallPath
    $config = @"
from pathlib import Path


REPO_ROOT = Path(r"$RepoRoot")
APP_ROOT = REPO_ROOT / "app"
KICAD_PYTHON = Path(r"$pythonPath")
"@
    Set-Content -LiteralPath (Join-Path $TargetPluginDir "config.py") -Value $config -Encoding UTF8
}

function Install-Plugin {
    param(
        [string]$TargetPluginsDir,
        [string]$KiCadInstallPath,
        [bool]$CreateShortcut
    )

    if (-not (Test-Path -LiteralPath $PluginSource -PathType Container)) {
        throw "Plugin source directory not found: $PluginSource"
    }
    if (-not (Test-Path -LiteralPath $LauncherScript -PathType Leaf)) {
        throw "Launcher script not found: $LauncherScript"
    }

    New-Item -ItemType Directory -Force -Path $TargetPluginsDir | Out-Null
    $targetPluginDir = Join-Path $TargetPluginsDir "kicad_ai_agent_launcher"
    if (Test-Path -LiteralPath $targetPluginDir) {
        Remove-Item -LiteralPath $targetPluginDir -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $targetPluginDir | Out-Null
    Copy-Item -Path (Join-Path $PluginSource "*") -Destination $targetPluginDir -Recurse -Force
    Write-PluginConfig -TargetPluginDir $targetPluginDir -RepoRoot $RepoRoot -KiCadInstallPath $KiCadInstallPath

    $shortcutPath = ""
    if ($CreateShortcut) {
        $shortcutPath = Join-Path ([Environment]::GetFolderPath("Desktop")) "KiCad AI Agent.lnk"
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        $shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$LauncherScript`""
        $shortcut.WorkingDirectory = $RepoRoot
        $kicadIcon = Join-Path $KiCadInstallPath "bin\kicad.exe"
        if (Test-Path -LiteralPath $kicadIcon) {
            $shortcut.IconLocation = "$kicadIcon,0"
        }
        $shortcut.Description = "Launch KiCad AI Agent for the last KiCad project or select a project."
        $shortcut.Save()
    }

    return [PSCustomObject]@{
        Target = $targetPluginDir
        Shortcut = $shortcutPath
        Config = Join-Path $targetPluginDir "config.py"
    }
}

function Show-InstallerGUI {
    $installations = Find-KiCadInstallations

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "KiCad AI Agent Plugin Installer"
    $form.Size = New-Object System.Drawing.Size(600, 500)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $form.MaximizeBox = $false
    $form.BackColor = [System.Drawing.Color]::FromArgb(0x15, 0x19, 0x22)
    $form.ForeColor = [System.Drawing.Color]::FromArgb(0xe7, 0xea, 0xf0)
    $form.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 9)

    $title = New-Object System.Windows.Forms.Label
    $title.Text = "KiCad AI Agent - One Click Plugin Installer"
    $title.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 13, [System.Drawing.FontStyle]::Bold)
    $title.Location = New-Object System.Drawing.Point(18, 16)
    $title.Size = New-Object System.Drawing.Size(550, 30)
    $form.Controls.Add($title)

    $hint = New-Object System.Windows.Forms.Label
    $hint.Text = "Select KiCad scripting/plugins directory, then click Install. Restart KiCad PCB Editor after install."
    $hint.Location = New-Object System.Drawing.Point(18, 52)
    $hint.Size = New-Object System.Drawing.Size(550, 38)
    $hint.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $form.Controls.Add($hint)

    $listBox = New-Object System.Windows.Forms.ListBox
    $listBox.Location = New-Object System.Drawing.Point(18, 96)
    $listBox.Size = New-Object System.Drawing.Size(550, 150)
    $listBox.BackColor = [System.Drawing.Color]::FromArgb(0x1b, 0x20, 0x2b)
    $listBox.ForeColor = [System.Drawing.Color]::FromArgb(0xe7, 0xea, 0xf0)
    $listBox.Font = New-Object System.Drawing.Font("Consolas", 9)
    foreach ($inst in $installations) {
        [void]$listBox.Items.Add($inst.DisplayText)
    }
    if ($listBox.Items.Count -gt 0) { $listBox.SelectedIndex = 0 }
    $form.Controls.Add($listBox)

    $pathBox = New-Object System.Windows.Forms.TextBox
    $pathBox.Location = New-Object System.Drawing.Point(18, 264)
    $pathBox.Size = New-Object System.Drawing.Size(420, 25)
    $pathBox.BackColor = [System.Drawing.Color]::FromArgb(0x1b, 0x20, 0x2b)
    $pathBox.ForeColor = [System.Drawing.Color]::FromArgb(0x4c, 0xc7, 0xb0)
    $pathBox.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
    if ($installations.Count -gt 0) { $pathBox.Text = $installations[0].PluginsPath }
    $form.Controls.Add($pathBox)

    $browseButton = New-Object System.Windows.Forms.Button
    $browseButton.Text = "Browse..."
    $browseButton.Location = New-Object System.Drawing.Point(450, 260)
    $browseButton.Size = New-Object System.Drawing.Size(118, 32)
    $form.Controls.Add($browseButton)

    $shortcutCheck = New-Object System.Windows.Forms.CheckBox
    $shortcutCheck.Text = "Create desktop shortcut"
    $shortcutCheck.Checked = $true
    $shortcutCheck.Location = New-Object System.Drawing.Point(18, 306)
    $shortcutCheck.Size = New-Object System.Drawing.Size(250, 24)
    $shortcutCheck.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $shortcutCheck.BackColor = [System.Drawing.Color]::FromArgb(0x15, 0x19, 0x22)
    $form.Controls.Add($shortcutCheck)

    $installButton = New-Object System.Windows.Forms.Button
    $installButton.Text = "Install"
    $installButton.Location = New-Object System.Drawing.Point(18, 344)
    $installButton.Size = New-Object System.Drawing.Size(130, 38)
    $installButton.BackColor = [System.Drawing.Color]::FromArgb(0x27, 0xa5, 0x8f)
    $installButton.ForeColor = [System.Drawing.Color]::FromArgb(0x04, 0x11, 0x0e)
    $installButton.Font = New-Object System.Drawing.Font("Microsoft YaHei UI", 10, [System.Drawing.FontStyle]::Bold)
    $form.Controls.Add($installButton)

    $status = New-Object System.Windows.Forms.Label
    $status.Text = "Ready"
    $status.Location = New-Object System.Drawing.Point(18, 400)
    $status.Size = New-Object System.Drawing.Size(550, 44)
    $status.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $form.Controls.Add($status)

    $script:selectedInstallPath = if ($installations.Count -gt 0) { $installations[0].InstallPath } else { "" }

    $listBox.Add_SelectedIndexChanged({
        if ($listBox.SelectedIndex -ge 0 -and $listBox.SelectedIndex -lt $installations.Count) {
            $pathBox.Text = $installations[$listBox.SelectedIndex].PluginsPath
            $script:selectedInstallPath = $installations[$listBox.SelectedIndex].InstallPath
        }
    })

    $browseButton.Add_Click({
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "Select KiCad scripting/plugins directory"
        if ($pathBox.Text) { $dialog.SelectedPath = $pathBox.Text }
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $pathBox.Text = $dialog.SelectedPath
            $script:selectedInstallPath = ""
        }
    })

    $installButton.Add_Click({
        try {
            if (-not $pathBox.Text) { throw "Please select a target plugins directory." }
            $installButton.Enabled = $false
            $status.Text = "Installing..."
            [System.Windows.Forms.Application]::DoEvents()
            $result = Install-Plugin -TargetPluginsDir $pathBox.Text -KiCadInstallPath $script:selectedInstallPath -CreateShortcut $shortcutCheck.Checked
            $message = "Install OK: $($result.Target)"
            if ($result.Shortcut) { $message += "`nShortcut: $($result.Shortcut)" }
            $status.Text = $message
            $status.ForeColor = [System.Drawing.Color]::FromArgb(0x4c, 0xc7, 0xb0)
        } catch {
            $status.Text = "Install FAILED: $($_.Exception.Message)"
            $status.ForeColor = [System.Drawing.Color]::FromArgb(0xff, 0x6b, 0x6b)
        } finally {
            $installButton.Enabled = $true
            [System.Windows.Forms.Application]::DoEvents()
        }
    })

    [System.Windows.Forms.Application]::Run($form)
}

if (-not (Test-Path -LiteralPath $PluginSource -PathType Container)) {
    [System.Windows.Forms.MessageBox]::Show("Plugin source directory not found:`n$PluginSource", "KiCad AI Agent Installer", "OK", "Error") | Out-Null
    exit 1
}

Show-InstallerGUI
