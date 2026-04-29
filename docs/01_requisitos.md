# 01 - Requisitos do Projeto V2

**Versão:** 1.0
**Data:** 2026-04-28
**Status:** Em definição

---

## 1. Visão Geral do Produto

O **Projetista V2** é um sistema web voltado para profissionais técnicos que precisam calcular e gerar listas de peças/materiais a partir de parâmetros de entrada de um projeto.

O sistema deve permitir que o usuário informe os dados de um projeto, receba o resultado do cálculo automaticamente e possa salvar e consultar resultados anteriores.

> **PENDENTE:** Confirmar o domínio específico do sistema.
> Exemplos: projeto elétrico, projeto hidráulico, estrutura metálica, orçamento de construção, etc.

---

## 2. Perfis de Usuário

### 2.1 Usuário Final (MVP)

- Profissional técnico que realiza projetos e precisa gerar listas de materiais.
- Acessa o sistema pelo navegador (desktop prioritário).
- Pode ou não ter conhecimento técnico em TI.
- Espera uma interface simples, rápida e confiável.

> **PENDENTE:** Haverá múltiplos tipos de usuário (ex: administrador vs. usuário comum)?
> No MVP, assumimos um único perfil de usuário autenticado.

---

## 3. Requisitos Funcionais

Os requisitos funcionais descrevem o que o sistema deve fazer.

### RF-01 — Autenticação de Usuário

- O sistema deve permitir que o usuário faça login com e-mail e senha.
- O sistema deve manter a sessão autenticada enquanto o token for válido.
- O sistema deve permitir logout.

> **PENDENTE:** Haverá cadastro público ou os usuários serão criados manualmente?
> No MVP, assumimos cadastro via e-mail com senha.

---

### RF-02 — Entrada de Dados do Projeto

- O usuário deve poder preencher um formulário com os parâmetros do projeto.
- O sistema deve validar os campos obrigatórios antes de processar.
- O sistema deve informar erros de forma clara ao usuário.

> **PENDENTE:** Quais são os campos do formulário?
> Definir: nome dos campos, tipos (número, texto, seleção), unidades, obrigatoriedade.

---

### RF-03 — Cálculo da Lista de Peças/Materiais

- O sistema deve processar os dados de entrada e calcular a lista de materiais necessários.
- O cálculo deve ser executado no backend (nunca no frontend).
- O resultado deve ser retornado ao usuário em formato estruturado e legível.

> **PENDENTE:** Qual é a lógica de cálculo?
> Definir: fórmulas, tabelas de referência, coeficientes, regras de arredondamento.

---

### RF-04 — Exibição do Resultado

- O sistema deve exibir o resultado do cálculo em forma de lista/tabela.
- A lista deve mostrar: item, descrição, quantidade e unidade de medida.
- O usuário deve poder visualizar o resultado antes de salvar.

> **PENDENTE:** O resultado deve ser exportável (PDF, Excel)?
> No MVP, apenas exibição em tela. Exportação fica para versão futura.

---

### RF-05 — Salvamento do Projeto

- O usuário deve poder salvar o projeto com um nome identificador.
- O sistema deve associar o projeto ao usuário autenticado.
- O sistema deve confirmar o salvamento com feedback visual.

---

### RF-06 — Consulta de Projetos Salvos

- O sistema deve listar os projetos salvos pelo usuário autenticado.
- O usuário deve poder abrir um projeto salvo e visualizar seus dados e resultado.
- O usuário deve poder excluir um projeto salvo.

> **PENDENTE:** O usuário deve poder reeditar e recalcular um projeto salvo?
> No MVP, assumimos apenas leitura. Edição fica para versão futura.

---

## 4. Requisitos Não Funcionais

Os requisitos não funcionais descrevem como o sistema deve se comportar.

### RNF-01 — Desempenho

