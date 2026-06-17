#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$PluginSource = Join-Path $RepoRoot "app\kicad_plugin\kicad_ai_agent_launcher"
$LauncherScript = Join-Path $RepoRoot "scripts\Start-KiCadAIAgent.ps1"

$script:Installations = @()
$script:DetectedTarget = ""
$script:DetectedKicadPath = ""

function Find-KiCadInstallations {
    $results = @()
    $appdataKicad = Join-Path $env:APPDATA "kicad"
    if (Test-Path -LiteralPath $appdataKicad) {
        foreach ($versionDir in Get-ChildItem -LiteralPath $appdataKicad -Directory | Sort-Object Name -Descending) {
            $pluginsDir = Join-Path $versionDir.FullName "scripting\plugins"
            if (Test-Path -LiteralPath $pluginsDir) {
                $kicadInstall = "C:\Program Files\KiCad\$($versionDir.Name)"
                $kicadExe = Join-Path $kicadInstall "bin\kicad.exe"
                $validKicad = Test-Path -LiteralPath $kicadExe
                $displayText = if ($validKicad) {
                    "KiCad $($versionDir.Name) [Verified] -- $pluginsDir"
                } else {
                    "KiCad $($versionDir.Name) [No binary] -- $pluginsDir"
                }
                $results += [PSCustomObject]@{
                    Version      = $versionDir.Name
                    PluginsPath  = $pluginsDir
                    InstallPath  = if ($validKicad) { $kicadInstall } else { "" }
                    Valid        = $validKicad
                    DisplayText  = $displayText
                }
            }
        }
    }
    if ($results.Count -eq 0) {
        $pfList = @()
        if ($env:ProgramFiles) { $pfList += $env:ProgramFiles }
        if (${env:ProgramFiles(x86)} -and ${env:ProgramFiles(x86)} -ne $env:ProgramFiles) {
            $pfList += ${env:ProgramFiles(x86)}
        }
        foreach ($pf in $pfList) {
            $kicadDir = Join-Path $pf "KiCad"
            if (Test-Path -LiteralPath $kicadDir) {
                foreach ($versionDir in Get-ChildItem -LiteralPath $kicadDir -Directory | Sort-Object Name -Descending) {
                    $kicadExe = Join-Path $versionDir.FullName "bin\kicad.exe"
                    if (Test-Path -LiteralPath $kicadExe) {
                        $pluginsDir = Join-Path $env:APPDATA "kicad\$($versionDir.Name)\scripting\plugins"
                        $displayText = "KiCad $($versionDir.Name) [Detected] -- $pluginsDir (auto-create)"
                        $results += [PSCustomObject]@{
                            Version      = $versionDir.Name
                            PluginsPath  = $pluginsDir
                            InstallPath  = $versionDir.FullName
                            Valid        = $true
                            DisplayText  = $displayText
                        }
                    }
                }
            }
        }
    }
    return $results
}

function Install-Plugin {
    param(
        [string]$TargetPluginsDir,
        [string]$KiCadInstallPath
    )
    try {
        $null = New-Item -ItemType Directory -Force -Path $TargetPluginsDir
        $targetPluginDir = Join-Path $TargetPluginsDir "kicad_ai_agent_launcher"
        if (Test-Path -LiteralPath $targetPluginDir) {
            Remove-Item -LiteralPath $targetPluginDir -Recurse -Force
        }
        Copy-Item -Path (Join-Path $PluginSource "*") -Destination $targetPluginDir -Recurse -Force
        $desktop = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktop "KiCad AI Agent.lnk"
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
        return @{ Ok = $true; Target = $targetPluginDir; Shortcut = $shortcutPath }
    }
    catch {
        return @{ Ok = $false; Error = $_.Exception.Message }
    }
}

