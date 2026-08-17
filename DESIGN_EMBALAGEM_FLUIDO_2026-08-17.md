# Design — Embalagem de fluido refrigerante na lista final de peças

**Data:** 2026-08-17 · **Status:** desenho fechado com o usuário, implementado com dados de teste
(R404A). Cadastro real dos demais fluidos/tamanhos fica pendente — processo de atualização a
combinar quando o usuário tiver os dados.

---

## 1. Contexto e motivação

O Card 5/6 já estima a carga total de fluido refrigerante em **kg** (`carga_fluido.py`, ver também
[[project_carga_fluido_referencias]] na memória). Mas fluido refrigerante não é vendido a granel —
é vendido em **embalagens de tamanho fixo** (cilindros descartáveis). A lista final de peças
(Card 6) até então mostrava só "Carga de Fluido R404A — X kg", que não é uma peça comprável.

Faltava: converter esse kg estimado em quantas embalagens de qual tamanho o técnico deve colocar
na lista de compra.

---

## 2. Decisões tomadas (usuário, 2026-08-17)

1. **Só embalagem descartável.** Retornável foi descartado — não é mais utilizado na prática.
2. **Local: Card 6**, junto da lista final — não no Card 5 (onde a carga ainda pode mudar).
3. **Poucos tamanhos por fluido** — cadastro pequeno, cabe seed direto por migration (sem
   importador de planilha como equipamentos/painéis, ao menos por enquanto).
4. **Algoritmo de sugestão** (substitui a ideia inicial de bin-packing por combinação):
   - Filtra as embalagens do fluido do projeto onde `peso_kg ≥ carga_total_kg` — ou seja, as que
     **cobririam a carga sozinha**.
   - Se só existir **uma** candidata: mostra ela direto, sem escolha.
   - Se existir **mais de uma**: lista todas, o técnico escolhe qual prefere (na prática tende a
     escolher a maior das opções válidas, por estratégia de deixar sobra de fluido na obra para
     eventual atendimento de garantia — mas isso é comportamento do usuário, não uma regra fixa no
     código).
   - **Quantidade = sempre 1** nesse caso (a embalagem escolhida já cobre a carga sozinha).
   - **Caso de borda — carga maior que a maior embalagem cadastrada** (nenhuma cobre sozinha):
     usa a maior embalagem disponível do fluido, quantidade = `arredondar_para_cima(carga_total_kg
     / peso_da_maior)`. Mesma filosofia de sempre sobrar fluido, aplicada a múltiplas unidades.
5. **Dados reais ficam pendentes.** Para teste, cadastrado só R404A: 10,9 kg e 0,7 kg (700 g).
   Quando o usuário levantar os tamanhos reais por fluido, os dados são atualizados — forma exata
   desse processo (migration nova vs. tela de admin) ainda não decidida, não é bloqueante agora.

---

## 3. Arquitetura implementada

### 3.1 Tabela nova — `embalagem_fluido`

Catálogo global (mesmo padrão do catálogo técnico existente — sem dono por empresa).

| Coluna | Tipo | Papel |
|---|---|---|
| `id` | Integer (PK) | — |
| `fluido` | String(20) | Ex: `R404A`, `R22` — mesma convenção de nomenclatura usada em `carga_fluido.py`/`solenoide.py`. |
| `peso_kg` | Float | Peso líquido de fluido na embalagem (kg). |

Sem coluna de tipo (só descartável, per decisão acima). Sem preço/código interno — isso é Fase B
(catálogo por empresa), igual ao resto do catálogo técnico hoje.

### 3.2 Backend

- `backend/app/models/embalagem_fluido.py` — model.
- `backend/alembic/versions/0024_embalagem_fluido.py` — cria a tabela e semeia dados de teste
  (R404A: 10,9 kg e 0,7 kg).
- `GET /api/v1/embalagem-fluido` — retorna todas as embalagens cadastradas (padrão do projeto:
  catálogo pequeno, carregado uma vez no `App.jsx` e passado via props — nunca buscado dentro de
  componente filho).

### 3.3 Frontend

- `App.jsx` — busca `embalagem-fluido` junto do resto do catálogo (fabricantes de painel, portas),
  passa como prop pro `GeradorOrcamento`.
- `ComponentesFluxo.jsx` — o item "Carga de Fluido" passa a carregar um campo `fluido` explícito
  (antes só existia embutido no texto do nome do item) para o Card 6 saber qual fluido filtrar no
  catálogo de embalagens sem parsear texto.
- `GeradorOrcamento.jsx` — aplica o algoritmo da seção 2 sobre o item `tipo_item === 'carga_fluido'`
  antes dele entrar em `materiaisAprovados` (o array-fonte usado por toda a lista, pelo payload do
  orçamento, pelo PDF e pelo Excel de cotação) — ponto único de transformação, garante que a escolha
  se propaga pra todo lugar que já lia esse array, sem precisar tocar cada exportador individualmente.
  Quando o técnico ainda não escolheu, ou não há embalagem cadastrada pro fluido do projeto, o item
  continua aparecendo em kg como hoje (nenhuma regressão pros fluidos sem cadastro ainda).

---

## 4. Não implementado / pendente

- Cadastro real dos tamanhos por fluido além do R404A de teste.
- Processo/tela de atualização do catálogo de embalagens (hoje só via migration/SQL direto).
- Preço por embalagem (Fase B, junto do resto do catálogo por empresa).
