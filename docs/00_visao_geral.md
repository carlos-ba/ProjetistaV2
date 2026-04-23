# 00 - Visão Geral do Projeto V2

## 1. Objetivo do Projeto

Este projeto nasce como uma nova versão independente, organizada e mais madura, construída a partir dos aprendizados obtidos no desenvolvimento do projeto V1.

O objetivo principal é criar uma base técnica limpa, escalável e preparada para produção, evitando a mistura de responsabilidades entre código, banco de dados, deploy, faturamento, frontend, backend e documentação.

O projeto V1 continuará servindo como ambiente de aprendizado, testes e referência, mas o projeto V2 deverá ser tratado como uma nova estrutura, com decisões técnicas mais claras desde o início.

---

## 2. Premissas Iniciais

As premissas iniciais do projeto são:

- Utilizar **Python** como linguagem principal do backend.
- Trabalhar no **PyCharm** como ambiente principal de desenvolvimento.
- Criar o projeto com **Git e GitHub desde o início**.
- Desenvolver o sistema com arquitetura baseada em **APIs**.
- Utilizar um frontend moderno, visualmente agradável e com boa experiência de usuário.
- Preparar o projeto para hospedagem em **Vercel (frontend) + Render (backend e banco)**.
- Separar claramente backend, frontend, documentação, infraestrutura, banco de dados e scripts.
- Criar documentação técnica desde o início para facilitar manutenção e evolução.
- Usar o V1 apenas como referência de aprendizado, não como base direta desorganizada.

---

## 3. Direção Técnica Inicial

A stack técnica inicial recomendada é:

| Camada | Tecnologia sugerida |
|---|---|
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL |
| Frontend | React ou Next.js |
| Estilização | Tailwind CSS |
| Versionamento | Git + GitHub |
| Ambiente local | PyCharm |
| Deploy futuro | Vercel + Render |
| Documentação | Markdown |
| Infraestrutura futura | Docker, Render Postgres, monitoramento e storage externo quando necessario |

Estas escolhas poderão ser ajustadas ao longo do projeto, mas devem servir como referência inicial para manter o desenvolvimento organizado.

---

## 4. Estrutura Inicial Recomendada

A estrutura inicial do projeto deverá seguir uma organização semelhante a esta:

```text
projeto-v2/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── database/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── styles/
│   └── package.json
│
├── docs/
│   ├── 00_visao_geral.md
│   ├── 01_requisitos.md
│   ├── 02_arquitetura.md
│   ├── 03_banco_de_dados.md
│   ├── 04_api.md
│   ├── 05_frontend.md
│   ├── 06_deploy_vercel_render.md
│   └── 07_decisoes_tecnicas.md
│
├── infra/
├── scripts/
├── tests/
├── .gitignore
├── README.md
└── docker-compose.yml
```

---

## 5. Papel do GitHub no Projeto

O GitHub deverá ser utilizado desde o primeiro dia para controlar as versões do projeto.

A lógica principal será:

```text
PyCharm / computador local
↓
Git local
↓
GitHub
```

O objetivo é garantir que cada avanço importante fique registrado, permitindo voltar versões, comparar mudanças e manter histórico técnico do desenvolvimento.

Fluxo básico recomendado:

```bash
git add .
git commit -m "estrutura inicial do projeto"
git push origin main
```

No início, o projeto poderá trabalhar apenas com a branch `main`.  
Depois, conforme o sistema crescer, poderá ser adotado o fluxo com branches:

```text
main        → versão estável
develop     → versão em desenvolvimento
feature/... → novas funcionalidades
```

---

## 6. Separação de Responsabilidades

Uma regra importante deste projeto será evitar misturar responsabilidades.

Cada parte do sistema deve ter uma função clara:

| Área | Responsabilidade |
|---|---|
| Backend | Regras de negócio, APIs, autenticação, integração com banco |
| Frontend | Interface do usuário e experiência visual |
| Banco de dados | Armazenamento estruturado das informações |
| Infraestrutura | Configuracao de deploy, Docker e operacao em nuvem |
| Documentação | Registro das decisões, regras e arquitetura |
| Scripts | Automatizações e comandos auxiliares |
| Testes | Validação do funcionamento do sistema |

---

## 7. Backend

O backend deverá ser construído com foco em API.

A recomendação inicial é utilizar:

```text
Python + FastAPI
```

O backend deverá ser responsável por:

