$ErrorActionPreference = "Stop"

$pythonPath = ".venv\\Scripts\\python.exe"

if (-not (Test-Path $pythonPath)) {
  Write-Error "Ambiente virtual nao encontrado. Execute scripts/setup_backend.ps1 primeiro."
}

Set-Location "backend"
& "..\\$pythonPath" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
