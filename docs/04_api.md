# 04 - API

Atualizado em: 2026-06-28

---

## 1. Padrões Gerais

- Formato: JSON
- Prefixo: `/api/v1`
- Autenticação: Bearer token JWT (header `Authorization: Bearer <token>`)
- Timezone: UTC em campos de data/hora
- Erros padronizados pelo FastAPI (422 para validação, 401 para não autenticado, 404 para não encontrado)

---

## 2. Autenticação

### POST `/api/v1/auth/login`
- Body: `{"email": "...", "senha": "..."}`
- Retorna: `{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}`

### POST `/api/v1/auth/refresh`
- Body: `{"refresh_token": "..."}`
- Retorna: novo `access_token`

### POST `/api/v1/auth/register`
- Cadastro de novo usuário

---

## 3. Projetos

### GET `/api/v1/projetos`
- Lista projetos do usuário autenticado

### POST `/api/v1/projetos`
- Cria novo projeto
- Body: `{"nome": "...", "cliente_id": null}`

### PATCH `/api/v1/projetos/{id}`
- Atualiza projeto (incluindo `dados_completos` — estado serializado de todos os cards)

---

## 4. Clientes

### GET `/api/v1/clientes`
- Lista clientes do usuário autenticado

### POST `/api/v1/clientes`
- Body: `{"nome": "...", "email": "...", "telefone": "...", "endereco": "..."}`

---

## 5. Catálogo

### GET `/api/v1/catalogo/paineis/fabricantes`
- Retorna fabricantes de painéis PIR com suas linhas e espessuras disponíveis
- Carregado no `App.jsx` na inicialização com retry automático

### GET `/api/v1/catalogo/portas`
- Retorna fabricantes e modelos de portas frigoríficas

---

## 6. Card 1 — Gabinete

### POST `/api/v1/gabinete`
- Body: dimensões, painel PIR escolhido, portas, temperatura interna, tipo de piso
- Retorna: `lista_corte` (painéis por parede), materiais, área total

---

## 7. Card 2 — Carga Térmica

### POST `/api/v1/carga-termica`
- Body: dimensões, painel, T.Amb, T.Interna, produto, ocupação, iluminação, método (simplificado/psicrométrico)
- Retorna: carga total (kcal/h) + breakdown por fonte

---

## 8. Card 3 — Seleção de Equipamentos

### POST `/api/v1/selecao`
- Body: `{"capacidade_kcalh": float, "fluido": "R404A", "temp_evaporacao": int, "temp_ambiente": int}`
- Retorna: lista de UCs compatíveis + lista de evaporadoras compatíveis, ordenadas por aderência

---

## 9. Card 4 — Tubulação

### POST `/api/v1/tubulacao`
- Body: distâncias por trecho, fluido, capacidade, T.Evap, T.Amb
- Retorna: bitolas ASHRAE por trecho, sugestão de isolamento Armacel

### GET `/api/v1/tubulacao/sugestao-isolamento`
- Query: `?temp_evap=-25`
- Retorna: padrão de isolamento sugerido (D/F/H/M/R/T) + descrição

---

## 10. Card 5 — Componentes de Fluxo

### POST `/api/v1/componentes`
- Body: `{"capacidade_kcalh": float, "fluido": "...", "temp_evap": int}`
- Retorna: separador de líquido e separador de óleo selecionados do banco

### POST `/api/v1/solenoide/selecionar`
- Body: `{"fluido": "R404A", "te_c": -25, "tc_c": -15, "capacidade_kw": 5.8, "dp_bar": 0.10}`
- Retorna: modelo EVR v2 selecionado (Danfoss), Kv calculado, capacidade na condição
- Fluidos suportados: R404A e R22

### POST `/api/v1/acessorios/selecionar`
- Body: `{"fluido": "...", "capacidade_kcalh": float, "tem_tanque_liquido": bool, "bitola_liquido": "..."}`
- Retorna: filtro secador (DML ou DMC) + visor de líquido (SGN)

### POST `/api/v1/carga-fluido/estimar`
- Body: `{"fluido": "...", "volume_interno_evap_kg": float, "bitola_liquido": "...", "comprimento_liquido_m": float, "bitola_succao": "...", "comprimento_succao_m": float}`
- Retorna: `{carga_evaporador_kg, carga_linha_liquido_kg, carga_linha_succao_kg, carga_total_kg}`

### POST `/api/v1/tanque-liquido/selecionar`
- Body: `{"carga_total_kg": float, "fluido": "..."}`
- Retorna: tanque vertical selecionado (Castel ou RAC) via NBR 16.069

### POST `/api/v1/cavalete/analisar`
- Body: bitolas de cada trecho, comprimentos, equipamentos selecionados
- Retorna: lista de luvas de redução, porcas de union, luvas de passagem por trecho

---

## 11. Card 6 — Orçamento e Proposta

### POST `/api/v1/orcamento`
- Body: todos os itens dos cards anteriores
- Retorna: lista consolidada de materiais + equipamentos para orçamento

### POST `/api/v1/cotacao`
- Cria cotação e gera planilha Excel para envio ao fornecedor

### GET `/api/v1/cotacao/{id}`
- Retorna dados da cotação

### PATCH `/api/v1/cotacao/{id}`
- Importa planilha devolvida com preços preenchidos

### POST `/api/v1/proposta`
- Gera proposta comercial em PDF com preços da cotação

---

## 12. Configurações

### GET `/api/v1/configuracoes/montagem`
- Retorna perfil de montagem do usuário autenticado

### POST `/api/v1/configuracoes/montagem`
- Salva perfil de montagem (tipo filtro, visor, trechos, flags de inclusão)

---

## 13. Utilitários

### GET `/api/v1/health`
- Retorna `{"status": "ok"}` — health check para o Render

---

## 14. Modelo de Erros

```json
{
  "detail": "Mensagem de erro"
}
```

Para erros de validação (422):
```json
{
  "detail": [
    {
      "loc": ["body", "campo"],
      "msg": "descrição do erro",
      "type": "tipo_do_erro"
    }
  ]
}
```
