$ErrorActionPreference = "Stop"

$RepoName = "kicad-ai-agent"
$Visibility = "public"
$Tag = "v0.2.0-beta.1"
$Root = Split-Path -Parent $PSScriptRoot
$Zip = Join-Path $Root "dist\kicad-ai-agent-beta-v0.2.0-beta.1.zip"
$Notes = Join-Path $Root "RELEASE_NOTES_zh-CN.md"

Push-Location $Root
try {
    gh auth status

    if (-not (Test-Path -LiteralPath $Zip)) {
        C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\package_beta.ps1")
    }

    $remote = git remote get-url origin 2>$null
    if (-not $remote) {
        gh repo create $RepoName --$Visibility --source . --remote origin --push --description "Windows KiCad AI Agent Beta with local side panel and CLI validation"
    } else {
        git push -u origin main
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
