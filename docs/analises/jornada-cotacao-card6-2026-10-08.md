# Jornada do usuário — Lista, Cotação e Proposta (Card 6)

Levantamento feito em **2026-10-08**, a partir do relato do próprio usuário
(Carlos) percorrendo o fluxo como cliente. **Só análise — nenhum código foi
alterado.** Os achados são acumulados aqui e serão tratados numa **correção
única** ao final do levantamento.

Cada achado: o que o usuário viu → o que o código faz → causa → direção de
correção (proposta, não implementada).

---

## Achado 1 — A lista que gerou a cotação não é a lista que o Card 6 mostra ao reabrir

### O que o usuário viu

1. Abriu o SaaS, localizou o projeto pelo **Histórico** e abriu.
2. O sistema levou direto ao **Card 6, com todos os itens marcados**, esperando
   aprovar a lista para gerar o orçamento.
3. Só que esse projeto já tinha tido itens **desmarcados**, e era justamente essa
   lista reduzida que tinha gerado a **planilha Excel de cotação** enviada ao
   fornecedor.
4. Resultado: precisa **marcar/desmarcar tudo de novo de memória**, com risco de
   esquecer algum item e criar conflito com a cotação já recebida.

Expectativa do usuário (correta): se a lista reduzida é a que gerou a cotação,
ao reabrir o Card 6 deveria refletir **a lista geradora**, não a original.

### O que o código faz

- **A cotação é um retrato (snapshot) da lista no momento em que foi gerada.**
  `montarItensCotacao()` (`GeradorOrcamento.jsx`) monta equipamentos + materiais
  **aprovados** (+ complementos) e `ModalCotacaoFornecedor` envia tudo em
  `POST /api/v1/cotacoes`, que grava em `cotacao_item`. Ou seja, **a lista
  geradora existe no banco** (`GET /api/v1/cotacoes?projeto_id=…`).
- **A seleção de itens do Card 6 é outro estado, sem ligação com a cotação.**
  Antes de 2026-10-06 18:38 (commit `2c49dcc`) ela **nunca era salva**: vivia
  só na memória da tela e voltava a "tudo marcado" a cada abertura.
- **Cronologia explica o caso concreto:** a cotação COT-2026-0078-F015 foi
  gerada em 06/10 por volta das 16h50 — **antes** da correção que passou a salvar
  a seleção. Portanto o projeto **não tem** a seleção gravada, e "tudo marcado"
  era o comportamento esperado do código daquela época.
- **Mesmo depois da correção (`2c49dcc`) a lacuna estrutural continua:**
  1. A seleção só é gravada quando o usuário clica **Salvar** depois de mudá-la.
     Gerar a cotação **não** salva o projeto. Dá pra desmarcar, gerar a cotação,
     fechar, e perder a seleção de novo.
  2. Nada **amarra** a seleção à cotação. São duas fontes de verdade
     (checkboxes × `cotacao_item`) sem reconciliação.
  3. `listaAprovada` e o orçamento gerado também não são salvos — a cada
     abertura, recomeça em "Aprovar lista". Por si só é o desenho atual, mas
     combinado com "tudo marcado" dá a sensação de ter perdido o trabalho.

### Risco real (além do incômodo)

Ao gerar a proposta, o preço de cada item vem da **cascata**: cotação do projeto
→ lista de preços da empresa → último preço de cotação histórica
(`obter_mapa_precos`). Um item que o usuário **esqueceu de desmarcar** e que não
estava na cotação **não aparece como "sem preço"**: ele pode entrar na proposta
com um preço **silencioso** vindo do catálogo da empresa ou de uma cotação
antiga. Esse é o cenário em que o esquecimento custa dinheiro — preço de origem
diferente da cotação, sem aviso, misturado aos preços da cotação.

### Causa raiz

