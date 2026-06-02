# CHECKPOINT — 01/06/2026
## Projetista V2 — Estado atual do desenvolvimento

---

## ✅ O QUE FOI FEITO HOJE

### Importação de dados reais
| Arquivo | Categoria | Modelos | Performances |
|---|---|---|---|
| pg1_ES+_404_copeland_ocr_v2.xlsx | Unidade Condensadora | 7 (ES+) | 278 |
| Evaporadores FL Elgin.xlsx | Evaporadora | 12 (FL*) | 264 |
| Selecao_Val_Expansao_kcal.xlsx | VET Danfoss | 8 (T2) | 64 |

### Correções ASHRAE
- `Carne Suína`: ponto congelamento -2.00 → **-2.20°C**, cp acima 3.44 → **3.60**, cp abaixo 1.72 → **1.81**, teor água 72 → **75.9%**
- `Frango Inteiro`: calor latente 246 → **220 kJ/kg**
- `Queijo Maturado`: ponto congelamento -10.00 → **-6.00°C**

### Correções críticas de unidades no cálculo de carga térmica
- **Carga de produto**: c1/c2 em kJ/(kg·K) agora corretamente convertidos para kcal com `×(1/4.184)` — antes estava 4,18× maior
- **Taxa de respiração**: W/tonne → kcal/h com `(mov/1000)×taxa×0.86` — antes estava 48× maior

### Melhoria no cálculo de infiltração
- Novo campo `metodo_infiltracao`: "simplificado" ou "psicrometrico"
- Método psicrométrico calcula entalpia real via fórmula de Magnus + ASHRAE Cap.1
- Novos campos `ur_externa` (%) e `ur_interna` (%) no request
- Frontend atualizado com seletor e campos de UR

### Padronização de categorias
Todos os nomes de categoria atualizados para terminologia técnica correta:
"Condensadora" → "Unidade Condensadora", "Válvula de Expansão" → "Válvula de Expansão Termostática", etc.

### Migration banco
- `0003_performance_consumo_kw.py`: renomeia `consumo_w` → `consumo_kw` (Numeric 8,3)

### Limpeza do banco
- Removidos todos os dados de seed (componentes, equipamentos, materiais sem performance real)
- Mantidos apenas: dados reais importados + perfis ASHRAE validados

### Documentação
- `docs/DECISOES_ARQUITETURA.md` — registro de todas as decisões técnicas

---

## 🗃️ ESTADO DO BANCO (dados reais)

| Tabela | Registros |
|---|---|
| equipamento | 32 (19 seed antigo com performance + 7 ES+ + 12 FL*) |
| performance_equipamento | 627 |
| componente_tecnico | 8 (VET Danfoss T2) |
| performance_componente | 64 |
| perfil_produto_termico | 26 (ASHRAE validado) |
| material | 0 (aguardando dados reais) |

---

## ⏳ PRÓXIMO PASSO

**Continuar importando planilhas de dados reais** ou iniciar **Fase 2 — Admin panel**.

Decisão de arquitetura registrada:
- Catálogo Global × Catálogo da Empresa (implementar no Admin)
- Campo `custo` como preço de referência, preço real no orçamento
- Categoria = formulário próprio no Admin

---

## 🚀 COMO RETOMAR O AMBIENTE LOCAL

```powershell
# 1. Docker Desktop (ícone verde na bandeja)
# 2. Banco
docker-compose up -d db
# 3. Backend
.\scripts\run_backend.ps1
# 4. Frontend
cd frontend && npm run dev
```

Credenciais de teste: `teste_local` / `senha123`
