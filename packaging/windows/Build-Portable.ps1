# Build a versioned, source-visible portable Windows package without a runtime download.
param(
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$Wheelhouse,
    [Parameter(Mandatory = $true)][string]$CommitSha
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$out = [System.IO.Path]::GetFullPath($OutputDirectory)
$stage = Join-Path $out 'staging'
$sourceZip = Join-Path $out 'tracked-source.zip'

$pkg = Get-Content (Join-Path $repo 'Noemorph\frontend\package.json') -Raw | ConvertFrom-Json
$version = [string]$pkg.version
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw "Unexpected package version: $version" }
if ($CommitSha -notmatch '^[a-fA-F0-9]{40}$') { throw 'Expected complete Git commit SHA.' }
if (-not (Test-Path (Join-Path $repo 'Noemorph\frontend\dist\index.html'))) {
    throw 'Build the frontend before packaging.'
}
if (-not (Test-Path $Wheelhouse)) { throw "Missing wheelhouse: $Wheelhouse" }

New-Item -ItemType Directory -Force -Path $out | Out-Null
if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

Push-Location $repo
try {
    & git archive --format=zip --output=$sourceZip HEAD Noemorph README.md LICENSE CONTRIBUTING.md THIRD_PARTY.md
    if ($LASTEXITCODE -ne 0) { throw 'Git archive of tracked Noemorph source failed.' }
}
finally { Pop-Location }

Expand-Archive -LiteralPath $sourceZip -DestinationPath $stage -Force
Remove-Item -LiteralPath $sourceZip -Force
Copy-Item -LiteralPath (Join-Path $repo 'Noemorph\frontend\dist') -Destination (Join-Path $stage 'Noemorph\frontend\dist') -Recurse -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'Start-Noemorph.ps1') -Destination (Join-Path $stage 'Start-Noemorph.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'README.md') -Destination (Join-Path $stage 'WINDOWS-PORTABLE-README.md')

$wheels = Join-Path $stage 'wheelhouse'
New-Item -ItemType Directory -Force -Path $wheels | Out-Null
$downloads = @(Get-ChildItem -LiteralPath $Wheelhouse -File -Filter '*.whl')
if ($downloads.Count -eq 0) { throw 'No wheels available for offline package.' }
foreach ($wheel in $downloads) { Copy-Item -LiteralPath $wheel.FullName -Destination $wheels }

$frontendIndex = Join-Path $stage 'Noemorph\frontend\dist\index.html'
$catalog = Join-Path $stage 'Noemorph\data\catalog.json'
if (-not (Test-Path $frontendIndex) -or -not (Test-Path $catalog)) {
    throw 'Missing required frontend or canonical catalog asset in release.'
}
$meta = [ordered]@{
    format = 'noemorph-windows-portable'
    version = $version
    commit = $CommitSha
    python = '3.14'
    platform = 'windows-x64'
    frontend_index_sha256 = (Get-FileHash $frontendIndex -Algorithm SHA256).Hash.ToLowerInvariant()
    catalog_sha256 = (Get-FileHash $catalog -Algorithm SHA256).Hash.ToLowerInvariant()
    wheels = @($downloads | Sort-Object Name | ForEach-Object {
        [ordered]@{
            file = $_.Name
            sha256 = (Get-FileHash (Join-Path $wheels $_.Name) -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    })
}
$meta | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath (Join-Path $stage 'release-manifest.json') -Encoding utf8
$shortSha = $CommitSha.Substring(0, 12).ToLowerInvariant()
$packageZip = Join-Path $out "Noemorph-Windows-v$version-$shortSha.zip"
if (Test-Path $packageZip) { Remove-Item $packageZip -Force }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $packageZip -CompressionLevel Optimal
if (-not (Test-Path $packageZip)) { throw 'Portable release ZIP was not created.' }
Write-Host "Portable Windows release ready: $packageZip"
