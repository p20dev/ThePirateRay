[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$CacheRoot,
    [switch]$BuildWindowsBundle
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$manifestPath = Join-Path $repositoryRoot "upstreams\rayforge.json"
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json

if (-not $CacheRoot) {
    $CacheRoot = Join-Path $repositoryRoot ".build\upstreams"
}

$shortCommit = $manifest.commit.Substring(0, 12)
$checkout = Join-Path $CacheRoot "rayforge-$shortCommit"

if (-not (Test-Path -LiteralPath $checkout)) {
    if (-not $PSCmdlet.ShouldProcess($checkout, "Clone pinned Rayforge source")) {
        return
    }

    New-Item -ItemType Directory -Force -Path $CacheRoot | Out-Null
    & git clone --filter=blob:none --no-checkout $manifest.repository $checkout
    if ($LASTEXITCODE -ne 0) {
        throw "Rayforge clone failed with exit code $LASTEXITCODE"
    }
}

if (-not (Test-Path -LiteralPath (Join-Path $checkout ".git"))) {
    throw "Existing cache path is not a Git checkout: $checkout"
}

$currentCommit = (& git -C $checkout rev-parse HEAD 2>$null)
if ($LASTEXITCODE -ne 0 -or $currentCommit -ne $manifest.commit) {
    if (-not $PSCmdlet.ShouldProcess($checkout, "Fetch and check out pinned commit $($manifest.commit)")) {
        return
    }

    & git -C $checkout fetch --depth 1 origin $manifest.commit
    if ($LASTEXITCODE -ne 0) {
        throw "Rayforge fetch failed with exit code $LASTEXITCODE"
    }
    & git -C $checkout checkout --detach $manifest.commit
    if ($LASTEXITCODE -ne 0) {
        throw "Rayforge checkout failed with exit code $LASTEXITCODE"
    }
}

$verifiedCommit = (& git -C $checkout rev-parse HEAD).Trim()
if ($verifiedCommit -ne $manifest.commit) {
    throw "Rayforge pin mismatch: expected $($manifest.commit), got $verifiedCommit"
}

Write-Output "Rayforge source ready at $checkout"
Write-Output "Verified commit: $verifiedCommit"

if (-not $BuildWindowsBundle) {
    Write-Output "No dependencies were installed and no build was started."
    return
}

$bash = "C:\msys64\usr\bin\bash.exe"
if (-not (Test-Path -LiteralPath $bash)) {
    throw "MSYS2 is required for the upstream Windows build. Install it explicitly before using build flags."
}

$msysCheckout = (& $bash -lc "cygpath -u '$checkout'").Trim()

if ($BuildWindowsBundle) {
    $environmentFile = Join-Path $checkout ".msys2_env"
    if (-not (Test-Path -LiteralPath $environmentFile)) {
        throw "A reviewed Rayforge Windows build runtime is not prepared. No dependencies were installed."
    }

    if ($PSCmdlet.ShouldProcess($checkout, "Build pinned Rayforge Windows bundle")) {
        & $bash -lc "cd '$msysCheckout' && bash scripts/win/win_build.sh 'pirateray-$shortCommit'"
        if ($LASTEXITCODE -ne 0) {
            throw "Rayforge Windows build failed with exit code $LASTEXITCODE"
        }
    }
}
