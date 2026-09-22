$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Python environment is missing. Run scripts/setup.ps1 first."
}

Set-Location $ProjectRoot
& $VenvPython -m pytest

Set-Location (Join-Path $ProjectRoot "apps\web")
npm run build

