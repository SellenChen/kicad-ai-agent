$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Version = "v0.2.2-beta.1"
$Name = "kicad-ai-agent-beta-$Version"
$Dist = Join-Path $Root "dist"
$Zip = Join-Path $Dist "$Name.zip"

$ResolvedRoot = [System.IO.Path]::GetFullPath($Root)
$ResolvedDist = [System.IO.Path]::GetFullPath($Dist)
if (-not $ResolvedDist.StartsWith($ResolvedRoot)) {
    throw "Refusing to package outside project dist directory."
}

New-Item -ItemType Directory -Force -Path $Dist | Out-Null
if (Test-Path -LiteralPath $Zip) {
    Remove-Item -LiteralPath $Zip -Force
}

Push-Location $Root
try {
    git -c safe.directory="$($ResolvedRoot -replace '\\','/')" archive --format=zip --prefix="$Name/" --output="$Zip" HEAD
} finally {
    Pop-Location
}

[PSCustomObject]@{
    Version = $Version
    Package = $Zip
    SizeBytes = (Get-Item -LiteralPath $Zip).Length
}
