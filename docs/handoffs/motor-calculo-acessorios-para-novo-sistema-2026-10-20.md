# Handoff Claude → Codex — trilha e motor de cálculo de acessórios (molde para o sistema novo)

**Status:** pronto para entrega (documento de referência, sem código novo)
**Origem:** Card 1 do Projeto Câmara Fria (IceNexus) — "Kit de Montagem" + itens afins, validado em produção
**Fontes no repositório (leitura apenas):** `backend/app/services/kit_montagem.py`,
`backend/app/services/barreira_vapor.py`, `backend/app/services/calculos_gabinete.py`,
`backend/tests/test_kit_montagem.py`, `CLAUDE.md` (seção "Card 1 — Kit de Montagem — regras de piso e Perfil T")
**Data:** 2026-10-20

> Este documento descreve **regras e ordem de cálculo**, não a implementação. O que é específico de
> câmara frigorífica está marcado; o que é **molde reutilizável** para qualquer sistema que "monta
> uma estrutura a partir de peças em barra + insumos consumíveis" está marcado como **[MOLDE]**.

---

## 1. A trilha (jornada) em uma frase

O usuário informa a geometria → o sistema calcula **quanto de cada perfil é necessário (em metros)** →
**converte para barras inteiras compradas** → usa os **metros reais das barras compradas** para calcular
os insumos derivados (selante, rebite, parafuso) → soma **itens manuais** que o usuário acrescentou →
procura cada item **no catálogo** → devolve uma lista de materiais; o que não existir no catálogo **some da
lista e vira aviso**, nunca erro silencioso.

```
Entradas (geometria + opções do usuário)
   │
   ▼
[1] Geometria derivada (sem banco)  ──►  perímetro, comp. útil da parede, área de painéis, nº de juntas do teto
   │
   ▼
[2] Metros necessários por perfil   ──►  fórmulas por tipo de perfil (seção 4)
   │
   ▼
[3] Busca no catálogo + arredondar PARA CIMA em barras inteiras  ──►  metros REAIS comprados
   │
   ▼
[4] Soma dos metros reais (auto + manuais + porta + Perfil T)   ──►  "metros_perfis_totais" (e "metros_perfil_u")
   │
   ▼
[5] Derivados dos metros reais      ──►  selante, rebite, parafuso+bucha, barra roscada
   │
   ▼
[6] Lista final + avisos de catálogo
```

## 2. Princípios do motor — **[MOLDE]** (valem para o sistema novo)

1. **Arredondar para cima em barras inteiras PRIMEIRO.** `barras = ceil(metros_necessarios / comprimento_da_barra)`.
2. **Tudo que é derivado usa o metro REAL comprado** (`barras × comprimento_da_barra`), nunca o metro teórico.
   Se sobra barra, a sobra entra no cálculo de rebite/selante — é intencional (a sobra é material que será instalado/aplicado).
3. **Somar antes de arredondar quando o mesmo perfil atende várias fontes** (ex.: acabamento de várias
   portas somam o perímetro total e arredondam **uma vez**).
4. **Fallback de medida: "próximo tamanho ACIMA, nunca abaixo".** Se não existir a medida exata no
   catálogo, usa a menor medida maior que o alvo e **avisa no detalhe da linha** ("sem medida exata…, usado Xmm").
   Em perfis onde a medida exata é obrigatória (Ângulo Interno) não há fallback.
5. **Empate entre barras de mesma medida → prefere a de maior comprimento** (menos barras a comprar).
6. **Catálogo ausente ≠ erro.** Item sem cadastro não entra na lista e gera mensagem em `avisos`
   (renderizada como banner vermelho acima da tabela). Sem isso o item some sem o usuário perceber.
7. **Insumos simples (selante, rebite, parafuso+bucha, barra roscada) usam a primeira linha do catálogo**
   (`ORDER BY id LIMIT 1`) — catálogo pequeno de propósito, sem seleção por especificação.
8. **Fator de segurança aplicado SÓ no selante**, campo local do card, independente de qualquer outra
   margem do sistema. Padrão 10%.
9. **Geometria (sem banco) separada do kit (com banco).** A função de geometria é síncrona e pura; o kit
   consome os resultados dela. Facilita teste e evita acoplamento.
10. **Sem retroatividade:** projeto salvo só muda quantidade quando o usuário manda recalcular.

## 3. Entradas e configurações

**Entradas do usuário (por projeto):** comprimento (C), largura (L), altura (H) da câmara; espessura do
painel (mm); largura do painel (m); tipo de piso (`painel` | `convencional` apoiado/rebaixado | `nenhum`);
`auto_portancia_mm` do painel (opcional); painéis extras manuais (uso/comprimento/qtde); portas com
flag "incluir perfil U de acabamento" (largura, altura, batente 3B/4B, qtde); perfis extras manuais
(perfil escolhido + quantidade de barras); fator de segurança do selante.

**Configurações por empresa (`ConfiguracaoMontagem`):**
- `largura_aba_padrao_mm` — aba padrão dos perfis, **40 mm**.
- `rendimento_selante_m_por_embalagem` — **12 m** de cordão por embalagem (se 0/vazio, usa 12).

