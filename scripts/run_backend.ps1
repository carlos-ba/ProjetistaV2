$ErrorActionPreference = "Stop"

$pythonPath = ".venv\Scripts\python.exe"
$backendPath = "backend"

if (-not (Test-Path $pythonPath)) {
    Write-Error "Ambiente virtual nao encontrado. Execute scripts/setup_backend.ps1 primeiro."
}

Write-Host "Iniciando backend em http://localhost:8000 ..." -ForegroundColor Cyan
Write-Host "Swagger UI: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "(Ctrl+C para parar)`n"

Set-Location $backendPath
& "..\$pythonPath" run.py
