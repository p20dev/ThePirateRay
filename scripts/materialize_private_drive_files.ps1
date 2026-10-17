[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

$ErrorActionPreference = 'Stop'
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$rootPrefix = $rootPath.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar

while (($line = [Console]::In.ReadLine()) -ne $null) {
    if ($line -eq '__END__') {
        break
    }
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }

    $item = $line | ConvertFrom-Json
    if (-not $item.relative_path -or -not $item.download_url) {
        throw 'Each input line must contain relative_path and download_url.'
    }

    $relativePath = $item.relative_path.Replace('/', [IO.Path]::DirectorySeparatorChar)
    $destination = [IO.Path]::GetFullPath((Join-Path $rootPath $relativePath))
    if (-not $destination.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing path outside acquisition root: $($item.relative_path)"
    }

    $parent = Split-Path -Parent $destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    Invoke-WebRequest -UseBasicParsing -Uri $item.download_url -OutFile $destination

    $actualSize = (Get-Item -LiteralPath $destination).Length
    if ($null -ne $item.expected_size -and $actualSize -ne [long]$item.expected_size) {
        throw "Size mismatch for $($item.relative_path): expected $($item.expected_size), got $actualSize"
    }

    if ($item.expected_sha256) {
        $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash.ToLowerInvariant()
        if ($actualHash -ne $item.expected_sha256.ToLowerInvariant()) {
            throw "SHA-256 mismatch for $($item.relative_path)"
        }
    }

    Write-Output ("OK`t{0}`t{1}" -f $actualSize, $item.relative_path)
}
