// Scripts próprios do site: o botão de tema e o cartão do Enter sobre a captura do hero.

const pt = document.documentElement.lang.startsWith('pt');
const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

// Tema: o <head> já aplicou o tema guardado ou o do sistema. O botão troca e guarda a escolha;
// sem escolha guardada, a página acompanha o sistema quando ele muda.
const root = document.documentElement;
const themeColor = document.querySelector('meta[name="theme-color"]');
const toggle = document.querySelector('[data-theme-toggle]');
function applyTheme(t) {
  root.dataset.theme = t;
  if (themeColor) themeColor.content = t === 'dark' ? '#17181c' : '#f7f7f5';
  toggle?.setAttribute('aria-pressed', String(t === 'dark'));
}
applyTheme(root.dataset.theme === 'dark' ? 'dark' : 'light');
toggle?.addEventListener('click', () => {
  const t = root.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(t);
  try { localStorage.setItem('theme', t); } catch (e) {}
});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
  let saved = null;
  try { saved = localStorage.getItem('theme'); } catch (err) {}
  if (!saved) applyTheme(e.matches ? 'dark' : 'light');
});

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