**Catálogos:**
- `perfil_metalico`: `tipo` (Ângulo Externo | Ângulo Interno | U | T | Liso | Z), `medida_1_mm`, `medida_2_mm`,
  `medida_3_mm`, `comprimento_mm` (barras de 3 m; Perfil T de 6 m), `codigo_fabricante`, `descricao_original`.
- `selante_montagem`, `rebite`, `parafuso_bucha`, `barra_roscada_perfil_t`: fabricante + código + descrição.
- `catalogo_generico` (por `tipo_item`: `lona_val_film`, `fita_branca`, `lona`): molde para o próximo
  cadastro simples; usa fabricante "Genérico" quando não há fornecedor específico.

## 4. Fórmulas, na ordem de cálculo

Notação: `P = 2C + 2L` (perímetro, m); `esp` = espessura do painel (m); `aba` = aba padrão (mm);
`hp` = altura útil da parede (m) — no sistema real: altura − espessura do teto, e − também a do piso
quando o piso é em painel; `ceil` = arredonda para cima; `Lbarra` = comprimento da barra do catálogo (m).

### 4.1 Geometria derivada (sem banco)
- **Área de painéis para o selante** = paredes + teto + **piso apenas se for em painel** + painéis extras manuais.
  **Não inclui:** placas de isolamento do piso convencional (outro tipo de isolamento, sem selante) nem portas.
- **Teto dividido pela auto-portância:** `N = ceil(L / auto_portância)`; cada pedaço mede `L / N` (pedaços **iguais**).
  Sem `auto_portância` ou L já dentro do limite → `N = 1`. **Linhas de sustentação do Perfil T = N − 1.**
  (Vale também para piso em painel na lista de painéis; o Perfil T é só do teto.)

### 4.2 Perfis automáticos (busca no catálogo + barras inteiras)

| Perfil | Metros necessários | Busca no catálogo |
|---|---|---|
| **Ângulo Externo** | `P + 4 × (hp + esp)` **+ `P` extra se piso em painel** | tipo, `medida_1 = aba`, `medida_2 ≥ aba + esp(mm)` (menor possível; fallback acima) |
| **Ângulo Interno** | `P + 4 × hp` | tipo, `medida_1 = aba`, `medida_2 = aba` (**exato**, sem fallback) |
| **U do piso** | `P` — **só se o piso NÃO for em painel** | tipo U, `medida_1 = aba`, `medida_3 = aba`, `medida_2 ≥ esp(mm)` (fallback acima) |
| **U de acabamento das portas** | `Σ perímetro_porta × qtde` das portas marcadas; **arredonda uma vez** | mesma busca do U do piso |
| **Perfil T** (teto dividido) | `C × (N − 1)` | tipo T, barra de maior comprimento (6 m) |
| **Perfis extras manuais** | quantidade de barras **digitada** pelo usuário | perfil escolhido; metros = `barras × Lbarra` |

Perímetro da porta: `4B` = 2 alturas + 2 larguras; `3B` = 2 alturas + 1 largura (base é soleira, sem perfil).
O campo `soleira` do catálogo **não serve de critério** (vem falso até nas 3B) — a regra é só pelo batente.
Porta sem batente informado → trata como 4B (nunca sai curto) **e emite aviso**.

**Regra de piso (correção validada em 2026-10-20):**
- Piso **em painel** → **não gera U do piso nem parafuso+bucha**; o acabamento parede × painel de piso
  segue o Ângulo Externo sobreposto, que ganha **uma volta extra de P**. As 4 subidas verticais permanecem.
- Piso **convencional** (apoiado ou rebaixado) ou **sem piso** → U do piso normal, sem volta extra.

### 4.3 Soma dos metros reais
```
metros_perfis_totais = Σ (barras × Lbarra)   de: Ângulo Externo, Ângulo Interno, U do piso,
                                                  U de porta, Perfil T, perfis manuais
metros_perfil_u      = Σ (barras × Lbarra)   de: U do piso e perfis manuais do tipo U
                                                  (U de porta NÃO entra aqui)
metros_perfil_t_real = barras_T × Lbarra_T
```
**Perfil T** soma em `metros_perfis_totais` (entra em selante e rebite), **não** em `metros_perfil_u`.
**U de porta** soma em `metros_perfis_totais` (selado e rebitado), **não** em parafuso+bucha.

### 4.4 Insumos derivados
- **Selante** (embalagens) =
  `ceil( ( metros_perfis_totais × 2  +  área_painéis × 0,145 ) ÷ rendimento × (1 + fator_segurança) )`
  — 2 cordões por perfil; 0,145 m de cordão por m² de painel; fator padrão 0,10.
- **Rebite** (un.) = `ceil( metros_perfis_totais × 1000 ÷ 200 ) × 2` — 2 linhas, 1 rebite a cada 200 mm.
- **Parafuso + bucha** (un.) = `ceil( metros_perfil_u × 1000 ÷ 500 )` — 1 linha, 1 conjunto a cada 500 mm, **só no U**.
- **Barra roscada** (un.) = `ceil( metros_perfil_t_real ÷ largura_do_painel )` — 1 kit por largura de painel
  ao longo do Perfil T, calculado sobre o metro **real** do T. Zero quando não há Perfil T.