- O cálculo deve ser processado e retornado em menos de 3 segundos para projetos de tamanho padrão.
- A interface deve carregar em menos de 2 segundos em conexões convencionais.

### RNF-02 — Disponibilidade

- O sistema deve ter disponibilidade mínima de 99% (excluindo janelas de manutenção planejadas).
- O ambiente de produção (Render + Vercel) é o responsável pelas garantias de uptime.

### RNF-03 — Segurança

- Nenhum dado sensível (senhas, tokens) deve ser armazenado em texto puro.
- A comunicação entre frontend e backend deve ocorrer exclusivamente via HTTPS.
- O backend deve validar e sanitizar todos os dados de entrada.
- Tokens de autenticação devem ter prazo de expiração definido.

### RNF-04 — Escalabilidade

- O backend deve ser stateless, permitindo escalonamento horizontal.
- O banco de dados deve ser o único ponto de estado persistente.

### RNF-05 — Manutenibilidade

- O código deve seguir a separação de camadas definida na arquitetura (api, services, models, schemas).
- Toda decisão técnica relevante deve ser registrada em `docs/07_decisoes_tecnicas.md`.
- O banco de dados deve usar migrations para controle de schema.

### RNF-06 — Usabilidade

- A interface deve funcionar corretamente em navegadores modernos (Chrome, Firefox, Edge, Safari).
- A interface deve ser responsiva para desktop (prioridade) e tablet.

---

## 5. Fluxo Principal do Usuário (MVP)

```text
1. Usuário acessa o sistema
2. Usuário faz login com e-mail e senha
3. Usuário acessa a tela de novo projeto
4. Usuário preenche os parâmetros do projeto
5. Usuário clica em "Calcular"
6. Sistema processa o cálculo no backend
7. Sistema exibe a lista de materiais resultante
8. Usuário nomeia e salva o projeto
9. Usuário pode consultar projetos salvos anteriormente
```

---

## 6. Fora do Escopo do MVP

Os itens abaixo são reconhecidos como necessários no futuro, mas **não fazem parte do MVP**:

- Exportação de resultados em PDF ou Excel
- Edição de projetos salvos e recálculo
- Compartilhamento de projetos entre usuários
- Painel administrativo
- Gestão de planos/assinatura (SaaS billing)
- Integração com ERPs ou sistemas externos
- Aplicativo mobile
- Modo offline

---

## 7. Restrições e Premissas

| Item | Descrição |
|---|---|
| Linguagem do sistema | Português (pt-BR) |
| Plataforma alvo | Web (navegador) |
| Autenticação MVP | E-mail + senha (JWT) |
| Deploy | Vercel (frontend) + Render (backend + banco) |
| Banco de dados | PostgreSQL (Render managed) |
| Backend | Python + FastAPI |
| Frontend | React ou Next.js + Tailwind CSS |
| Comunicação | REST API (JSON) |
| Versionamento | Git + GitHub |

---

## 8. Pendências Críticas para Inicio do Desenvolvimento

Antes de implementar qualquer código de negócio, os seguintes pontos devem ser respondidos e documentados:

| # | Questão | Impacto |
|---|---|---|
| P1 | Qual o domínio do sistema? (elétrico, hidráulico, etc.) | Define todo o modelo de dados e lógica de cálculo |
| P2 | Quais são os campos de entrada do formulário? | Define o schema de entrada da API e o formulário do frontend |
| P3 | Qual é a lógica/fórmula de cálculo? | Define a camada de serviço do backend |
| P4 | Quais são os campos e unidades da lista de resultado? | Define o schema de saída da API e a exibição do frontend |
| P5 | O cadastro de usuário é aberto ou controlado? | Define o fluxo de autenticação e os endpoints necessários |

---

## 9. Histórico de Versões

| Versão | Data | Autor | Descrição |
|---|---|---|---|
| 1.0 | 2026-04-28 | Equipe + IA | Estrutura inicial criada com base na visão geral e próximos passos |
