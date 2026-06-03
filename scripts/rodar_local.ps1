# ============================================================
# RODAR PROJETISTAV2 LOCALMENTE
# Executar na raiz do projeto após o setup_novo_pc.ps1
# ============================================================

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent

Write-Host "Iniciando ProjetistaV2..." -ForegroundColor Cyan

# 1. Docker Desktop
$dockerRunning = try { docker info 2>&1 | Out-Null; $true } catch { $false }
if (-not $dockerRunning) {
    Write-Host "Abrindo Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    Write-Host "Aguardando Docker (~30s)..."
    Start-Sleep -Seconds 30
}

# 2. Banco
Set-Location $Root
docker-compose up -d db 2>&1 | Out-Null
Start-Sleep -Seconds 4
docker exec projetista_v2_db pg_isready -U projetista -d projetista_v2 | Out-Null
Write-Host "  [OK] Banco PostgreSQL" -ForegroundColor Green

# 3. Backend
Start-Process -FilePath "$Root\.venv\Scripts\python.exe" `
  -ArgumentList "run.py" `
  -WorkingDirectory "$Root\backend" `
  -WindowStyle Normal
Start-Sleep -Seconds 6

$b = try { (Invoke-RestMethod "http://localhost:8000/health" -TimeoutSec 5).status } catch { "offline" }
if ($b -eq "ok") {
    Write-Host "  [OK] Backend → http://localhost:8000/docs" -ForegroundColor Green
} else {
    Write-Host "  [AGUARDANDO] Backend ainda iniciando..." -ForegroundColor Yellow
}

# 4. Frontend
Start-Process -FilePath "cmd.exe" `
  -ArgumentList "/c", "npm run dev" `
  -WorkingDirectory "$Root\frontend" `
  -WindowStyle Normal
Start-Sleep -Seconds 8

$f = try { (Invoke-WebRequest "http://localhost:5173" -TimeoutSec 5 -UseBasicParsing).StatusCode } catch { "offline" }
if ($f -eq 200) {
    Write-Host "  [OK] Frontend → http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "  [AGUARDANDO] Frontend ainda iniciando..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "  SISTEMA NO AR!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "  http://localhost:5173   ← Aplicação" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs ← API" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Login: teste_local / senha123" -ForegroundColor Gray
Write-Host ""
