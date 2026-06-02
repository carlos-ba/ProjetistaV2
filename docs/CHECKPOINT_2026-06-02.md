# CHECKPOINT — 02/06/2026
## Projetista V2 — Estado atual do desenvolvimento

---

## ✅ O QUE FOI FEITO HOJE

### UX — Wizard com cards colapsáveis (concluído)
- `EtapaCard.jsx` — componente com `somenteLeitura`, `onSelecionar`, `onEditar`, `onFechar`
- Card 6 (Orçamento) sem botões Editar/Descartar — abre/fecha pelo header
- Clique no header → mostra detalhe à direita SEM abrir para edição
- Clique em "✏️ Editar" → abre card para edição
- Clique em "✕ Descartar edição" → fecha sem perder dados
- Dados preservados via `className="hidden"` (componentes nunca desmontados)

### UX — Painel lateral direito melhorado
- Detalhe rico por etapa: cada card mostra info específica no painel direito
- Contorno roxo (`border-[#7B2D8B]/30 bg-purple-50/40`) para distinguir o painel de detalhe
- PainelInsights movido para sidebar esquerda (acima do status do servidor)
- `itensAcessorios` e `itensTubulacao` guardados separadamente no App.jsx → painéis corretos

### Correções de dados
- Categoria `"Separador de Líquido"` corrigida (acento faltando causava erro na seleção)
- Lógica de seleção do separador corrigida com **interpolação linear** real
- Evaporadoras seed (SILP/EVAP) removidas — ficam apenas FL* com dados reais
- Typo `"Evaporador"` → `"Evaporadora"` no frontend (seleção não encontrava)

### Isolamento de tubulação — completo
- Tabela `isolamento_tubulacao` criada (migration 0006) com 97 registros Armacel
- Script `scripts/importar_isolamento.py` criado e executado
- `calculos_tubulacao.py` refatorado para async + consulta banco Armacel
- Conversão bitola imperial → mm (1/4" a 4.1/8")
- Sugestão automática de padrão por T.Evap (D/F/H/M/R/T)
- Linha de sucção sempre isolada; linha de líquido opcional
- Endpoint `GET /api/v1/tubulacao/sugestao-isolamento?temp_evap=X`
- Frontend `CalculadoraTubulacao.jsx` completamente redesenhado

### Limpeza do cálculo de tubulação
- Removidos: Isolamento Polietileno hardcoded e Fita PVC — não tinham tabela real

---

## 🗃️ ESTADO DO BANCO

| Tabela | Registros |
|---|---|
| equipamento | 19 (7 ES+ condensadoras + 12 FL* evaporadoras) |
| performance_equipamento | 627 |
| componente_tecnico | 18 (8 VET + 10 Separador de Líquido) |
| performance_componente | 128 (64 VET + 64 Separador) |
| painel_frigorifico | 16 (Kingspan Isoeste PIR) |
| isolamento_tubulacao | 97 (Armacel D/F/H/M/R/T) |
| perfil_produto_termico | 26 (ASHRAE validado) |

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

- **Frontend:** http://localhost:5173
- **Swagger:** http://localhost:8000/docs
- **Login:** `teste_local` / `senha123`

---

## ⏳ PRÓXIMOS PASSOS

### Prioridade imediata
1. **Testar fluxo completo** — Gabinete → Carga → Equipamentos → Acessórios → Tubulação → Orçamento
2. **Mais planilhas** — Danfoss VET R404A, compressores, outros fabricantes

### Roadmap
```
✅ Fase 1 — Segurança & Auth
✅ Dados reais importados
✅ Correções ASHRAE
✅ Wizard UX com cards colapsáveis
✅ Isolamento tubulação com catálogo Armacel
⏳ Fase 2 — Admin panel
⏳ Fase 3 — IA com Tool Use
⏳ Fase 4 — Deploy
⏳ Fase 5 — Billing
```

---

## 📁 ARQUIVOS MODIFICADOS HOJE

```
frontend/src/
├── App.jsx                          ← passoSelecionado, itensAcessorios, itensTubulacao
├── components/
│   ├── EtapaCard.jsx                ← somenteLeitura, onSelecionar, onEditar, onFechar
│   ├── PainelResumoLateral.jsx      ← detalhe por etapa, contorno roxo, itens separados
│   └── CalculadoraTubulacao.jsx     ← seletor padrão D/F/H/M/R/T, toggle líquido

backend/app/
├── schemas/tubulacao.py             ← padrao_isolamento, isolar_liquido, SugestaoIsolamentoResponse
├── services/calculos_tubulacao.py   ← async, catálogo Armacel, sugestão automática
├── api/routes_tubulacao.py          ← async, endpoint sugestão-isolamento
└── models/isolamento.py             ← IsolamentoTubulacao (NOVO)

backend/alembic/versions/
└── 0006_isolamento_tubulacao.py     ← NOVA migration

scripts/
├── importar_isolamento.py           ← NOVO
└── isolamento_temp.xlsx             ← cópia local da planilha Armacel
```
