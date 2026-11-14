[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$bridgePath = Join-Path $taskRoot 'services\mcp_bridge.py'
$statusPath = Join-Path $taskRoot '.local\mcp-status.json'
if (Test-Path -LiteralPath $statusPath) {
    $status = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId = $($status.pid)" -ErrorAction SilentlyContinue
    if ($existing -and $existing.CommandLine.Replace('/', '\').Contains($bridgePath)) {
        Write-Output "El puente ya esta ejecutandose (PID $($status.pid))."
        return
    }
}
. (Join-Path $PSScriptRoot 'enter-idf.ps1')
$pythonPath = Join-Path $env:IDF_PYTHON_ENV_PATH 'Scripts\python.exe'
New-Item -ItemType Directory -Force -Path (Join-Path $taskRoot '.local') | Out-Null
$secureEndpoint = Read-Host 'Pega el endpoint MCP completo de XiaoZhi (entrada oculta)' -AsSecureString
$credential = [System.Net.NetworkCredential]::new('', $secureEndpoint)
$env:MCP_ENDPOINT = $credential.Password
try {
    Start-Process -FilePath $pythonPath -ArgumentList @('"' + $bridgePath + '"') -WindowStyle Hidden -WorkingDirectory $taskRoot -RedirectStandardOutput (Join-Path $taskRoot '.local\mcp-bridge.log') -RedirectStandardError (Join-Path $taskRoot '.local\mcp-bridge-error.log')
} finally {
    Remove-Item Env:MCP_ENDPOINT -ErrorAction SilentlyContinue
    $credential = $null
}
Write-Output 'Puente iniciado. Consulta .local/mcp-status.json y actualiza Endpoint Status en XiaoZhi.'
