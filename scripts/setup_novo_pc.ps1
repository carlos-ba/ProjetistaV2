# ============================================================
# SETUP COMPLETO — ProjetistaV2
# Executar em um novo PC com Windows após instalar:
#   - Python 3.14+  → https://python.org
#   - Node.js 18+   → https://nodejs.org
#   - Docker Desktop → https://docker.com
#   - Git            → https://git-scm.com
#   - VS Code (opcional) → https://code.visualstudio.com
#
# USO:
#   1. Abra o PowerShell como Administrador
#   2. cd C:\caminho\onde\quer\o\projeto
#   3. .\setup_novo_pc.ps1
# ============================================================

$ErrorActionPreference = "Stop"
$Projeto = "ProjetistaV2"
$Repo    = "https://github.com/carlos-ba/ProjetistaV2.git"

function Log($msg, $cor = "Cyan") { Write-Host "`n==> $msg" -ForegroundColor $cor }
function Ok($msg)  { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Err($msg) { Write-Host "  [ERRO] $msg" -ForegroundColor Red; exit 1 }

# ── 1. Verificar pré-requisitos ──────────────────────────────
Log "Verificando pré-requisitos..."

@("python","node","npm","git","docker") | ForEach-Object {
    if (-not (Get-Command $_ -ErrorAction SilentlyContinue)) {
        Err "$_ não encontrado. Instale antes de continuar."
    }
    Ok "$_ encontrado"
}

# ── 2. Clonar repositório ────────────────────────────────────
Log "Clonando repositório..."
if (Test-Path $Projeto) {
    Write-Host "  Pasta '$Projeto' já existe — atualizando..."
    Set-Location $Projeto
    git pull origin main
} else {
    git clone $Repo $Projeto
    Set-Location $Projeto
}
Ok "Repositório pronto"

$Root = Get-Location

# ── 3. Virtual environment Python ───────────────────────────
Log "Criando ambiente virtual Python..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Ok "Venv criado"
} else {
    Ok "Venv já existe"
}

# ── 4. Instalar dependências Python ──────────────────────────
Log "Instalando dependências Python..."
& ".\.venv\Scripts\pip.exe" install -r "backend\requirements.txt" --quiet
Ok "Dependências Python instaladas"

# ── 5. Criar .env do backend ─────────────────────────────────
Log "Configurando .env do backend..."
$envFile = "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item "backend\.env.example" $envFile
    Write-Host "  Arquivo .env criado a partir do exemplo." -ForegroundColor Yellow
    Write-Host "  *** IMPORTANTE: edite o arquivo backend\.env e preencha as variáveis ***" -ForegroundColor Red
} else {
    Ok ".env já existe"
}

# ── 6. Instalar dependências Node ────────────────────────────
Log "Instalando dependências do frontend..."
Set-Location "frontend"
npm install --silent
Set-Location $Root
Ok "Dependências Node instaladas"

# ── 7. Docker — subir banco ──────────────────────────────────
Log "Iniciando banco de dados PostgreSQL via Docker..."
docker-compose up -d db 2>&1 | Out-Null
Start-Sleep -Seconds 5
$ready = docker exec projetista_v2_db pg_isready -U projetista -d projetista_v2 2>&1
if ($ready -like "*accepting*") {
    Ok "Banco PostgreSQL rodando"
} else {
    Write-Host "  Banco ainda iniciando — aguarde e execute as migrations manualmente." -ForegroundColor Yellow
}

# ── 8. Rodar migrations ──────────────────────────────────────
Log "Executando migrations do banco..."
Set-Location "backend"
try {
    & ".\.venv\Scripts\alembic.exe" upgrade head 2>&1 | Select-String "Running upgrade|already up"
    Ok "Migrations aplicadas (0001 → 0007)"
} catch {
    Write-Host "  Migrations falharam — verifique se o banco está rodando e o .env está correto." -ForegroundColor Yellow
}
Set-Location $Root

# ── 9. Resumo final ──────────────────────────────────────────
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  SETUP CONCLUÍDO!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Edite o arquivo backend\.env:" -ForegroundColor White
Write-Host "   - APP_ENV=development"
Write-Host "   - SECRET_KEY=qualquer-chave-local"
Write-Host "   - DATABASE_URL=postgresql+psycopg://projetista:projetista@localhost:5432/projetista_v2"
Write-Host "   - ANTHROPIC_API_KEY=sua-chave (se usar IA)"
Write-Host ""
Write-Host "2. Importe os dados do catálogo (equipamentos, perfis, etc.):" -ForegroundColor White
Write-Host "   Os scripts estão em scripts\ — use os arquivos Excel do OneDrive"
Write-Host "   Exemplo: python scripts\importar_excel.py <arquivo.xlsx>"
Write-Host ""
Write-Host "3. Para RODAR o projeto:" -ForegroundColor White
Write-Host "   Terminal 1: .\scripts\run_backend.ps1"
Write-Host "   Terminal 2: cd frontend && npm run dev"
Write-Host ""
Write-Host "4. Acesse: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "PRODUÇÃO:" -ForegroundColor Yellow
Write-Host "   Frontend: https://projetista-v2-frontend-carlos-bas-projects.vercel.app"
Write-Host "   Backend:  https://projetista-v2-backend.onrender.com"
Write-Host ""