Não existe vínculo entre "o que foi cotado" e "o que está marcado". A seleção é
tratada como preferência de tela, quando na prática ela **define o escopo da
cotação** e deveria acompanhá-la.

### Direção de correção (a decidir na correção única)

- **A. Reconciliar com a cotação ao abrir o Card 6.** Se o projeto tem cotação
  (pendente ou processada), oferecer "Usar a lista da cotação COT-… ": marca o
  que está na cotação e desmarca o que não está, casando por `norm(descricao)`
  (a mesma chave já usada para preços). Mostrar o resumo da diferença
  ("3 itens da lista atual não estão na cotação").
- **B. Sinalizar item a item** na checklist: selo "na cotação COT-…" /
  "fora da cotação", para o esquecimento ficar visível.
- **C. Gravar a seleção junto com a cotação.** Ao gerar a planilha de cotação,
  persistir a seleção atual (autosave do `inputs_orcamento`), para as duas
  nascerem juntas.
- **D. Mostrar a origem de cada preço** na proposta (cotação / catálogo da
  empresa / histórico) e destacar, antes de gerar, itens marcados que **não
  estão na cotação escolhida**.
- **E. Aviso de "seleção não salva"** quando a seleção muda e o projeto não foi
  salvo.

Decisões que precisarão do usuário: se a reconciliação (A) é automática ou
pergunta antes; o que fazer quando há 2+ cotações (qual manda); se "tudo
aprovado" também deve ser lembrado ao reabrir.

---

## Achado 2 — Depois de gerar a proposta, o usuário não encontra como mudar a composição

### O que o usuário viu

Ao desmarcar os itens e gerar a lista, o sistema abre a **Lista de Engenharia** e a
**Composição da Proposta** (empreitada / faturamento direto, lista completa, mão
de obra) — essa parte funcionou bem. No fim da seção vieram os botões de gerar
planilha de cotação ou proposta ao cliente. Ele usou **"Gerar proposta ao
cliente"**, o sistema listou as duas cotações, escolheu a **COT-…-F015** e a
proposta saiu com os preços dela — **sem precisar gerar nova cotação** (esse trecho
da jornada está correto).

Então quis mudar a proposta **antes de emitir**: sair de **faturamento direto**
para **empreitada**. Nesse ponto da tela só enxergou as ações **imprimir, baixar
PDF e salvar**. Concluiu que estava "preso" e sem como editar.

### O que o código faz (verificado em teste na tela real, 2026-10-08)

- **A mudança é possível e é imediata.** Com a proposta já gerada, trocar a
  composição (radio "Empreitada" ↔ "Faturamento direto") **atualiza a proposta na
  hora**: a nota "materiais faturados diretamente pelo fornecedor" some, o total
  muda de R$ 1.449,28 (só serviços) para R$ 12.318,84 (materiais + serviços). O
  financeiro (`calcFinanceiro()`) é recalculado a cada render a partir desse
  estado — não exige gerar de novo.
- **O problema é de descoberta, não de capacidade.** A Composição fica **~2.300 px
  acima** da proposta, na seção "Lista de Engenharia". Entre uma e outra há o
  painel "Revisão", o "Resumo Financeiro Interno" e a própria proposta. Quem está
  olhando a proposta não vê a composição e **nada na proposta aponta para ela**.
- **O único botão de "voltar" ali engana.** O **"✏️ EDITAR"** (caixa de dados do
  cliente, canto da proposta) não abre composição nenhuma: ele só **apaga o
  orçamento gerado** (`setOrcamento(null)`) e some com a proposta. Quem clica
  espera editar e perde o que estava vendo.
- A barra inferior da proposta só tem saídas: imprimir, PDF, salvar — nenhuma ação
  de "ajustar composição" ou "voltar à configuração".
- **Não é regressão da correção de 06/10** (`2c49dcc`): com a lista aprovada a
  Composição já aparecia antes e depois dela; o desenho do fluxo é que a esconde
  por distância.
