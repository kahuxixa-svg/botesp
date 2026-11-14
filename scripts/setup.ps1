[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$idfPath = Join-Path $taskRoot '.tools\esp-idf'
$idfCommit = 'c1d1695f8f8310fa7e408ab97f95ab4e76b3be88'
$env:IDF_TOOLS_PATH = Join-Path $taskRoot '.tools\espressif'
$env:PYTHONUTF8 = '1'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
Get-Command git, python -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $taskRoot '.tools') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $taskRoot '.local') | Out-Null
# Windows PowerShell 5 wraps normal native stderr progress as ErrorRecords.
# Check exit codes explicitly for these native commands.
$ErrorActionPreference = 'Continue'

if (-not (Test-Path -LiteralPath $idfPath)) {
    git clone --branch release/v6.1 --filter=blob:none https://github.com/espressif/esp-idf.git $idfPath 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo descargar ESP-IDF.' }
    git -C $idfPath checkout --detach $idfCommit 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo seleccionar la revision de ESP-IDF.' }
}
$installedCommit = git -C $idfPath rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $installedCommit -ne $idfCommit) {
    throw "El SDK existente no coincide con $idfCommit. Usa una carpeta de clon nueva."
}
git -C $idfPath submodule update --init --recursive --depth 1 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron preparar los submodulos de ESP-IDF.' }
python (Join-Path $idfPath 'tools\idf_tools.py') install --targets=esp32s3 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las herramientas ESP32-S3.' }
python (Join-Path $idfPath 'tools\idf_tools.py') install-python-env 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar Python para ESP-IDF.' }
. (Join-Path $PSScriptRoot 'enter-idf.ps1')
$ErrorActionPreference = 'Continue'
python -m pip install -r (Join-Path $taskRoot 'requirements.txt') 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las herramientas del proyecto.' }
$ErrorActionPreference = 'Stop'
Write-Output 'Entorno preparado. Ejecuta .\scripts\build.ps1 para compilar.'
