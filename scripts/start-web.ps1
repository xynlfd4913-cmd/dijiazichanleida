param(
    [ValidateRange(1, 65535)]
    [int]$Port = 3000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WebRoot = Join-Path $ProjectRoot "apps\web"

if (-not (Test-Path -LiteralPath (Join-Path $WebRoot "node_modules"))) {
    throw "Frontend dependencies are missing. Run scripts/setup.ps1 first."
}

$PortInUse = $false
$Probe = [System.Net.Sockets.TcpClient]::new()
try {
    $ConnectTask = $Probe.ConnectAsync("127.0.0.1", $Port)
    $PortInUse = $ConnectTask.Wait(750) -and $Probe.Connected
} catch {
    $PortInUse = $false
} finally {
    $Probe.Dispose()
}

if ($PortInUse) {
    throw "Port $Port is already serving a local application. Open http://localhost:$Port if it is this project, or stop that server before starting another one."
}

Set-Location $WebRoot
Write-Host "Starting web app at http://localhost:$Port"
npm run dev -- --port $Port
