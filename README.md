# Projetista V2

Projeto V2 iniciado a partir de uma base limpa, organizada e escalavel, conforme `docs/00_visao_geral.md`.

## Estrutura inicial

- `backend/`: API em Python com FastAPI.
- `frontend/`: aplicacao frontend separada do backend.
- `docs/`: documentacao tecnica do projeto.
- `infra/`: arquivos de infraestrutura e deploy.
- `scripts/`: scripts de apoio.
- `tests/`: testes em nivel de projeto.

## Primeiros passos

1. Ler `docs/00_visao_geral.md`.
2. Definir requisitos em `docs/01_requisitos.md`.
3. Evoluir arquitetura em `docs/02_arquitetura.md`.
4. Padronizar ambiente:

```powershell
.\scripts\setup_backend.ps1
.\scripts\run_backend.ps1
```

## Stack inicial (referencia)

- Backend: Python + FastAPI
- Banco: PostgreSQL
- Frontend: React ou Next.js
- Infra futura: Docker + AWS

## Comandos padrao

O projeto possui:

- `Makefile` com alvos de setup e execucao do backend.
- scripts PowerShell em `scripts/` para uso no Windows.