- Nome enganoso relacionado: o painel **"🔍 Revisão antes de gerar a proposta"**
  só aparece **depois** que o orçamento existe (`orcamento &&`) — "antes de gerar"
  quando na verdade já foi gerado.

### Causa raiz

A tela é uma **página única e longa** (checklist → lista → composição → revisão →
financeiro → proposta), e o passo seguinte ("ver/emitir a proposta") não mantém
**contexto nem atalho** para o passo anterior ("configurar"). A tela não tem a noção
de estágios (configurar → revisar → emitir), então quem chega no fim não vê a
saída de volta.

### Direção de correção (a decidir na correção única)

- **F.** Barra de ações na própria proposta com **"⚙️ Ajustar composição"** (rola até
  a seção e a destaca) — e um resumo do modo atual ("Faturamento direto · margem
  serviços 25% · imposto 6%") com link de edição, sempre visível junto da proposta.
- **G.** Trocar o **"✏️ EDITAR"** por algo que diga o que faz ("Fechar proposta"/
  "Refazer") e **não** apagar o orçamento sem confirmação; ou levá-lo à composição.
- **H.** Opcional: **painel de composição compacto fixo/flutuante** ao lado da proposta,
  já que a mudança é imediata — editar e ver o resultado na mesma tela.
- **I.** Renomear "Revisão antes de gerar a proposta" (ex: "Revisar preços e
  quantidades").
- **J.** Considerar dividir em **estágios** (Lista → Composição → Proposta) com
  navegação "voltar/avançar" explícita.

Decisão para o usuário: preferência entre F+G (menor mudança) e H/J (mudança
maior de layout).

---

## Achado 3 — Na "Revisão", a descrição do sistema some e aparece o nome genérico do fornecedor

### O que o usuário viu

No painel "Revisão antes de gerar a proposta" as linhas apareciam como
**"DANFOSS 018F6264"**, **"ELF ELFS10L"**, **"CURVA & COBRE"**, **"APIS DELTA"** —
em vez da descrição que o sistema gerou (ex: "Luva de Redução 7/8" x 1/2"",
"Curva 90 1 1/8"). Várias linhas "CURVA & COBRE" são indistinguíveis entre si.
Suspeita do usuário: a importação da cotação **substituiu** as descrições
originais, que são mais precisas.

### O que o código faz

- **A importação não sobrescreve a descrição original.** `confirmar_importacao`
  grava só `preco_unitario`, `marca_modelo_cotado`, `prazo`/`qtde_cotada` e `obs`
  em `cotacao_item`; `cotacao_item.descricao` (a do sistema) fica intacta.
- **O que o fornecedor cotou vai para `marca_modelo_cotado`.** O texto vem da IA
  (e é editável): para o PDF Brasifrio ela montou **MARCA + CÓDIGO DO FABRICANTE**
  (ex: "DANFOSS 018F6264", "ELGIN 45ESB4400TCC") e, nos itens sem código no PDF,
  **só a MARCA** ("CURVA & COBRE", "APIS DELTA"). Isso é informação útil (qual
  produto o fornecedor oferece), mas **não é uma descrição**.
- **A troca de nome acontece só na proposta**, em `nomeCorrigido()`
  (`GeradorOrcamento.jsx`): se o item estiver marcado em **"Fornecedor cotou: X —
  usar este item na proposta ao cliente"** (`itensSubstituidos[chave]`), o nome
  impresso passa a ser exatamente o `marca_modelo_cotado`. Esse mapa **é salvo
  com o projeto**. Não há nenhum código que marque isso automaticamente.
- Como os nomes da tela estão trocados, a opção **está ativa** para essas linhas
  (marcada na Revisão — talvez numa sessão anterior, já que fica salva). **A
  confirmar com o usuário:** se marcou "usar este item…" nelas.

### Falhas encontradas nesse mecanismo (independente de quem marcou)

1. **Substituir é perder a descrição.** O nome do fornecedor **troca** o do
   sistema em vez de somar. Com marca sem código, o resultado é inútil na
   proposta ("CURVA & COBRE" ×3 sem medida).
2. **A linha trocada perde o checkbox.** A Revisão busca a sugestão pela chave do
   **nome já trocado** (`norm(l.item)`), que não existe no mapa — então o
   checkbox "usar este item" **desaparece** e não há como desfazer na própria
   tela.
3. **Correções digitadas nessa linha são ignoradas.** Quantidade e preço manual
   da Revisão são gravados com a chave do nome trocado, mas a geração procura
   pela chave do **nome original** — sem casamento, a correção **não é aplicada**
   (sem aviso).
4. **O rótulo induz ao erro:** "usar este item na proposta ao cliente" pede uma
   confirmação que parece inofensiva, mas apaga a descrição do projeto; e aparece
   para **todos** os itens (a IA preenche a marca/modelo de todos), não só para os
   4 que ela sinalizou como `possivel_substituicao`.

### Causa raiz

O campo `marca_modelo_cotado` serve a dois papéis incompatíveis — **informação do
fornecedor** (sempre preenchida) e **nome substituto** (só para troca de produto) — e a
troca é por **substituição total**, com chave de correção que muda junto com o nome.

### Confirmação e decisão do usuário (2026-10-08)

O usuário **confirmou que marcou** "usar este item" de propósito, como teste da
substituição vinda do fornecedor — a troca de nome foi consequência disso. O teste
expôs a jornada confusa (descrição perdida, checkbox sumido, correção ignorada).
**Decisão:** ao aceitar o item do fornecedor, o sistema deve **manter a
descrição correta do sistema** e **acrescentar a marcação/oferta do fornecedor**
(direção K abaixo) — nunca substituir.

### Direção de correção (a decidir na correção única)

- **K.** *(direção aprovada pelo usuário)* Nunca trocar a descrição do sistema: exibir **a descrição do sistema como
  principal** e a do fornecedor como informação secundária ("Fornecedor: DANFOSS
  018F6264"). Se o usuário optar por usar o item do fornecedor, o nome na
  proposta vira **"descrição do sistema (fornecedor: marca/modelo)"**, ou o
  modelo entra no detalhe, nunca no lugar do nome.
- **L.** Chave estável: manter a chave **original** de cada item
  (`descricao_original`) no payload e na resposta (`detalhamento_itens`) e usá-la
  em checkbox, quantidade e preço manual — a linha nunca perde o controle nem a
  correção.
- **M.** A opção "usar o item do fornecedor" só aparece para itens que a IA marcou
  como **possível substituição** (ou que o usuário habilitar), **desmarcada** por
  padrão, com texto claro do efeito.
- **N.** Mostrar marca/modelo cotado em coluna própria na Revisão (e na planilha
  importada), com o código do fornecedor — útil para conferir a compra.
- **O.** Mostrar na Revisão mais contexto por linha (unidade, detalhe/medida),
  para linhas parecidas serem distinguíveis.

---

## Achado 4 — Atalho "Cotações → Gerar proposta" sem projeto aberto: de onde vem o projeto?

### O que o usuário fez e perguntou

Com o SaaS zerado (nenhum projeto carregado), foi direto ao painel **Cotações**.
Viu a lista de **todas** as cotações de **todos** os projetos, com status
(processada/enviada), e clicou **"Gerar proposta"** sem ter aberto projeto nenhum.
O sistema abriu o projeto certo, no Card 6, e mostrou as duas cotações
processadas (…-F015 do mesmo projeto) para escolher. Pergunta: *ele abriu a última
que eu tinha usado, ou abriu pela ligação entre cotação e projeto?*

### Resposta (confirmada no código)

**Pela ligação cotação → projeto** (`cotacao.projeto_id`), **não** pelo "último
projeto aberto" — o sistema não guarda "último aberto".

Passo a passo real:

1. Sem projeto aberto, o painel nasce em **"Todas"** (o seletor "Este projeto /
   Todas" só aparece quando há projeto aberto) → lista cotações de todos os
   projetos da empresa, em ordem de **criação, mais nova primeiro**
   (`order_by created_at desc`).
2. O botão **"GERAR PROPOSTA →"** (um só, no rodapé da lista, não por cotação) pega
   a **primeira cotação `processada` da lista exibida** — ou seja, **a processada
   criada mais recentemente em toda a empresa** (`cotacoesFiltradas.find(...)` em
   `PainelCotacoes.jsx`).
3. `App.jsx` compara o `projeto_id` dessa cotação com o projeto aberto; como não
   havia nenhum, **busca o projeto no banco** (`GET /projetos/{id}`), roda
   `carregarProjeto` + `irParaOrcamento` e dispara a geração automática.
4. Com o projeto carregado, a geração consulta **todas as cotações processadas
   daquele projeto** (`GET /cotacoes?projeto_id=…`): com **1**, usa direto; com
   **2 ou mais** (o caso dele), abre o modal "uma específica ou melhor preço por
   item". **A cotação F015 que ele escolheu foi escolhida nesse modal**, não na
   lista do painel.

Funciona, mas só deu certo porque a cotação "mais recente criada" era do projeto
que ele queria.

### Riscos / falhas desse atalho

1. **O alvo é escolhido em silêncio e por um critério que o usuário não vê:**
   "processada criada por último, em qualquer projeto". Havendo várias cotações de
   projetos diferentes, o botão pode abrir **outro projeto** que não o desejado.
   O usuário olha uma lista e acha que está escolhendo uma linha; o botão não
   depende de nenhuma linha.
2. **Auto-aprova a lista e gera a proposta direto** (efeito de
   `triggerGerarProposta`: `listaAprovada = true` + gerar). Após carregar o
   projeto, **a seleção de itens volta ao estado salvo** — e, sem seleção salva
   (caso do Achado 1), **tudo marcado** — então a proposta já nasce com a
   **lista inteira**, pulando a conferência. É o pior ponto de entrada para o
   problema do Achado 1.
3. **Troca o projeto aberto sem avisar.** Se já havia um projeto aberto com
   alterações não salvas e a cotação alvo é de outro, `carregarProjeto` o
   substitui **sem confirmação** (diferente do botão "Novo", que pergunta). O
   mesmo vale para abrir pelo Histórico. Risco de perder trabalho não salvo.
4. **Sem cotação processada, o botão vira "IR PARA O PROJETO →" e envia alvo
   nulo:** a tela abre o Card 6 do projeto que estiver aberto (ou vazio) e tenta
   gerar — comportamento mal definido.
5. A ordem é por **data de criação**, não pela de recebimento do fornecedor
   (`data_recebimento`); uma cotação antiga respondida agora não ganha prioridade.

### Direção de correção (a decidir na correção única)

- **Q.** Botão **por cotação** ("Gerar proposta com esta cotação") em cada linha, e
  mostrar o destino: "Abrir projeto *Frigorífico Barros* e gerar proposta com
  COT-…-F015".
- **R.** Ao chegar por este atalho, **não auto-aprovar nem gerar às cegas**: abrir o
  Card 6 já com a seleção reconciliada com a cotação (direção A do Achado 1) e um
  resumo ("27 itens da cotação · 4 fora dela") para o usuário confirmar.
- **S.** **Confirmar antes de trocar de projeto** quando houver alteração não
  salva (atalho e Histórico).
- **T.** Tratar explicitamente "sem cotação processada" (mensagem clara, nada de
  gerar vazio).
- **U.** Deixar visível, também sem projeto aberto, o filtro por projeto/cliente na
  lista de cotações (hoje só aparece com projeto aberto).

---

## Achado 5 — "A importação trocou a descrição pela marca" (reteste em produção)

### O que o usuário viu

Reteste com uma lista nova: desmarcou itens, gerou nova cotação e importou a
**mesma cotação do fornecedor** (PDF Brasifrio). Na lista de peças, o item
"Luva de cobre redutora 1.1/8 x 3/4" apareceu só como **"ELF"** — de novo a marca
no lugar da descrição. Pediu para verificar se a IA está fazendo isso.

### Verificação da IA (2026-10-08)

A análise do PDF foi rodada duas vezes com o mesmo PDF e a lista do projeto: sem
apelidos e **com** os apelidos que a primeira passada ensinaria. Em **todas as 27
linhas** a `descricao` devolvida é a **do sistema** (ex: "Luva de Redução 1.1/8" x
3/4""); a marca vai separada, em `marca_modelo` ("ELF", "CURVA & COBRE",
"DANFOSS 068-2032"…), e o texto do PDF em `descricao_pdf`. **A IA não troca a
descrição pela marca.** Também não há linhas extras nem apelidos distorcidos
("luva de cobre redutora" etc. são genéricos de propósito, sem a marca).

### Causa provável (a confirmar com o usuário)

A opção "usar este item / mencionar" (`itensSubstituidos`) **fica salva no projeto**
e é **indexada só pela descrição do item**. Marcada num teste anterior, ela continua
**ligada** quando chega uma cotação nova — e passa a valer para a oferta nova sem
ninguém marcar nada. No código **antigo** isso trocava o nome pelo `marca_modelo`
("ELF"), exatamente o que foi visto; no código **da entrega 1** o nome se mantém e
só ganha "(oferta: ELF)". Como o app é uma SPA, a aba aberta antes do deploy
continua rodando o JS antigo até **recarregar a página** (o bundle de produção já
tem a entrega 1 — verificado em 2026-10-08).

### Falha de desenho que sobra (mesmo com a entrega 1)

A marca "ligada" não pergunta de novo a cada cotação: a decisão "mencionar a oferta
do fornecedor" foi tomada para **uma oferta específica** (ex: ELF 1.1/8 do fornecedor
A), mas o sistema a guarda como um "sim" genérico do item. Uma cotação futura, de
outro fornecedor ou com outra marca, herda o "sim" sem o usuário saber.

### Direção de correção (a decidir)

- **V.** Guardar **qual oferta** foi aceita (o texto `marca_modelo`), não um sim/não:
  só vale enquanto a oferta atual for a mesma; oferta diferente → volta a perguntar.
  Flags antigas (booleanas) deixam de ser aplicadas.
- **W.** Quando a oferta é só uma **marca** (sem código — "ELF", "CURVA & COBRE"),
  não oferecer a menção na proposta: não acrescenta informação útil.

---

## Achado 6 — O sistema trata "marca" como se fosse "item substituto"

### O que o usuário viu (Revisão, após a entrega 1)

Em linhas como "Orifício de Expansão 6" aparece **"Fornecedor ofertou: DANFOSS —
mencionar na proposta ao cliente"** e o nome ganha **"(oferta: DANFOSS)"**. O
fornecedor, porém, só informou a **marca** (Danfoss) — o item é **o mesmo**, a
descrição do sistema está correta. A tela apresenta como "oferta/substituição" algo
que é só **marca**. O usuário aponta a confusão: o que está sendo sugerido trocar
é a descrição, e o que existe é apenas uma marca (que ele poderia **editar**).

### O que o código faz (verificado)

- `_gerarComCotacoes` (`GeradorOrcamento.jsx`) monta `ultimoModeloMapRef` com
  **todo** item cujo `marca_modelo_cotado` difere da descrição — e uma marca
  **sempre** difere da descrição. Resultado: **toda linha cotada** vira "oferta".
- A IA preenche `marca_modelo` com **MARCA + CÓDIGO** ("DANFOSS 068Z3409"), só a
  **MARCA** ("ELF", "CURVA & COBRE") ou, em substituições, o produto diferente
  ("IMPORTADO"). A mesma coluna mistura três coisas.
- A **substituição de verdade** (produto diferente do pedido) é identificada pela IA
  com `status = possivel_substituicao` + `obs` — mas esse status **não é gravado**
  em `cotacao_item` (só `marca_modelo_cotado` e `obs_fornecedor`), então a
  Revisão não consegue distinguir "só marca" de "item diferente". Na amostra da
  Brasifrio foram **4 de 27** os casos de substituição real (acumulador importado,
  tanque ELF 10L, isolamento KFLEX, quadro ELF).
- O texto da tela ("ofertou", "mencionar na proposta") e o efeito
  ("(oferta: …)" no nome) falam em substituição para qualquer marca.

### Causa raiz

Dois conceitos diferentes numa só coluna e numa só ação: **marca/modelo cotado**
(informação de compra, sempre existe) e **item substituto** (decisão rara, exige
atenção). O desenho antigo (entrega original, set/2026) só previa substituição; a
entrega 1 manteve o conceito e só trocou "substituir" por "acrescentar".

### Direção de correção (a decidir)

- **Y. Separar os dois conceitos.**
  1. **Marca** vira informação comum: em cada linha da Revisão, campo **"Marca"**
     editável (pré-preenchido pela cotação), sem nenhum rótulo de "oferta" ou
     "substituição". Opcionalmente impressa na proposta ("… — marca Danfoss").
  2. **Código do fabricante** (068Z3409) fica **interno** (Revisão, planilhas,
     compra) — não vai na proposta ao cliente.
  3. **Possível substituição** (item realmente diferente) ganha tratamento próprio,
     destacado, só para o que a IA sinalizou, com a explicação (`obs`) visível e uma
     decisão explícita. Para isso, gravar o sinal da IA em `cotacao_item`
     (coluna booleana nova, nullable, aditiva — migration 0044).
- **V e W** (propostas anteriores) ficam **superadas** por esta separação.
- **X** (edição na Revisão acende o aviso "recalcular") continua valendo.

**Decisões do usuário (2026-10-08):** aprovou as recomendações — a marca só aparece
na proposta quando marcada; o código do fabricante fica só interno; migration
aditiva autorizada. Implementado como Entrega 1b (ver tabela de andamento).

---

## Achado 7 — Complemento de 15 m volta como "1 un": a quantidade digitada na conferência não vale

### O que o usuário fez e viu (relato de 2026-10-14)

Na lista nova, acrescentou dois **complementos** livres — "Infraestrutura elétrica" e
"Infraestrutura mecânica", **15 metros** cada. Gerou a planilha de cotação e importou
o PDF do fornecedor (Brasifrio): os dois **não estavam no PDF**, e a conferência os
mostrou corretamente como não encontrados. Ele **corrigiu na própria conferência**,
digitando **quantidade e valor**. Ao gerar a proposta, o item entrou **como unidade
unitária (1 un)**, sem usar a quantidade que digitou.

### Verificação (reproduzida na tela real, 2026-10-14)

Cotação de teste com os dois complementos, preço R$ 100,00 e R$ 120,00, "Qtde cotada" 15,
projeto copiado, proposta gerada:

| Como o complemento está cadastrado no Card 6 | O que a proposta mostra |
|---|---|
| **15 m** (quantidade 15, unidade m) | "15 m — R$ 1.500,00" e "15 m — R$ 1.800,00" ✅ |
| **1 un** (quantidade padrão; os "15 metros" só no texto ou na cabeça) | "**1 un — R$ 100,00**" e "**1 un — R$ 120,00**" ❌ |

Ou seja, **é possível, e o resultado é exatamente o relatado** quando o complemento
está com a quantidade padrão (1 un).

### Causa

1. **"Qtde cotada" é só informativa** (decisão da entrega de 2026-10-06): grava em
   `cotacao_item.qtde_cotada` e nunca altera a quantidade da proposta. Mas a tela de
   conferência mostra o campo logo ao lado do preço, destaca em âmbar quando difere
   do pedido ("pedido: 1 un") — **parece que digitar ali corrige a quantidade**. Não
   corrige.
2. **O preço do fornecedor é sempre por unidade** ("Preço unitário") e o total é
   `preço × quantidade do complemento` (`precoComplemento(c) × c.qtde`). Com o
   complemento em 1 un, o total é só o preço.
3. **Os complementos não aparecem na "Revisão antes de gerar a proposta"** — ela
   lista só `orcamento.detalhamento_itens` (materiais + equipamentos); complemento
   vai direto da lista do Card 6 para a proposta (`complementosPreenchidos`). Então
   **não existe nenhum lugar, depois da importação, para corrigir quantidade/preço
   de um complemento** sem voltar à caixa de complementos e editar à mão.
4. Em item que **não veio no PDF**, o sistema não tem ao que se agarrar: a
   conferência não deixa claro que o valor digitado é **por unidade** nem em qual
   unidade (m, un).

### Escopo da correção (definido pelo usuário em 2026-10-14)

**Tudo o mais estava correto** — materiais, equipamentos, Revisão e conferência não
devem mudar. O único problema era o **complemento digitado à mão** que não vem no PDF do
fornecedor: ao importar, o usuário informa **quantidade e preço unitário** na
conferência e esses dados não chegavam à proposta (vinha "1 un").

Regra confirmada: **total = preço unitário da cotação × quantidade**, sempre, na unidade
em que foi cotado (por metro → valor por metro; por unidade; por pacote).

**Correção aplicada (somente complementos):** quando o preço do complemento vem da
cotação (e não foi digitado na própria caixa de complementos) e a importação trouxe
uma quantidade (`qtde_cotada`), essa quantidade vale na proposta, no PDF, na Lista de
Engenharia e no total. Nada mais foi alterado: itens normais continuam usando a
quantidade calculada (a "Qtde cotada" segue só informativa pra eles), a Revisão e a
tela de conferência ficam como estavam.

> Uma 1ª tentativa (2026-10-14) mexeu além do pedido (quantidade da cotação valendo pra
> todos os itens, complementos na Revisão, novos rótulos) e foi **desfeita** — fica
> registrado pra não repetir o excesso de escopo.

---

## Plano de correção e andamento

Combinado com o usuário em 2026-10-08: corrigir em **3 entregas**, cada uma testada
na tela e pushada antes da seguinte, sem migration em nenhuma.

| Entrega | Conteúdo | Situação |
|---|---|---|
| **1 — Integridade da proposta** | A, B (seleção × cotação, pergunta), D (origem do preço), K, L, M (descrição preservada, chave estável), R (atalho não gera às cegas) | ✅ implementada 2026-10-08 (C dispensada — a cotação passa a ser a fonte da seleção) |
| **1b — Marca × substituição** (Achados 5 e 6: Y + X; V/W superadas) | marca editável e opcional na proposta; código só interno; substituição só quando a IA sinaliza; aviso de correções pendentes; migration 0044 aditiva | ✅ implementada 2026-10-08 |
| **2 — Navegação da proposta** | F, G, I (e H/J opcionais) — "Ajustar composição" junto da proposta, "EDITAR" honesto, rename da Revisão | pendente |
| **3 — Atalho de Cotações** | Q, S, T, U — botão por cotação, confirmar troca de projeto, caso sem cotação processada, filtro visível | pendente |

Decisões do usuário até aqui: a seleção deve ser **perguntada** (não aplicada
sozinha); ao aceitar o item do fornecedor, **manter a descrição do sistema** e
acrescentar a oferta.

---

*(próximos achados da jornada entram abaixo)*
