# Site do ecossistema IceNexus

Site institucional e comercial publicado em
[www.icenexus.com.br](https://www.icenexus.com.br). O projeto apresenta o
ecossistema IceNexus e encaminha os visitantes para seus produtos e ambientes.

## Rotas principais

- `/`: página de entrada do ecossistema.
- `/projeto-camara-fria`: apresentação e oferta do Projeto de Câmara Fria.
- `/academia`: apresentação da Academia IceNexus.
- `/acessar`: acesso aos produtos disponíveis.
- `/contratar/[plan]`: compatibilidade com links antigos; redireciona para os planos.
- `/treinamentos`: compatibilidade com links antigos; redireciona para a Academia.

## Desenvolvimento

Requisitos: Node.js 22.13 ou superior.

```bash
npm install
npm run dev
```

Verificações locais:

```bash
npm run lint
npm run build
```

## Publicação

O projeto `icenexus-site` está conectado ao repositório
`carlos-ba/ProjetistaV2` na Vercel, com `site-ecosistema` como diretório raiz.

- `main`: produção em `www.icenexus.com.br`.
- outras branches: deployments de Preview para validação antes da produção.

## Limites atuais

- A autenticação real acontece nos ambientes próprios de cada produto.
- O site não implementa banco de dados, checkout ou autenticação ChatGPT.
- Informações comerciais devem ser alteradas somente após validação da oferta correspondente.
