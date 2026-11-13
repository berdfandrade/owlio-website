# Site do Owlio

No ar em https://berdfandrade.github.io/owlio-website/

Página de apresentação do [Owlio](https://github.com/berdfandrade/owlio), em português (`index.html`) e inglês (`en/index.html`), feita com Vite e o kit da taste skill.

```bash
npm install
npm run dev      # servidor local com recarga
npm run build    # gera o site estático em dist/
```

## Link de download

O botão "Baixar para Windows" aponta direto para o instalador da versão mais recente do Owlio (por exemplo `https://github.com/berdfandrade/owlio/releases/download/v0.1/Owlio-Setup-0.1.exe`), sem precisar editar nada a cada versão:

- **No deploy**, a Action consulta a última release do `berdfandrade/owlio` e põe o link do `Owlio-Setup-*.exe` nas páginas. Ela roda a cada push e também uma vez por dia.
- **Ao abrir a página**, o `src/main.js` consulta a API do GitHub de novo e atualiza o botão, caso tenha saído uma versão depois do último deploy.
- **Sem instalador publicado**, fica o link do `.env` (a página de releases).

O link aparece no menu, no topo e no fim das duas páginas.

## Onde fica cada coisa

- `index.html`, `en/index.html`: as duas páginas.
- `src/site.css`, `src/main.js`: o estilo do site e a animação do cartão do Enter no topo.
- `public/assets/`: o kit da taste skill (sistema, movimento, fragmentos e momentos), servido como arquivos soltos.
- `public/shots/pt/` e `public/shots/en/`: capturas reais do Owlio em WebP, tiradas do app aberto com os roteiros de exemplo (`examples/`), com a interface em português e em inglês.

## Publicação

Cada push na `main` roda a Action `.github/workflows/deploy.yml`, que gera o site e publica no GitHub Pages.

O site fica em `/owlio-website/` (o `base` em `vite.config.js`). Com um domínio próprio, troque o `base` por `'/'`.
