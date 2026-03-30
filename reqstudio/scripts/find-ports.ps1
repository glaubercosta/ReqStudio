# find-ports.ps1 — Detect available ports for ReqStudio services
# Usage: .\scripts\find-ports.ps1

function Test-PortAvailable {
    param([int]$Port)
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    }
    catch {
        return $false
    }
}

function Find-FreePort {
    param([int]$Default, [string]$Name)
    
    if (Test-PortAvailable -Port $Default) {
        Write-Host "$Name=$Default (default - available)"
    }
    else {
        for ($offset = 1; $offset -le 100; $offset++) {
            $candidate = $Default + $offset
            if (Test-PortAvailable -Port $candidate) {
                Write-Host "$Name=$candidate (default $Default is busy)"
                return
            }
        }
        Write-Host "$Name=NONE (no free port found near $Default)"
    }
}

Write-Host "`n🔍 Finding available ports for ReqStudio...`n"
Write-Host "# Add these to your .env file:"

Find-FreePort -Default 8000 -Name "API_PORT"
Find-FreePort -Default 5432 -Name "DB_PORT"
Find-FreePort -Default 5173 -Name "FRONTEND_PORT"

Write-Host "`n✅ Done."
