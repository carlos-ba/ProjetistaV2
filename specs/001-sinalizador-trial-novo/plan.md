# Plano — 001 sinalizador de trial novo

## Módulos afetados

| Arquivo | Mudança |
|---|---|
| `backend/alembic/versions/0047_empresa_lead_tratado_em.py` (novo) | `ADD COLUMN lead_tratado_em TIMESTAMP NULL`; `UPDATE empresa SET lead_tratado_em = now()` (regra 3); `downgrade` remove a coluna. |
| `backend/app/models/empresa.py` | Campo `lead_tratado_em: Mapped[Optional[datetime]]`. |
| `backend/app/services/auth.py` (`registrar_usuario`) | Nenhuma linha nova: o campo nasce nulo por padrão (regra 2). Só um teste garante isso. |
| `backend/app/api/routes_admin.py` | `EmpresaOut` ganha `lead_tratado_em`; `EmpresaUpdate` ganha `lead_tratado: bool \| None` (True grava `now()`, False limpa); `criar_empresa` grava `lead_tratado_em = now()` (H3). |
| `frontend/src/components/AdminEmpresas.jsx` | Bolinha + botão alternar na linha; contador na aba "Empresas"; `PATCH` com `{ lead_tratado }`. |

## Contratos

- `GET /api/v1/admin/empresas` → cada item ganha `lead_tratado_em: datetime \| null` (UTC marcado, mesmo cuidado do fix "-1 dias" de 16/09).
- `PATCH /api/v1/admin/empresas/{id}` aceita `{ "lead_tratado": true | false }` sem alterar os outros campos (o `PATCH` já ignora campos ausentes).
- Cálculo da cor no frontend: `status_assinatura === 'trial'` ? (`lead_tratado_em` ? verde : vermelho) : sem bolinha. Sem campo derivado no backend.

## Decisões

- **Campo de data, não booleano:** guarda também *quando* foi tratado, sem custo extra, e permite evolução futura (histórico) sem nova migration.
- **Sem retroatividade por migration**, não por lógica de data de corte: mais simples e auditável (regra 3).
- **Sem ADR:** não troca biblioteca nem abordagem.

## Riscos

- `lead_tratado_em` é coluna sem timezone (padrão do projeto) → marcar UTC ao devolver, como na Atividade de Usuários.
- Esquecer `lead_tratado_em` no mapeamento `EmpresaOut(**{c.name ...})` de `listar_empresas`: o campo só chega se estiver em `EmpresaOut.model_fields` (já é dinâmico, mas o teste A1 cobre).
- Backend local com `--reload` pode não pegar o modelo novo → reiniciar o servidor limpo (gotcha já documentado).
