# Handoff Claude → Codex — ligar os links de checkout reais na landing page

**Status:** aguardando Codex pegar
**Área:** `site-ecosistema/` (domínio do Codex, ver `AGENTS.md`)
**Contexto:** achado testando a jornada completa de compra do webhook do
Checkout TheMembers (ver `CLAUDE.md`, seção "Webhook do Checkout TheMembers"
— Etapa 1 + revisão + payload real, já em produção desde 2026-09-04).

## O que está errado

Em `https://icenexus.com.br/projeto-camara-fria`, os botões "Solicitar
contratação" dos 3 planos ainda apontam para
`mailto:financeiro@icenexus.com.br?subject=...` — um placeholder que nunca
foi trocado pelo link de checkout real, mesmo o Checkout já estar
configurado e funcionando na TheMembers (testado com uma compra real em
2026-09-04, via Pix, webhook confirmado ponta a ponta).

## O que precisa entrar no lugar

Os 3 links reais de checkout (`checkout.thebank.com.br`, confirmados hoje
direto no painel da TheMembers — `Produto → Icenexus Premium → Ofertas`):

| Oferta | Preço | Link |
|---|---:|---|
| Profissional Mensal | R$ 159/mês (recorrente) | `https://checkout.thebank.com.br/7501283916486672384` |
| Profissional Semestral | 6× R$ 99 (R$ 594, venda única, 183 dias) | `https://checkout.thebank.com.br/7501283403359830016` |
| Premium — Engenharia e Capacitação | 6× R$ 497 (R$ 2.982, venda única, 183 dias) | `https://checkout.thebank.com.br/7501282048323481600` |

Trocar o `href` de cada botão de plano pelo link correspondente. Sem lógica
nova — é literalmente destino do link, o checkout inteiro (formulário,
cobrança, confirmação) já é hospedado e resolvido pela TheMembers/TheBank.

## Por que importa agora

Sem isso, ninguém consegue assinar sozinho pela landing page — todo tráfego
de conversão self-serve cai num e-mail manual em vez de fechar a venda
automaticamente, que é o objetivo central dessa fase do lançamento (ver
`project-jornada-assinatura-saas` na memória do Claude — "só o técnico
assina de forma automática").

## Fora de escopo deste handoff

- Confirmar/cadastrar de propósito que Semestral e Premium não são
  assinatura recorrente (venda única com prazo fixo) — já validado, não
  precisa reconfirmar no lado da TheMembers.
- Qualquer mudança no backend/webhook — já está pronto e em produção.