- Receber requisições do frontend.
- Processar regras de negócio.
- Validar dados.
- Consultar e gravar informações no banco de dados.
- Controlar autenticação e permissões.
- Expor endpoints organizados.
- Registrar logs e erros importantes.
- Preparar o sistema para integrações futuras.

---

## 8. Frontend

O frontend deverá ser moderno, responsivo e com boa experiência visual.

A recomendação inicial é avaliar:

```text
React ou Next.js + Tailwind CSS
```

O frontend deverá ser responsável por:

- Apresentar as telas do sistema.
- Consumir as APIs do backend.
- Criar uma experiência de uso simples e profissional.
- Trabalhar bem em desktop, tablet e celular.
- Separar componentes visuais reutilizáveis.
- Manter consistência visual.

---

## 9. Banco de Dados

O banco de dados recomendado inicialmente é:

```text
PostgreSQL
```

Motivos da escolha:

- É robusto.
- É amplamente usado em produção.
- Tem boa compatibilidade com Python.
- Pode ser usado localmente e em producao no Render PostgreSQL.
- Suporta sistemas que crescem com mais segurança.

O projeto deverá evitar criar tabelas sem planejamento.  
Antes de implementar o banco, deverão ser definidos os principais módulos, entidades e relacionamentos.

---

## 10. Deploy e Operacao em Nuvem

O projeto adotara, como premissa inicial, a seguinte distribuicao:

| Plataforma | Uso |
|---|---|
| Vercel | Hospedagem do frontend |
| Render Web Service | Hospedagem do backend FastAPI |
| Render PostgreSQL | Banco de dados gerenciado |

Diretrizes iniciais:

- Backend e frontend devem continuar separados.
- Variaveis de ambiente devem ser usadas para URLs, credenciais e configuracoes.
- Nao armazenar arquivos importantes no filesystem efemero do backend.
- Manter logs, backups e monitoramento basico desde o inicio.

---

## 11. Regras de Organização do Projeto

Durante o desenvolvimento, deverão ser seguidas estas regras:

1. Não criar código sem entender a finalidade da função.
2. Não misturar backend com frontend.
3. Não colocar regra de negócio diretamente na interface.
4. Não alterar banco de dados sem documentar.
5. Não fazer deploy sem registrar versão no GitHub.
6. Não deixar senhas, tokens ou chaves dentro do código.
7. Não usar o V1 como cópia direta sem revisar.
8. Não instalar bibliotecas sem justificar o motivo.
9. Não criar arquivos soltos fora da estrutura definida.
10. Sempre documentar decisões técnicas importantes.

---

## 12. Uso de IA no Desenvolvimento

A IA poderá ser usada como apoio no desenvolvimento, mas com controle.

A IA deverá ajudar em:

- Criar estrutura de arquivos.
- Sugerir códigos.
- Explicar erros.
- Revisar arquitetura.
- Criar documentação.
- Gerar testes.
- Refatorar trechos de código.
- Criar prompts e checklists de desenvolvimento.

A IA não deverá decidir sozinha:

- Estrutura definitiva do banco.
- Regras críticas de negócio.
- Estratégia de segurança.
- Deploy de produção.
- Bibliotecas principais sem validação.

Toda sugestão de IA deverá ser revisada antes de entrar no projeto.

---

## 13. Objetivo da Documentação

A documentação deverá funcionar como memória técnica do projeto.

Ela deverá permitir que qualquer pessoa, ou agente de IA, entenda:

- O que o projeto faz.
- Como está organizado.
- Quais tecnologias usa.
- Como rodar localmente.
- Como testar.
- Como fazer deploy.
- Quais decisões técnicas foram tomadas.
- O que ainda está pendente.

---

## 14. Próximos Arquivos de Documentação

Após este arquivo, os próximos documentos recomendados são:

```text
01_requisitos.md
02_arquitetura.md
03_banco_de_dados.md
04_api.md
05_frontend.md
06_deploy_vercel_render.md
07_decisoes_tecnicas.md
```

Cada arquivo deverá tratar uma parte específica do projeto, evitando que todas as informações fiquem concentradas em um único documento.

---

## 15. Definição Estratégica

A definição estratégica inicial deste projeto é:

```text
Criar um projeto independente, limpo, organizado e escalavel, usando Python como base principal, APIs como padrao de comunicacao, frontend moderno para boa experiencia do usuario, GitHub como controle de versao e Vercel + Render como ambiente inicial de hospedagem.
```

Este documento deverá ser atualizado conforme o projeto evoluir.
