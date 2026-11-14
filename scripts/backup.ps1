[CmdletBinding()]
param([string]$Port = 'COM3')

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'enter-idf.ps1')
$taskRoot = Split-Path -Parent $PSScriptRoot
$backupDirectory = Join-Path $taskRoot '.local\backups'
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$safePort = $Port -replace '[^a-zA-Z0-9_-]', '_'
$backupPath = Join-Path $backupDirectory "esp32s3-$safePort-$stamp.bin"
$ErrorActionPreference = 'Continue'
python -m esptool --chip esp32s3 --port $Port --baud 921600 read-flash 0 ALL $backupPath
$backupExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($backupExit -ne 0) { throw "No se pudo leer el respaldo: $backupExit" }
$backupFile = Get-Item -LiteralPath $backupPath
if ($backupFile.Length -ne 16777216) { throw 'El respaldo no tiene los 16 MB de la T-Display-S3.' }
$backupHash = (Get-FileHash -LiteralPath $backupPath -Algorithm SHA256).Hash.ToLowerInvariant()
@{ file = $backupFile.Name; bytes = $backupFile.Length; sha256 = $backupHash } |
    ConvertTo-Json | Set-Content -LiteralPath ($backupPath + '.json') -Encoding UTF8
Write-Output "Respaldo privado: $backupPath"
Write-Output "SHA256: $backupHash"