### 4.5 Barreira de vapor (só piso convencional) — outro motor, mesma filosofia
Fórmulas confirmadas com o autor da planilha de referência, validadas num projeto real de 134 m² de piso:
- **Lona Val Film** (m²) = `área_piso × 1,20`
- **Fita Branca** (rolos) = `ceil( (área_piso × 1,20 ÷ 223) × 1,50 )` — 223 m²/rolo, fator 1,50 (fixos no código)
- **Lona** (m) = `(área_piso × 1,32) ÷ 4`
`área_piso` vale 0 quando o piso não é convencional → nada é gerado. Itens sem cadastro somem + aviso.

## 5. Exemplo de conferência (para validar a implementação nova)

Câmara 5 × 4 × 3 m, painel PIR 70 mm, aba 40 mm, barras de 3 m, rendimento 12 m, fator 10%, área de painéis 98,62 m²:

| Cenário | Ângulo Externo | Ângulo Interno | U | Parafuso | Selante | Rebite |
|---|---|---|---|---|---|---|
| **Piso em painel** | 16 barras (47,72 m; inclui a volta do piso) | 10 | **— (não gera)** | **—** | 16 | 780 |
| **Convencional / sem piso** | 10 | 10 | 6 | 36 | 16 | 780 |

**Perfil T** (largura 10 m, auto-portância 7 m ⇒ N = 2 ⇒ 1 linha; 1 barra de 6 m): selante 23 → 24, rebite
1140 → 1200 (+60), parafuso **60 inalterado** (T não entra em parafuso).

Os 5 testes de `backend/tests/test_kit_montagem.py` recompõem essas contas a partir do catálogo e são a
melhor especificação executável: piso em painel sem U/parafuso e com volta extra; convencional e sem piso
com U/parafuso; Perfil T em selante/rebite e fora do parafuso; totais com piso em painel.

## 6. Contrato de saída

Cada item da lista traz: `item` (nome), `qtd` (texto de exibição), `quantidade` (número), `unidade`
(`barra`/`embalagem`/`un`/`rolo`/`m²`/`m`), `detalhe` (rastreabilidade: medida, metros necessários, código do
fabricante, avisos de fallback) e `tipo_item` (slug estável para classificação:
`perfil_angulo_externo`, `perfil_angulo_interno`, `perfil_u`, `perfil_manual`, `perfil_t`,
`selante_montagem`, `rebite`, `parafuso_bucha`, `barra_roscada_perfil_t`, `lona_val_film`, `fita_branca`, `lona`).
Mais uma lista `avisos` (strings). **A ordem da lista é parte da experiência:** perfis automáticos → U de porta
→ perfis manuais → selante → rebite → parafuso → Perfil T → barra roscada.

## 7. O que é específico de câmara fria × o que é molde

- **Específico do domínio (adaptar):** nomes dos perfis, regra de piso (painel × convencional × sem piso), U de
  porta 3B/4B, Perfil T/barra roscada pela auto-portância, barreira de vapor, constantes 0,145 / 200 / 500 /
  223 / 1,32 ÷ 4.
- **Molde reutilizável:** princípios da seção 2, o pipeline da seção 1 (geometria pura → metros necessários →
  barras inteiras → metros reais → derivados), catálogo com fallback "acima", aviso em vez de erro, fator de
  segurança local, lista com `tipo_item` estável, testes que recompõem a conta a partir do catálogo.
- **Constantes que viram configuração no sistema novo** (hoje fixas ou por empresa): aba padrão, rendimento do
  selante, fator do selante, passo do rebite (200 mm), passo do parafuso (500 mm), consumo de selante por m²
  (0,145), rendimento e fator da fita branca.

## 8. Pontos a decidir com o dono do sistema novo antes de implantar

1. Quais perfis/insumos existem no domínio novo e quais regras de "geometria → metros" substituem as da seção 4.2.
2. Onde fica a fronteira entre geometria (sem banco) e kit (com banco) — recomendado manter separada.
3. Se haverá "perfil extra manual" e "painel extra manual" (impactam metros e área do selante).
4. Constantes da seção 7: fixas no código ou configuráveis por empresa.
5. Formato do catálogo e do cadastro (aqui: tabela por tipo de insumo simples + `catalogo_generico`).

## 9. Observações abertas (não resolvidas no sistema de origem)

- A lista do kit não distingue piso **rebaixado × apoiado** no U (ambos geram o mesmo U do perímetro) — não foi pedido mudar.
- O código de fabricante do Perfil T e da Barra Roscada no catálogo ainda é **placeholder** (não afeta quantidade).
- Catálogo de Selante/Rebite/Parafuso usa fabricante "Genérico" (sem fornecedor definido).
- Há uma versão mais antiga do desenho em `DESIGN_KIT_MONTAGEM_2026-09-01.md` (não versionado) — **este documento a supera**
  nas regras de piso e Perfil T.
