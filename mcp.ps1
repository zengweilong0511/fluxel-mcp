# ApiCargo MCP Server 管理脚本
param([string]$Action = "status")

$Port = 3000

function Get-ServerProcess {
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction Stop
        return Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    } catch {
        return $null
    }
}

if ($Action -eq "status") {
    $p = Get-ServerProcess
    if ($p) {
        Write-Host "[OK] MCP Server running on port $Port (PID: $($p.Id))"
    } else {
        Write-Host "[STOPPED] MCP Server not running"
    }
}
elseif ($Action -eq "start") {
    $p = Get-ServerProcess
    if ($p) {
        Write-Host "[WARN] Already running (PID: $($p.Id))"
        exit
    }
    $env:APICARGO_API_BASE = "http://localhost:8082"
    $env:MCP_PORT = "$Port"
    Start-Process python -ArgumentList "server.py" -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
    Start-Sleep 2
    $p = Get-ServerProcess
    if ($p) { Write-Host "[OK] Started (PID: $($p.Id))" }
    else { Write-Host "[ERR] Failed to start" }
}
elseif ($Action -eq "stop") {
    $p = Get-ServerProcess
    if ($p) {
        Stop-Process -Id $p.Id -Force
        Write-Host "[OK] Stopped"
    } else {
        Write-Host "[WARN] Not running"
    }
}
elseif ($Action -eq "restart") {
    & $PSCommandPath -Action stop
    Start-Sleep 1
    & $PSCommandPath -Action start
}
