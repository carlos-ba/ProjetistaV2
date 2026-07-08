# 05 - Frontend

Atualizado em: 2026-06-28

---

## 1. Stack

| Tecnologia | Versão | Função |
|-----------|--------|--------|
| React | 19 | UI e gerenciamento de estado |
| Vite | latest | Bundler e dev server |
| Tailwind CSS | v3 | Estilização utility-first |
| shadcn/ui | latest | Componentes de UI base |
| Axios | latest | Cliente HTTP (`src/api.js`) |

---

## 2. Estrutura de Arquivos

```
frontend/src/
├── App.jsx                        ← Orquestrador principal — state management global + wizard
├── main.jsx                       ← Entry point
├── api.js                         ← Axios wrapper com interceptors de auth
├── contexts/
│   └── AuthContext.jsx            ← Contexto de autenticação (JWT)
├── pages/
│   └── LoginPage.jsx              ← Tela de login
└── components/
    ├── EtapaCard.jsx              ← Wrapper para cada card (expansível/colapsável)
    ├── CalculadoraGabinete.jsx    ← Card 1: gabinete + painéis PIR + portas
    ├── CalculadoraCargaTermica.jsx← Card 2: carga térmica
    ├── SelecaoEquipamentos.jsx    ← Card 3: UC + evaporadora
    ├── CalculadoraTubulacao.jsx   ← Card 4: tubulação ASHRAE + isolamento
    ├── ComponentesFluxo.jsx       ← Card 5: todos os componentes de fluxo
    ├── GeradorOrcamento.jsx       ← Card 6: orçamento + cotação + proposta
    ├── PainelResumoLateral.jsx    ← Painel direito: resumo em tempo real por etapa
    ├── PainelInsights.jsx         ← Indicadores técnicos (sidebar esquerda)
    ├── PainelCotacoes.jsx         ← Gestão de cotações (sidebar)
    ├── ConfiguracoesPage.jsx      ← Perfis de montagem
    ├── CavaleteIlustracao.jsx     ← Diagrama SVG flutuante do cavalete
    └── VisualizadorProjeto.jsx    ← Preview do gabinete calculado
```

---

## 3. Fluxo do Wizard (App.jsx)

`App.jsx` é o orquestrador central. Gerencia todo o estado compartilhado entre os 6 cards e passa dados por callbacks.

### Estado principal

```javascript
// Resultados por card
dadosDoGabinete        // resultado Card 1
gabineteCalculado      // bool — Card 1 concluído
cargaCalculada         // kcal/h — resultado Card 2
tempExternaCalculo     // T.Amb do Card 2
itensGabinete          // lista_corte painéis — Card 1
itensTubulacao         // lista de tubos — Card 4
resultadoTubulacao     // objeto completo bitolas + distâncias — Card 4
itensAcessorios        // componentes do Card 5
cavaleteResult         // análise cavalete — Card 5
temTanqueCavalte       // bool — Card 5
itensOrcamento         // { materiais: [], equipamentos: [] } — Card 6

// Catálogo (carregado no boot com retry)
catalogoPaineis        // fabricantes + linhas PIR
catalogoPortas         // portas frigoríficas

// Configurações
configuracoesMontagem  // perfil de montagem do usuário

// Controle de fluxo
invalidados            // { 2: bool, 3: bool, 4: bool, 5: bool, 6: bool }
```

### Callbacks de propagação

| Callback | Disparado por | O que faz |
|----------|--------------|-----------|
| `receberDadosGabinete` | Card 1 | Salva gabinete, invalida cards 2-6 |
| `receberResultadoCarga` | Card 2 | Salva carga + T.Amb, invalida cards 3-6 |
| `receberEquipamentosFinalizados` | Card 3 | Salva equipamentos, reseta acessórios e tubulação, invalida 4-6 |
| `receberDadosTubulacao` | Card 4 | Salva tubulação + bitolas, invalida cards 5-6 |
| `receberComponentesFluxo` | Card 5 | Salva acessórios, invalida card 6 |
| `receberCavaleteChange` | Card 5 | Salva cavalete result + tem_tanque |

### Consolidação do orçamento

```javascript
// useEffect que reconstrui materiais sempre que algum card atualiza
useEffect(() => {
  setItensOrcamento(prev => ({
    ...prev,
    materiais: [...itensGabinete, ...itensAcessorios, ...itensTubulacao],
  }));
}, [itensGabinete, itensAcessorios, itensTubulacao]);
```

---

## 4. Catálogo — Carregamento no Boot

O catálogo de painéis PIR e portas frigoríficas é carregado no `App.jsx` **antes de renderizar qualquer card**, com retry automático a cada 2 segundos até sucesso.

**Regra:** nunca buscar catálogo dentro de um componente filho. Sempre passar via props.

---

## 5. Autenticação

- `AuthContext.jsx` gerencia o token JWT
- `api.js` intercepta todas as requisições para injetar o `Authorization: Bearer <token>`
- Ao receber 401, tenta refresh automático do token
- Redireciona para `LoginPage.jsx` se o refresh falhar

---

## 6. EtapaCard — Padrão dos Cards

Todos os 6 cards são envoltos por `EtapaCard.jsx` que oferece:
- Expansão/colapso pelo header (clique)
- Modo somente leitura (`somenteLeitura`) — exibe resumo no painel direito sem abrir para edição
- Botão "✏️ Editar" — abre para edição
- Botão "✕ Descartar edição" — fecha sem perder dados
- Dados preservados via `className="hidden"` (componentes **nunca** desmontados — estado preservado)

---

## 7. Card 5 — ComponentesFluxo (o mais complexo)

Fluxo de chamadas em paralelo via `Promise.allSettled`:
1. `POST /api/v1/componentes` — separadores
2. `POST /api/v1/solenoide/selecionar` — EVR v2
3. `POST /api/v1/acessorios/selecionar` — filtro DML/DMC + visor SGN

Encadeamento após carga de fluido:
```
estimarCargaFluido()
  ↓
POST /api/v1/tanque-liquido/selecionar
  ↓
analisarCavaleteAuto()
  ↓
POST /api/v1/cavalete/analisar
```

O diagrama SVG do cavalete é exibido em `CavaleteIlustracao.jsx` como painel flutuante.

---

## 8. Painel Lateral Direito

`PainelResumoLateral.jsx` exibe informações contextuais para cada card ativo:
- Card 1: dimensões e área calculada
- Card 2: carga térmica por fonte
- Card 3: equipamentos selecionados
- Card 4: bitolas e distâncias por trecho
- Card 5: todos os componentes com modelos
- Card 6: totais do orçamento

---

## 9. Variáveis de Ambiente

```
VITE_API_BASE_URL=http://localhost:8000   # local
VITE_API_BASE_URL=https://projetista-v2-api-alt.onrender.com  # produção (Vercel)
```

---

## 10. Regras de Desenvolvimento Frontend

- Nenhuma regra de cálculo de domínio no frontend — somente coleta de dados e exibição de resposta
- Estado global centralizado no `App.jsx`; estados locais nos cards apenas para controle de UI
- Componentes nunca desmontados enquanto o wizard está aberto (estado preservado via `hidden`)
- Tailwind CSS para toda estilização — sem CSS modules ou styled-components
