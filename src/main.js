// Animação própria do site: o cartão do Enter sobre a captura do hero.
// Fica parado quando o sistema pede menos movimento.

const pt = document.documentElement.lang.startsWith('pt');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

// O cartão do hero: a tecla Enter é apertada e o próximo elemento aparece.
const card = document.querySelector('.float-card');
if (card && !reduced) {
  const key = card.querySelector('.float-card__key');
  const text = card.querySelector('.float-card__text');
  // [tecla, antes, quem, meio, próximo elemento]
  const steps = pt
    ? [['Enter', 'depois de ', 'TOMÁS', ' começa o ', 'Diálogo'],
       ['Enter', 'depois da ', 'fala', ' vem outro ', 'Personagem'],
       ['Tab', 'numa ', 'ação vazia', ' vira ', 'Personagem']]
    : [['Enter', 'after ', 'TOMAS', ' starts the ', 'Dialogue'],
       ['Enter', 'after the ', 'line', ' comes the next ', 'Character'],
       ['Tab', 'on an ', 'empty action', ' turns it into ', 'Character']];
  const b = (s, next) => { const el = document.createElement('b'); el.textContent = s; if (next) el.dataset.next = ''; return el; };
  let i = 0;
  setInterval(() => {
    i = (i + 1) % steps.length;
    const [k, before, who, mid, next] = steps[i];
    key.textContent = k;
    key.classList.add('is-press');
    setTimeout(() => key.classList.remove('is-press'), 180);
    text.replaceChildren(before, b(who), mid, b(next, true));
  }, 3200);
}

// "Baixar para Windows" vai direto para o instalador da versão mais recente no GitHub.
// O link do build (VITE_DOWNLOAD_URL) já vem resolvido pelo deploy; aqui ele só é atualizado
// se saiu uma versão nova depois da última publicação do site. Sem rede, fica o link do build.
fetch('https://api.github.com/repos/berdfandrade/owlio/releases/latest', {
  headers: { Accept: 'application/vnd.github+json' },
})
  .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
  .then((release) => {
    const exe = release.assets.find((a) => /^Owlio-Setup-.*\.exe$/.test(a.name));
    if (!exe) return;
    for (const a of document.querySelectorAll('a[data-download]')) a.href = exe.browser_download_url;
  })
  .catch(() => {});
