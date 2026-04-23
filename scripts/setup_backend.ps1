param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$venvPath = ".venv"
$pipPath = Join-Path $venvPath "Scripts\\pip.exe"

Write-Host "Criando ambiente virtual em $venvPath..."
& $Python -m venv $venvPath

Write-Host "Instalando dependencias do backend..."
& $pipPath install -r "backend/requirements.txt"

Write-Host "Setup concluido."
