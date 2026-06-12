# Tests

Pasta reservada para testes de integração e E2E entre camadas.

## Testes de Backend

Os testes unitários do backend estão em `backend/tests/`.

```powershell
cd backend
..\.venv\Scripts\pytest.exe tests/
```

## Testes E2E

A serem implementados conforme a base de usuários cresce e os fluxos críticos se estabilizam.

Fluxos prioritários para cobertura futura:
- Cálculo de carga térmica (valores esperados por tipo de carga)
- Seleção de equipamentos (interpolação de capacidade)
- Geração e importação de planilha de cotação
- Geração de proposta comercial (gross-up, impostos)
