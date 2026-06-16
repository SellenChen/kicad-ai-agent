$ErrorActionPreference = "Stop"

$RepoName = "kicad-ai-agent"
$Owner = "SellenChen"
$Visibility = "public"
$Tag = "v0.2.0-beta.1"
$Root = Split-Path -Parent $PSScriptRoot
$SafeRoot = ([System.IO.Path]::GetFullPath($Root)) -replace '\\','/'
$Zip = Join-Path $Root "dist\kicad-ai-agent-beta-v0.2.0-beta.1.zip"
$Notes = Join-Path $Root "RELEASE_NOTES_zh-CN.md"

Push-Location $Root
try {
    gh auth status

    if (-not (Test-Path -LiteralPath $Zip)) {
        C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\package_beta.ps1")
    }

    $remotes = git -c safe.directory="$SafeRoot" remote
    if ($remotes -notcontains "origin") {
        gh repo view "$Owner/$RepoName" 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) {
            gh repo create "$Owner/$RepoName" --$Visibility --description "Windows KiCad AI Agent Beta with local side panel and CLI validation"
        }
        git -c safe.directory="$SafeRoot" remote add origin "https://github.com/$Owner/$RepoName.git"
        git -c safe.directory="$SafeRoot" push -u origin main
    } else {
        git -c safe.directory="$SafeRoot" push -u origin main
    }

    $existing = gh release view $Tag 2>$null
    if ($LASTEXITCODE -eq 0) {
        gh release upload $Tag $Zip --clobber
    } else {
        gh release create $Tag $Zip --title "KiCad AI Agent $Tag" --notes-file $Notes --prerelease
    }
} finally {
    Pop-Location
}
