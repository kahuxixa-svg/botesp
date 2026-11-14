[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$statusPath = Join-Path $taskRoot '.local\mcp-status.json'
$bridgePath = Join-Path $taskRoot 'services\mcp_bridge.py'
if (-not (Test-Path -LiteralPath $statusPath)) { Write-Output 'El puente no esta iniciado.'; return }
$status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
$bridgeProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($status.pid)" -ErrorAction SilentlyContinue
if ($bridgeProcess -and ($bridgeProcess.CommandLine.Replace('/', '\').Contains($bridgePath))) {
    Stop-Process -Id $status.pid
}
$status.connected = $false
$status.initialized = $false
$status | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
Write-Output 'Puente MCP detenido.'
