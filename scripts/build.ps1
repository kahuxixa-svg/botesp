[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'enter-idf.ps1')
$taskRoot = Split-Path -Parent $PSScriptRoot
python (Join-Path $PSScriptRoot 'prepare_troko_assets.py')
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron preparar las animaciones originales de Troko.' }
Push-Location (Join-Path $taskRoot 'xiaozhi-esp32')
try {
    # Keep Windows compiler command lines within CreateProcess limits.
    $env:CMAKE_NINJA_FORCE_RESPONSE_FILE = 'ON'
    $ErrorActionPreference = 'Continue'
    python scripts/build.py lilygo/troko-t-display-s3 --name troko-lilygo-t-display-s3-no-audio --language es-ES --wake-word disabled
    $buildExitCode = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($buildExitCode -ne 0) { throw "La compilacion fallo: $buildExitCode" }
} finally {
    Pop-Location
}
