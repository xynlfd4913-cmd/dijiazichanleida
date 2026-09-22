$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = Join-Path $ProjectRoot ".venv"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$UsePyLauncher = $false

if (Test-Path -LiteralPath $BundledPython) {
    $BootstrapPython = $BundledPython
} else {
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        $BootstrapPython = $PyLauncher.Source
        $UsePyLauncher = $true
    } else {
        $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $PythonCommand) {
            throw "Python 3.12 is required. Install it from https://www.python.org/downloads/."
        }
        $BootstrapPython = $PythonCommand.Source
    }
}

Set-Location $ProjectRoot
if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
}
if (-not (Test-Path -LiteralPath $VenvPath)) {
    if ($UsePyLauncher) {
        & $BootstrapPython -3.12 -m venv $VenvPath
    } else {
        & $BootstrapPython -m venv $VenvPath
    }
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[dev]"

Set-Location (Join-Path $ProjectRoot "apps\web")
if (-not (Test-Path -LiteralPath ".env.local")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env.local"
}
if (Test-Path -LiteralPath "package-lock.json") {
    npm ci
} else {
    npm install
}

Write-Host "Setup complete. Start the API and web app in two terminals:"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\start-api.ps1"
Write-Host "  powershell -ExecutionPolicy Bypass -File .\scripts\start-web.ps1"
