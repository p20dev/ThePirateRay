[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$CacheRoot,
    [string]$ArtifactRoot
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$upstreamManifest = Get-Content -Raw -LiteralPath (
    Join-Path $repositoryRoot "upstreams\rayforge.json"
) | ConvertFrom-Json
$shortCommit = $upstreamManifest.commit.Substring(0, 12)

if (-not $CacheRoot) {
    $CacheRoot = Join-Path $repositoryRoot ".build\upstreams"
}
if (-not $ArtifactRoot) {
    $ArtifactRoot = Join-Path $repositoryRoot ".build\artifacts"
}

$repositoryStatus = @(
    & git -C $repositoryRoot status --porcelain=v1 --untracked-files=all
)
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect The Pirate Ray checkout state"
}
if ($repositoryStatus.Count -gt 0) {
    throw "The Pirate Ray checkout must be clean before an external checkpoint build"
}
if (
    (Test-Path -LiteralPath $ArtifactRoot) -and
    @(Get-ChildItem -LiteralPath $ArtifactRoot -Force).Count -gt 0
) {
    throw "Artifact root must be absent or empty: $ArtifactRoot"
}

& (Join-Path $PSScriptRoot "prepare_rayforge_build.ps1") `
    -CacheRoot $CacheRoot `
    -AllowStagedPirateRayAddon
if ($LASTEXITCODE -ne 0) {
    throw "Pinned Rayforge source preparation failed"
}

$checkout = Join-Path $CacheRoot "rayforge-$shortCommit"
$verifiedCommit = (& git -C $checkout rev-parse HEAD).Trim()
if ($verifiedCommit -ne $upstreamManifest.commit) {
    throw "Rayforge pin mismatch before packaging"
}

$addonSource = Join-Path $repositoryRoot (
    "spikes\rayforge-jcz-no-device-addon"
)
$addonText = Get-ChildItem -LiteralPath $addonSource -Recurse -File |
    Where-Object { $_.Extension -eq ".py" } |
    ForEach-Object { Get-Content -Raw -LiteralPath $_.FullName }
$forbidden = @("import usb", "import serial", "import socket", "pyusb")
foreach ($needle in $forbidden) {
    if (($addonText -join "`n").ToLowerInvariant().Contains($needle)) {
        throw "No-device addon contains forbidden transport token: $needle"
    }
}

