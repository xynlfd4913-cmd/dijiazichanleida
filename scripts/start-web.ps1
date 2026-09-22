$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$WebRoot = Join-Path $ProjectRoot "apps\web"

if (-not (Test-Path -LiteralPath (Join-Path $WebRoot "node_modules"))) {
    throw "Frontend dependencies are missing. Run scripts/setup.ps1 first."
}

Set-Location $WebRoot
npm run dev

