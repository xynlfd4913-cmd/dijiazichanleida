$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$EnvFile = Join-Path $ProjectRoot ".env"

if (Test-Path -LiteralPath $EnvFile) {
    foreach ($Line in Get-Content -LiteralPath $EnvFile) {
        $Trimmed = $Line.Trim()
        if (-not $Trimmed -or $Trimmed.StartsWith("#") -or -not $Trimmed.Contains("=")) {
            continue
        }
        $Parts = $Trimmed.Split("=", 2)
        if (-not [Environment]::GetEnvironmentVariable($Parts[0], "Process")) {
            [Environment]::SetEnvironmentVariable($Parts[0], $Parts[1], "Process")
        }
    }
}

if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
} elseif (Test-Path -LiteralPath $BundledPython) {
    $Python = $BundledPython
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand) {
        throw "Python 3.12 was not found. Run scripts/setup.ps1 first."
    }
    $Python = $PythonCommand.Source
}

Set-Location $ProjectRoot
$ApiHost = if ($env:API_HOST) { $env:API_HOST } else { "127.0.0.1" }
$ApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8000" }
& $Python -m uvicorn services.api.main:app --reload --host $ApiHost --port $ApiPort
