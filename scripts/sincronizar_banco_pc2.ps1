# ============================================================
# SINCRONIZAR BANCO LOCAL DO PC2 (NOTEBOOK) COM PRODUCAO
# Executar no PC2: C:\projetos\ProjetistaV2
# Uso: .\scripts\sincronizar_banco_pc2.ps1
# ============================================================

$token = "afd9dbd2df55ef4b30c286c16d16e0c5e836cbfdfd0b1e79c2471f7bac773915"
$base  = "https://projetista-v2-api-alt.onrender.com"

Write-Host ""
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SINCRONIZANDO BANCO DO PC2 (NOTEBOOK)" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

function Chamar($url, $metodo = "GET") {
    try {
        $r = Invoke-RestMethod -Uri $url -Method $metodo -TimeoutSec 60
        return $r
    } catch {
        Write-Host "  ERRO: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

# 1. Verifica backend
Write-Host "[1/7] Verificando backend..." -NoNewline
$h = Chamar "$base/health"
if ($h.status -eq "ok") { Write-Host " OK" -ForegroundColor Green } else { Write-Host " FALHOU" -ForegroundColor Red; exit 1 }

# 2. Categorias e fabricantes
Write-Host "[2/7] Categorias e fabricantes..." -NoNewline
$r = Chamar "$base/api/seed/base-completo?token=$token" "POST"
Write-Host " $($r.totais.categoria) categorias" -ForegroundColor Green

# 3. Corrige nomes das categorias
Write-Host "[3/7] Corrige nomes das categorias..." -NoNewline
$r = Chamar "$base/api/seed/fix-categorias?token=$token" "POST"
Write-Host " OK" -ForegroundColor Green

# 4. Separadores de Líquido RAC (10 modelos)
Write-Host "[4/7] Separadores de Líquido RAC..." -NoNewline
$r = Chamar "$base/api/seed/rac-extras?token=$token" "POST"
Write-Host " $($r.total_separadores_liquido) modelos" -ForegroundColor Green

# 5. T2 VET Danfoss (16 performances cada)
Write-Host "[5/7] VET T2 Danfoss performances..." -NoNewline
$r = Chamar "$base/api/seed/perf-t2?token=$token" "POST"
Write-Host " $($r.total_performance_componente) performances" -ForegroundColor Green

# 6. Separadores de Óleo SOF
Write-Host "[6/7] Separadores de Óleo SOF..." -NoNewline
$r = Chamar "$base/api/seed/sep-oleo?token=$token" "POST"
Write-Host " $($r.total_componentes) modelos" -ForegroundColor Green

# 7. Isolamentos Armacel
Write-Host "[7/7] Isolamentos Armacel..." -NoNewline
$r = Chamar "$base/api/seed/isolamentos?token=$token" "POST"
Write-Host " $($r.total) registros" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Sincronização concluída!" -ForegroundColor Green
Write-Host "   Execute: .\scripts\auditar_banco.ps1 para confirmar" -ForegroundColor Gray
Write-Host ""
