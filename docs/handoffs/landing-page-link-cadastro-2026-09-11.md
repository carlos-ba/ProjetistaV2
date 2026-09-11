# Handoff Claude → Codex — link "Começar minha avaliação" precisa carregar `?cadastro=1`

**Status:** aguardando Codex pegar
**Área:** `site-ecosistema/` (domínio do Codex, ver `AGENTS.md`)
**Contexto:** achado analisando a jornada de quem chega pela primeira vez no
SaaS via landing page (ver `CLAUDE.md`, seção "Chegada pela landing page —
abre direto em 'Criar Conta'", em produção desde 2026-09-11).

## O que está errado

Em `https://icenexus.com.br/projeto-camara-fria`
(`site-ecosistema/app/projeto-camara-fria/page.tsx`), o botão "Começar
minha avaliação" (plano "Avaliação gratuita") linka pra
`https://camara-fria.icenexus.com.br` — a URL nua, sem nenhum parâmetro.
Quem clica cai na tela de login pedindo usuário/senha de uma conta que
ainda nem existe, sem nenhuma orientação de que o caminho certo é "Criar
Conta". Achado revisando a experiência de primeiro acesso, sem nenhum
usuário reportar diretamente.

## O que precisa entrar no lugar

Trocar o `href` desse botão específico:

```diff
- href="https://camara-fria.icenexus.com.br"
+ href="https://camara-fria.icenexus.com.br/?cadastro=1"
```

Só nesse botão ("Começar minha avaliação" / Avaliação gratuita) — os
outros CTAs de planos pagos (`Solicitar contratação`, já linkados pro
checkout real desde o handoff de 2026-09-04) não mudam.

## Por que importa agora

Sem isso, quem chega pela landing page pra testar de graça esbarra numa
tela de login confusa (pedindo credencial de uma conta inexistente) antes
de sequer conseguir se cadastrar — perda de conversão logo no primeiro
passo do funil self-serve.

## O que já está pronto do nosso lado (sem mudança nenhuma sua além do link)

`LoginPage.jsx` já lê esse parâmetro: com `?cadastro=1` na URL, o app
abre direto na aba "Criar Conta" com um banner de boas-vindas ("👋
Bem-vindo! Crie sua conta gratuita para começar."); sem o parâmetro,
nada muda (continua abrindo em "Entrar", que é o certo pra quem já tem
conta). Já testado e em produção — só falta o link apontar pra lá.

## Fora de escopo deste handoff

- Qualquer mudança no app do SaaS (`backend/`/`frontend/`) — já está
  pronto e em produção.
- Os outros CTAs de planos pagos — sem mudança, já resolvidos no handoff
  de 2026-09-04.
