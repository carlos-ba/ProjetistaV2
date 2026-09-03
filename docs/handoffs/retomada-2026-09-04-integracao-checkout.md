# Ponto de retomada — integração do Checkout TheMembers

**Registro:** encerramento dos trabalhos de 2026-09-03

**Retomada prevista:** 2026-09-04

**Responsável atual pela implementação:** Claude — núcleo do SaaS

## Situação ao encerrar o dia

- A especificação técnica do webhook foi preparada pelo Codex e publicada na branch `codex/especificacao-webhook-themembers-2026-09-03`.
- Documento principal: `docs/handoffs/especificacao-webhook-checkout-themembers-2026-09-03.md`.
- Commit da especificação: `b6f7607`.
- O Claude iniciou a integração no SaaS, mas o resultado da implementação ainda não foi revisado pelo Codex.
- Nenhuma afirmação de conclusão, deploy ou ativação do webhook deve ser feita sem nova verificação.
- A produção não deve receber eventos reais até que os payloads, IDs dos produtos, token, migrations e testes estejam confirmados.

## Ofertas e checkouts confirmados

| Oferta | Condição comercial publicada | Checkout |
|---|---|---|
| Avaliação gratuita | 15 dias e 1 projeto; cadastro direto no SaaS | fluxo atual de criação de conta |
| Profissional Mensal | R$ 159 por mês | `https://checkout.thebank.com.br/7501283916486672384` |
| Profissional Semestral | 6 × R$ 99, total R$ 594 | `https://checkout.thebank.com.br/7501283403359830016` |
| Premium — Engenharia e Capacitação | 6 × R$ 497, total R$ 2.982 | `https://checkout.thebank.com.br/7501282048323481600` |

Os números das URLs são apenas candidatos a identificadores do produto. O mapeamento definitivo depende dos campos recebidos nos payloads reais do Checkout.

## Contatos institucionais já definidos

- E-mail: `contato@icenexus.com.br`
- WhatsApp: `(11) 95721-4799`

## Regras técnicas que não devem ser perdidas

1. Usar a documentação de **Webhooks do Checkout**, não a da Área de Membros.
2. Validar o token estático recebido no cabeçalho `x-signature`.
3. Não reutilizar `Empresa.plano` para distinguir Mensal, Semestral e Premium.
4. Manter `Empresa.plano` como eixo técnico (`tecnico`/`empresa`) e criar `oferta_comercial` separadamente.
5. Tratar eventos com idempotência e auditoria.
6. Não criar automaticamente uma conta a partir do checkout.
7. Associar compra e conta pelo e-mail normalizado; compra sem conta deve permanecer pendente para reconciliação.
8. Produto desconhecido nunca pode liberar acesso.
9. Suspensão, cancelamento, estorno e chargeback precisam bloquear edição sem apagar projetos nem impedir leitura/exportação.
10. Nunca registrar token ou dados pessoais completos nos logs.

## Primeiras verificações na retomada

1. Receber do Claude a branch, o commit e o resumo exato do que foi implementado.
2. Conferir se a implementação partiu da `main` atualizada e não da branch das páginas comerciais.
3. Comparar a implementação com a especificação técnica, item por item.
4. Revisar migrations, modelos, endpoint, validação do `x-signature`, idempotência e regras de bloqueio.
5. Rodar os testes automatizados e verificar se o build permanece válido.
6. Confirmar que `.env.example` foi atualizado sem incluir segredos.
7. Confirmar que nenhuma variável real, token ou dado pessoal foi commitado.
8. Validar payload sanitizado de cada oferta antes de aceitar os IDs dos produtos.
9. Fazer deploy inicialmente com o processamento desabilitado.
10. Só cadastrar/ativar o webhook no painel TheMembers depois da revisão técnica e de uma transação controlada.

## Estado das páginas comerciais

As mudanças comerciais estão isoladas na branch `codex/ofertas-checkout-2026-09-03`, no diretório de trabalho `D:\Projetos\paginas comerciais\work\ProjetistaV2-codex-ofertas`.

Commits conhecidos:

- `c440c70` — ofertas e links de checkout;
- `a675548` — contatos institucionais.

Preview conhecida:

`https://icenexus-site-ku1cglxcp-carlos-bas-projects.vercel.app/projeto-camara-fria#planos`

Essas mudanças não devem ser misturadas à branch de implementação do webhook.

## Pergunta de abertura para amanhã

Solicitar ao Claude: branch usada, commits realizados, arquivos modificados, testes executados, resultado dos testes, migrations criadas, variáveis necessárias e se houve qualquer deploy ou configuração no painel TheMembers/Render.
