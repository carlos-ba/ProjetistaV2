# Scripts

Scripts de importação de catálogo e manutenção do banco de dados.

## Manutenção

| Script | Função |
|---|---|
| `copiar_prod_para_local.py` | Copia dados de produção para o banco local (protocolo COPY binário via psycopg3) |
| `auditar_banco.ps1` | Consultas de auditoria no banco local |
| `rodar_local.ps1` | Atalho para iniciar o backend local |

## Importação de Catálogo

| Script | Dados |
|---|---|
| `importar_paineis.py` | Painéis frigoríficos (fabricante, núcleo, espessura, largura) |
| `importar_portas.py` | Portas frigoríficas |
| `importar_evaporadoras.py` | Evaporadoras |
| `importar_vet.py` / `importar_vet_danfoss.py` | Válvulas de expansão termostática |
| `importar_separador.py` / `importar_separador_oleo.py` | Separadores de óleo |
| `importar_isolamento.py` | Isolamento de tubulação |
| `importar_excel.py` | Importação genérica via Excel |

## Planilhas de Referência

Cada script de importação possui uma planilha correspondente (`*_temp.xlsx`) com o formato esperado.

## Sincronização Produção → Local

```powershell
cd backend
& "..\venv\Scripts\python.exe" ..\scripts\copiar_prod_para_local.py
```

Executa no início de cada sessão de desenvolvimento para garantir que o banco local está alinhado com produção.

## Setup Inicial (novo computador)

```powershell
.\scripts\setup_novo_pc.ps1
```
