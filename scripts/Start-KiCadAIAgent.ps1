param(
    [string]$Project = "",
    [int]$Port = 8765
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$AppRoot = Join-Path $RepoRoot "app"
$RuntimeRoot = Join-Path $RepoRoot "work\stage2_runtime"
$LastProjectFile = Join-Path $RuntimeRoot "last_project.txt"
$KiCadPython = "C:\Program Files\KiCad\10.0\bin\python.exe"

function Get-AgentProject {
    param([string]$ExplicitProject)

    if ($ExplicitProject -and (Test-Path -LiteralPath $ExplicitProject)) {
        return (Resolve-Path -LiteralPath $ExplicitProject).Path
    }

    if (Test-Path -LiteralPath $LastProjectFile) {
        $last = (Get-Content -LiteralPath $LastProjectFile -Raw).Trim()
        if ($last -and (Test-Path -LiteralPath $last)) {
            return (Resolve-Path -LiteralPath $last).Path
        }
    }

    Add-Type -AssemblyName System.Windows.Forms
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.Title = "Select KiCad project or schematic"
    $dialog.Filter = "KiCad files (*.kicad_pro;*.kicad_sch)|*.kicad_pro;*.kicad_sch|All files (*.*)|*.*"
    $dialog.Multiselect = $false
    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw "No KiCad project selected."
    }
    return $dialog.FileName
}

function Test-AgentReady {
    param([int]$CandidatePort, [string]$ExpectedProject)

    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:${CandidatePort}/api/health" -TimeoutSec 1
        if (-not $health.ok) {
            return $false
        }
        $projectInfo = Invoke-RestMethod -Uri "http://127.0.0.1:${CandidatePort}/api/project" -TimeoutSec 1
        return ([System.IO.Path]::GetFullPath($projectInfo.project) -ieq [System.IO.Path]::GetFullPath($ExpectedProject))
    } catch {
        return $false
    }
}

function Get-UsablePort {
    param([int]$StartPort, [string]$ExpectedProject)

    for ($candidate = $StartPort; $candidate -lt ($StartPort + 20); $candidate++) {
        if (Test-AgentReady -CandidatePort $candidate -ExpectedProject $ExpectedProject) {
            return $candidate
        }
        try {
            $client = New-Object System.Net.Sockets.TcpClient
            $async = $client.BeginConnect("127.0.0.1", $candidate, $null, $null)
            $connected = $async.AsyncWaitHandle.WaitOne(150)
            $client.Close()
            if (-not $connected) {
                return $candidate
            }
        } catch {
            return $candidate
        }
    }
    throw "No available port found."
}

function Open-AgentWindow {
    param([string]$Url)

    $edgeCandidates = @()
    if (${env:ProgramFiles}) {
        $edgeCandidates += (Join-Path ${env:ProgramFiles} "Microsoft\Edge\Application\msedge.exe")
    }
    if (${env:ProgramFiles(x86)}) {
        $edgeCandidates += (Join-Path ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe")
    }
    foreach ($edge in $edgeCandidates) {
        if ($edge -and (Test-Path -LiteralPath $edge)) {
            Start-Process -FilePath $edge -ArgumentList @("--app=$Url", "--window-size=430,920", "--window-position=1480,40")
            return
        }
    }
    Start-Process $Url
}

$Project = Get-AgentProject -ExplicitProject $Project
New-Item -ItemType Directory -Force -Path $RuntimeRoot | Out-Null
Set-Content -LiteralPath $LastProjectFile -Value $Project -Encoding UTF8

if (-not (Test-Path -LiteralPath $KiCadPython)) {
    $KiCadPython = "python.exe"
}

$Port = Get-UsablePort -StartPort $Port -ExpectedProject $Project
$Url = "http://127.0.0.1:${Port}"

if (-not (Test-AgentReady -CandidatePort $Port -ExpectedProject $Project)) {
    $args = @(
        (Join-Path $AppRoot "run_agent.py"),
        "--project",
        $Project,
        "--host",
        "127.0.0.1",
        "--port",
        [string]$Port
    )
    Start-Process -FilePath $KiCadPython -ArgumentList $args -WorkingDirectory $AppRoot -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        if (Test-AgentReady -CandidatePort $Port -ExpectedProject $Project) {
            $ready = $true
            break
        }
        Start-Sleep -Milliseconds 250
    }
    if (-not $ready) {
        throw "KiCad AI Agent service startup timed out."
    }
}

Open-AgentWindow -Url $Url