function Show-InstallerGUI {
    $script:Installations = Find-KiCadInstallations

    $form = New-Object System.Windows.Forms.Form
    $form.Text = "KiCad AI Agent Plugin Installer"
    $form.Size = New-Object System.Drawing.Size(550, 520)
    $form.StartPosition = [System.Windows.Forms.FormStartPosition]::CenterScreen
    $form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $form.MaximizeBox = $false
    $form.BackColor = [System.Drawing.Color]::FromArgb(0x15, 0x19, 0x22)
    $form.ForeColor = [System.Drawing.Color]::FromArgb(0xe7, 0xea, 0xf0)
    $form.Font = New-Object System.Drawing.Font("Microsoft YaHei", 9)

    # Title
    $headerLabel = New-Object System.Windows.Forms.Label
    $headerLabel.Text = "KiCad AI Agent - Install Plugin"
    $headerLabel.Font = New-Object System.Drawing.Font("Microsoft YaHei", 14, [System.Drawing.FontStyle]::Bold)
    $headerLabel.Size = New-Object System.Drawing.Size(510, 36)
    $headerLabel.Location = New-Object System.Drawing.Point(18, 14)
    $headerLabel.ForeColor = [System.Drawing.Color]::FromArgb(0xe7, 0xea, 0xf0)
    $form.Controls.Add($headerLabel)

    $subtitleLabel = New-Object System.Windows.Forms.Label
    $subtitleLabel.Text = "Install the plugin into KiCad scripting directory. After install, access via Tools > KiCad AI Agent in PCB Editor."
    $subtitleLabel.Size = New-Object System.Drawing.Size(510, 32)
    $subtitleLabel.Location = New-Object System.Drawing.Point(18, 50)
    $subtitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $form.Controls.Add($subtitleLabel)

    # Detection status
    $detectedLabel = New-Object System.Windows.Forms.Label
    if ($script:Installations.Count -gt 0) {
        $detectedLabel.Text = "KiCad installations detected. Select target plugins directory:"
    } else {
        $detectedLabel.Text = "No KiCad installation auto-detected. Use [Browse...] to manually select your scripting/plugins folder."
    }
    $detectedLabel.Size = New-Object System.Drawing.Size(510, 32)
    $detectedLabel.Location = New-Object System.Drawing.Point(18, 88)
    $detectedLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $form.Controls.Add($detectedLabel)

    $listBox = New-Object System.Windows.Forms.ListBox
    $listBox.Size = New-Object System.Drawing.Size(510, 140)
    $listBox.Location = New-Object System.Drawing.Point(18, 124)
    $listBox.BackColor = [System.Drawing.Color]::FromArgb(0x1b, 0x20, 0x2b)
    $listBox.ForeColor = [System.Drawing.Color]::FromArgb(0xe7, 0xea, 0xf0)
    $listBox.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
    $listBox.Font = New-Object System.Drawing.Font("Consolas", 9)
    $form.Controls.Add($listBox)

    foreach ($inst in $script:Installations) {
        $index = $listBox.Items.Add($inst.DisplayText)
        if ($inst.Valid) {
            $listBox.SelectedIndex = $index
            $script:DetectedTarget = $inst.PluginsPath
            $script:DetectedKicadPath = $inst.InstallPath
        }
    }
    if ($listBox.SelectedIndex -lt 0 -and $listBox.Items.Count -gt 0) {
        $listBox.SelectedIndex = 0
        $script:DetectedTarget = $script:Installations[0].PluginsPath
        $script:DetectedKicadPath = $script:Installations[0].InstallPath
    }

    $pathGroup = New-Object System.Windows.Forms.GroupBox
    $pathGroup.Text = "Target Install Path"
    $pathGroup.Size = New-Object System.Drawing.Size(510, 50)
    $pathGroup.Location = New-Object System.Drawing.Point(18, 274)
    $pathGroup.BackColor = [System.Drawing.Color]::FromArgb(0x15, 0x19, 0x22)
    $pathGroup.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $form.Controls.Add($pathGroup)

    $selectedPathLabel = New-Object System.Windows.Forms.Label
    $selectedPathLabel.Text = if ($script:DetectedTarget) { $script:DetectedTarget } else { "(not selected)" }
    $selectedPathLabel.Size = New-Object System.Drawing.Size(490, 22)
    $selectedPathLabel.Location = New-Object System.Drawing.Point(8, 22)
    $selectedPathLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x4c, 0xc7, 0xb0)
    $selectedPathLabel.AutoEllipsis = $true
    $pathGroup.Controls.Add($selectedPathLabel)

    $browseButton = New-Object System.Windows.Forms.Button
    $browseButton.Text = "Browse..."
    $browseButton.Size = New-Object System.Drawing.Size(130, 32)
    $browseButton.Location = New-Object System.Drawing.Point(18, 336)
    $browseButton.BackColor = [System.Drawing.Color]::FromArgb(0x1b, 0x20, 0x2b)
    $browseButton.ForeColor = [System.Drawing.Color]::FromArgb(0xe7, 0xea, 0xf0)
    $browseButton.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $browseButton.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(0x2a, 0x31, 0x41)
    $form.Controls.Add($browseButton)

    $checkbox = New-Object System.Windows.Forms.CheckBox
    $checkbox.Text = "Create desktop shortcut (KiCad AI Agent.lnk)"
    $checkbox.Checked = $true
    $checkbox.Size = New-Object System.Drawing.Size(330, 24)
    $checkbox.Location = New-Object System.Drawing.Point(160, 340)
    $checkbox.BackColor = [System.Drawing.Color]::FromArgb(0x15, 0x19, 0x22)
    $checkbox.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $checkbox.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $form.Controls.Add($checkbox)

    $installButton = New-Object System.Windows.Forms.Button
    $installButton.Text = "Install"
    $installButton.Size = New-Object System.Drawing.Size(130, 38)
    $installButton.Location = New-Object System.Drawing.Point(18, 380)
    $installButton.BackColor = [System.Drawing.Color]::FromArgb(0x27, 0xa5, 0x8f)
    $installButton.ForeColor = [System.Drawing.Color]::FromArgb(0x04, 0x11, 0x0e)
    $installButton.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
    $installButton.FlatAppearance.BorderColor = [System.Drawing.Color]::FromArgb(0x27, 0xa5, 0x8f)
    $installButton.Font = New-Object System.Drawing.Font("Microsoft YaHei", 10, [System.Drawing.FontStyle]::Bold)
    $form.Controls.Add($installButton)

    $statusLabel = New-Object System.Windows.Forms.Label
    $statusLabel.Text = "Ready"
    $statusLabel.Size = New-Object System.Drawing.Size(510, 20)
    $statusLabel.Location = New-Object System.Drawing.Point(18, 432)
    $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
    $form.Controls.Add($statusLabel)

    $footerLabel = New-Object System.Windows.Forms.Label
    $footerLabel.Text = "After install, restart KiCad PCB Editor. Access via Tools > KiCad AI Agent."
    $footerLabel.Size = New-Object System.Drawing.Size(510, 20)
    $footerLabel.Location = New-Object System.Drawing.Point(18, 456)
    $footerLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x6a, 0x74, 0x82)
    $footerLabel.Font = New-Object System.Drawing.Font("Microsoft YaHei", 8)
    $form.Controls.Add($footerLabel)

    $listBox.Add_SelectedIndexChanged({
        if ($listBox.SelectedIndex -ge 0 -and $listBox.SelectedIndex -lt $script:Installations.Count) {
            $script:DetectedTarget = $script:Installations[$listBox.SelectedIndex].PluginsPath
            $script:DetectedKicadPath = $script:Installations[$listBox.SelectedIndex].InstallPath
            $selectedPathLabel.Text = $script:DetectedTarget
        }
    })

    $browseButton.Add_Click({
        $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
        $dialog.Description = "Select KiCad scripting/plugins directory"
        if ($script:DetectedTarget) {
            $dialog.SelectedPath = $script:DetectedTarget
        }
        if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            $script:DetectedTarget = $dialog.SelectedPath
            $script:DetectedKicadPath = ""
            $selectedPathLabel.Text = $script:DetectedTarget
            $listBox.ClearSelected()
            $statusLabel.Text = "Manual path selected."
            $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
        }
    })

    $installButton.Add_Click({
        $target = $script:DetectedTarget
        $kicadPath = $script:DetectedKicadPath
        if (-not $target) {
            $statusLabel.Text = "Please select a target directory first."
            $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0xff, 0x6b, 0x6b)
            return
        }
        if (-not (Test-Path -LiteralPath $PluginSource -PathType Container)) {
            $statusLabel.Text = "Plugin source not found. Check repository integrity."
            $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0xff, 0x6b, 0x6b)
            return
        }
        $installButton.Enabled = $false
        $statusLabel.Text = "Installing..."
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x9a, 0xa4, 0xb2)
        [System.Windows.Forms.Application]::DoEvents()

        $result = Install-Plugin -TargetPluginsDir $target -KiCadInstallPath $kicadPath

        if ($result.Ok) {
            $statusLabel.Text = "Install OK -> $($result.Target)"
            $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0x4c, 0xc7, 0xb0)
            if ($result.Shortcut) {
                $statusLabel.Text += " | Desktop shortcut created."
            }
        } else {
            $statusLabel.Text = "Install FAILED: $($result.Error)"
            $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(0xff, 0x6b, 0x6b)
        }
        $installButton.Enabled = $true
        [System.Windows.Forms.Application]::DoEvents()
    })

    [System.Windows.Forms.Application]::Run($form)
}

if (-not (Test-Path -LiteralPath $PluginSource -PathType Container)) {
    Write-Host "ERROR: Plugin source directory not found: $PluginSource" -ForegroundColor Red
    Write-Host "Run this script from within the kicad-ai-agent repository." -ForegroundColor Yellow
    exit 1
}

Show-InstallerGUI
