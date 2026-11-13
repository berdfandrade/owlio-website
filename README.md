# Site do Owlio

No ar em https://berdfandrade.github.io/owlio-website/

Página de apresentação do [Owlio](https://github.com/berdfandrade/owlio), em português (`index.html`) e inglês (`en/index.html`), feita com Vite e o kit da taste skill.

```bash
npm install
npm run dev      # servidor local com recarga
npm run build    # gera o site estático em dist/
```

## Link de download

O botão "Baixar para Windows" lê o link do arquivo `.env`:

```
VITE_DOWNLOAD_URL=https://github.com/berdfandrade/owlio/releases/latest
```

Troque pelo link direto do instalador e rode `npm run build` de novo. O link aparece no menu, no topo e no fim das duas páginas.

## Onde fica cada coisa

- `index.html`, `en/index.html`: as duas páginas.
- `src/site.css`, `src/main.js`: o estilo do site e a animação do cartão do Enter no topo.
- `public/assets/`: o kit da taste skill (sistema, movimento, fragmentos e momentos), servido como arquivos soltos.
- `public/shots/pt/` e `public/shots/en/`: capturas reais do Owlio em WebP, tiradas do app aberto com os roteiros de exemplo (`examples/`), com a interface em português e em inglês.

## Publicação

Cada push na `main` roda a Action `.github/workflows/deploy.yml`, que gera o site e publica no GitHub Pages.

O site fica em `/owlio-website/` (o `base` em `vite.config.js`). Com um domínio próprio, troque o `base` por `'/'`.