$addonDestination = Join-Path $checkout (
    "rayforge\builtin_addons\rayforge-addon-the-pirate-ray-jcz"
)
if ($PSCmdlet.ShouldProcess($addonDestination, "Stage no-device addon")) {
    $resolvedCheckout = [IO.Path]::GetFullPath($checkout).TrimEnd("\")
    $resolvedAddonDestination = [IO.Path]::GetFullPath($addonDestination)
    $expectedAddonDestination = Join-Path $resolvedCheckout (
        "rayforge\builtin_addons\rayforge-addon-the-pirate-ray-jcz"
    )
    if ($resolvedAddonDestination -ne $expectedAddonDestination) {
        throw "Refusing to replace an unexpected addon staging path"
    }
    if (Test-Path -LiteralPath $resolvedAddonDestination) {
        Remove-Item -LiteralPath $resolvedAddonDestination -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $addonDestination | Out-Null
    Copy-Item -Path (Join-Path $addonSource "*") `
        -Destination $addonDestination -Recurse -Force
}

$prepareArguments = @{
    CacheRoot = $CacheRoot
    BuildWindowsBundle = $true
    AllowStagedPirateRayAddon = $true
}
& (Join-Path $PSScriptRoot "prepare_rayforge_build.ps1") @prepareArguments
if ($LASTEXITCODE -ne 0) {
    throw "Pinned Rayforge Windows bundle build failed"
}

$bundleName = "rayforge-vpirateray-$shortCommit"
$bundleDirectory = Join-Path $checkout "dist\$bundleName"
$application = Join-Path $bundleDirectory "$bundleName.exe"
$installer = Join-Path $checkout "dist\$bundleName-installer.exe"
if (-not (Test-Path -LiteralPath $application)) {
    throw "Expected packaged application was not produced: $application"
}
if (-not (Test-Path -LiteralPath $installer)) {
    throw "Expected installer was not produced: $installer"
}

New-Item -ItemType Directory -Force -Path $ArtifactRoot | Out-Null
$artifactInstaller = Join-Path $ArtifactRoot (Split-Path -Leaf $installer)
if ($PSCmdlet.ShouldProcess($artifactInstaller, "Copy installer into checkpoint")) {
    Copy-Item -LiteralPath $installer -Destination $artifactInstaller -Force
}
$licenseDirectory = Join-Path $bundleDirectory "THIRD_PARTY_LICENSES"
$rayforgeLicense = Join-Path $checkout "LICENSE"
$normalizedLicense = [IO.File]::ReadAllText($rayforgeLicense).Replace("`r`n", "`n").Replace("`r", "`n")
$normalizedLicenseBytes = [Text.Encoding]::UTF8.GetBytes($normalizedLicense)
$rayforgeLicenseHash = [Convert]::ToHexString(
    [Security.Cryptography.SHA256]::HashData($normalizedLicenseBytes)
).ToLowerInvariant()
if ($rayforgeLicenseHash -ne $upstreamManifest.license_file.sha256_lf) {
    throw "Pinned Rayforge license hash mismatch"
}
$rayforgeNotice = Join-Path $repositoryRoot "third_party\licenses\Rayforge-LICENSE.txt"
$bundledRayforgeLicense = Join-Path $licenseDirectory "Rayforge-LICENSE.txt"
$sidecarRayforgeLicense = Join-Path $ArtifactRoot "Rayforge-LICENSE.txt"
if ($PSCmdlet.ShouldProcess($licenseDirectory, "Stage Rayforge license notice")) {
    New-Item -ItemType Directory -Force -Path $licenseDirectory | Out-Null
    Copy-Item -LiteralPath $rayforgeNotice -Destination $bundledRayforgeLicense -Force
    Copy-Item -LiteralPath $rayforgeNotice -Destination $sidecarRayforgeLicense -Force
}

$archive = Join-Path $ArtifactRoot "$bundleName.zip"
if ($PSCmdlet.ShouldProcess($archive, "Create portable checkpoint archive")) {
    Compress-Archive -LiteralPath $bundleDirectory -DestinationPath $archive -Force
}

$addonFiles = Get-ChildItem -LiteralPath $addonSource -Recurse -File |
    Sort-Object FullName |
    ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($addonSource.Length + 1).Replace("\", "/")
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
        }
    }
$result = [ordered]@{
    schema_version = 2
    checkpoint = "Rayforge Windows no-device bundle"
    rayforge_commit = $verifiedCommit
    addon = "the_pirate_ray_jcz"
    addon_packaged_root = "rayforge/builtin_addons/rayforge-addon-the-pirate-ray-jcz"
    addon_source_files = $addonFiles
    hardware_access = $false
    transport = $null
    bundle = [ordered]@{
        path = Split-Path -Leaf $archive
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
        bytes = (Get-Item -LiteralPath $archive).Length
    }
    installer = [ordered]@{
        path = Split-Path -Leaf $artifactInstaller
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $artifactInstaller).Hash.ToLowerInvariant()
        bytes = (Get-Item -LiteralPath $artifactInstaller).Length
    }
    license_files = @(
        [ordered]@{
            upstream = "Rayforge"
            path = Split-Path -Leaf $sidecarRayforgeLicense
            bundle_path = "THIRD_PARTY_LICENSES/Rayforge-LICENSE.txt"
            sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $sidecarRayforgeLicense).Hash.ToLowerInvariant()
            bytes = (Get-Item -LiteralPath $sidecarRayforgeLicense).Length
        }
    )
    manual_interaction_required = $true
}
$manifestPath = Join-Path $ArtifactRoot "rayforge-windows-checkpoint.json"
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "Checkpoint manifest: $manifestPath"
Write-Output "Transfer the complete artifact directory: $ArtifactRoot"
