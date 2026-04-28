# 03 - Banco de Dados

Modelagem minima para o teste de arquitetura SDD do MVP.

## 1. Entidades do MVP

### Projeto

- `id` (UUID, PK)
- `nome` (varchar 120, not null)
- `status` (varchar 30, default `rascunho`)
- `created_at` (timestamp, not null)
- `updated_at` (timestamp, not null)

### Calculo

- `id` (UUID, PK)
- `projeto_id` (UUID, FK -> projeto.id, not null)
- `payload_entrada` (jsonb, not null)
- `resultado` (jsonb, not null)
- `versao_regra` (varchar 20, not null)
- `created_at` (timestamp, not null)

## 2. Relacionamentos

- 1 `Projeto` para N `Calculo`.
- Exclusao de projeto:
  - opcao recomendada para MVP: `ON DELETE CASCADE` em `calculo.projeto_id`.

## 3. Regras de Integridade

- `nome` de projeto obrigatorio.
- Todo calculo deve referenciar projeto existente.
- `payload_entrada` e `resultado` devem ser JSON valido.
- `versao_regra` obrigatoria para rastreabilidade.

## 4. Indices Minimos

- `idx_calculo_projeto_id` em `calculo(projeto_id)`.
- `idx_projeto_created_at` em `projeto(created_at desc)`.

## 5. Estrategia de Migracao

- Ferramenta recomendada: Alembic.
- Padrao:
  1. criar migration para tabelas base;
  2. aplicar em ambiente local;
  3. aplicar em homologacao/producao via pipeline.
