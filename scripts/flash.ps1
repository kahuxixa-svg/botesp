[CmdletBinding()]
param([string]$Port = 'COM3')

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'enter-idf.ps1')
$taskRoot = Split-Path -Parent $PSScriptRoot
$imagePath = Join-Path $taskRoot 'xiaozhi-esp32\build\merged-binary.bin'
$buildPath = Join-Path $taskRoot 'xiaozhi-esp32\build'
if (-not (Test-Path -LiteralPath $imagePath)) { throw 'Primero ejecuta scripts/build.ps1.' }
if (-not (Test-Path -LiteralPath (Join-Path $buildPath 'flash_args'))) { throw 'Falta build/flash_args.' }
$ErrorActionPreference = 'Continue'
Push-Location $buildPath
try {
    # Write only declared firmware partitions. A merged image fills NVS gaps
    # with FF and would erase the owner's saved Wi-Fi and activation identity.
    python -m esptool --chip esp32s3 --port $Port --baud 921600 write-flash '@flash_args'
    $flashExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
$ErrorActionPreference = 'Stop'
if ($flashExitCode -ne 0) { throw "La grabacion fallo: $flashExitCode" }
