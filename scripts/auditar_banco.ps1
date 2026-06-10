# ============================================================
# AUDITORIA DO BANCO DE PRODUCAO vs LOCAL
# Uso: .\scripts\auditar_banco.ps1
# ============================================================

param(
    [string]$Token = "afd9dbd2df55ef4b30c286c16d16e0c5e836cbfdfd0b1e79c2471f7bac773915",
    [string]$BackendUrl = "https://projetista-v2-api-alt.onrender.com"
)

Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  AUDITORIA DO BANCO DE PRODUÇÃO" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan

# ── Contagens locais ────────────────────────────────────────
Write-Host "`n[LOCAL] Contando registros..." -ForegroundColor Yellow
$localContagens = @{}
$tabelas = @(
    "equipamento", "performance_equipamento",
    "componente_tecnico", "performance_componente",
    "painel_frigorifico", "isolamento_tubulacao", "porta_frigoriifica"
)
foreach ($t in $tabelas) {
    $count = docker exec projetista_v2_db psql -U projetista -d projetista_v2 -t -A -c "SELECT COUNT(*) FROM $t" 2>$null
    $localContagens[$t] = [int]$count.Trim()
}

# ── Contagens em produção ───────────────────────────────────
Write-Host "[PROD]  Consultando produção..." -ForegroundColor Yellow
try {
    $prod = Invoke-RestMethod -Uri "$BackendUrl/api/seed/auditoria?token=$Token" -Method GET -TimeoutSec 60
} catch {
    Write-Host "ERRO ao consultar producao: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# ── Comparação ─────────────────────────────────────────────
Write-Host ""
Write-Host "┌──────────────────────────────┬──────────┬──────────┬────────┐"
Write-Host "│ Tabela                       │  Local   │  Prod    │ Status │"
Write-Host "├──────────────────────────────┼──────────┼──────────┼────────┤"

$algumProblema = $false
foreach ($t in $tabelas) {
    $local = $localContagens[$t]
    $prodVal = $prod.contagens.$t
    $status = if ($local -eq $prodVal) { "✅ OK  " } else { "❌ DIFF"; $algumProblema = $true }
    $cor = if ($local -eq $prodVal) { "Green" } else { "Red" }
    $linha = "│ {0,-28} │ {1,8} │ {2,8} │ {3}  │" -f $t, $local, $prodVal, $status
    Write-Host $linha -ForegroundColor $cor
}
Write-Host "└──────────────────────────────┴──────────┴──────────┴────────┘"

# ── Integridade ─────────────────────────────────────────────
Write-Host ""
if ($prod.componentes_sem_performance_total -gt 0) {
    Write-Host "⚠️  COMPONENTES SEM PERFORMANCE:" -ForegroundColor Red
    $prod.componentes_sem_performance | ForEach-Object {
        Write-Host "   - $($_.modelo) ($($_.categoria))" -ForegroundColor Red
    }
    $algumProblema = $true
}

if ($prod.equipamentos_sem_performance_total -gt 0) {
    Write-Host "⚠️  EQUIPAMENTOS SEM PERFORMANCE:" -ForegroundColor Red
    $prod.equipamentos_sem_performance | ForEach-Object {
        Write-Host "   - $($_.modelo) ($($_.categoria))" -ForegroundColor Red
    }
    $algumProblema = $true
}

Write-Host ""
Write-Host "Performances por componente (produção):" -ForegroundColor Cyan
$prod.performances_por_componente.PSObject.Properties | ForEach-Object {
    $cor = if ($_.Value -ge 8) { "Green" } else { "Yellow" }
    Write-Host "   $($_.Name): $($_.Value)" -ForegroundColor $cor
}

Write-Host ""
if ($algumProblema) {
    Write-Host "⚠️  BANCO DESINCRONIZADO — execute o seed necessário antes de fazer deploy!" -ForegroundColor Red
} else {
    Write-Host "✅  BANCO SINCRONIZADO — local e produção estão iguais." -ForegroundColor Green
}
Write-Host ""
