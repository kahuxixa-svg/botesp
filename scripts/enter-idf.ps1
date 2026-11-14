$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$env:IDF_TOOLS_PATH = Join-Path $taskRoot '.tools\espressif'
$env:PYTHONUTF8 = '1'
$idfExport = Join-Path $taskRoot '.tools\esp-idf\export.ps1'
if (-not (Test-Path -LiteralPath $idfExport)) {
    throw 'Falta ESP-IDF en .tools/esp-idf. Consulta README.md.'
}
# Windows PowerShell 5 treats normal native stderr progress as an ErrorRecord.
# ESP-IDF's activation script reports progress there.
$savedErrorPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    $taskIdfOutput = . $idfExport 2>&1
    $taskIdfOutput | ForEach-Object { "$_" }
} finally {
    $ErrorActionPreference = $savedErrorPreference
}
if (-not $env:IDF_PYTHON_ENV_PATH) { throw 'No se pudo activar ESP-IDF.' }
