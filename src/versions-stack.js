// A pilha de Versões da seção #versoes: as cópias do roteiro empilhadas em perspectiva, como na
// janela Versões do Owlio. Ao rolar a página pela seção, a cópia da frente recua para o fundo e a
// próxima, mais antiga, vem para a frente; a data dela acende na linha do tempo ao lado.

const SCRIPT = {
  pt: {
    file: 'a_ultima_sessao.fountain',
    page: 'p. 1',
    stamps: [['Agora', 'agora'], ['12 nov.', '12 nov., 16:40'], ['11 nov.', '11 nov., 22:08'], ['9 nov.', '9 nov., 11:31'],
             ['6 nov.', '6 nov., 18:55'], ['3 nov.', '3 nov., 10:20'], ['29 out.', '29 out., 14:47'], ['24 out.', '24 out., 21:03']],
    blocks: [
      ['t', 'FADE IN:'],
      ['h', 'EXT. CINE ODEON - NOITE'],
      ['a', 'Chuva fina sobre a fachada de um cinema de rua decadente. Metade das letras do letreiro está apagada: "C NE OD ON". Um cartaz anuncia "ÚLTIMA SESSÃO — HOJE".'],
      ['a', 'HELENA (60), capa de chuva amarela, para diante da bilheteria fechada. Bate no vidro com os nós dos dedos.'],
      ['h', 'INT. CINE ODEON - SAGUÃO - NOITE'],
      ['a', 'Carpete vermelho gasto, pôsteres desbotados. TOMÁS (25), lanterninha de uniforme largo demais, varre pipoca velha. Ele se assusta com as batidas.'],
      ['c', 'TOMÁS'], ['p', '(sem abrir a porta)'], ['d', 'Fechado, senhora. A sessão já começou.'],
      ['c', 'HELENA'], ['d', 'Eu sei. Eu sempre chego atrasada. Quarenta anos chegando atrasada nesse lugar.'],
      ['a', 'Tomás hesita. Olha para a sala de projeção, depois para a chuva.'],
      ['c', 'TOMÁS'], ['d', 'O gerente me mata.'],
    ],
  },
  en: {
    file: 'the_last_show.fountain',
    page: 'p. 1',
    stamps: [['Now', 'now'], ['Nov 12', 'Nov 12, 4:40 PM'], ['Nov 11', 'Nov 11, 10:08 PM'], ['Nov 9', 'Nov 9, 11:31 AM'],
             ['Nov 6', 'Nov 6, 6:55 PM'], ['Nov 3', 'Nov 3, 10:20 AM'], ['Oct 29', 'Oct 29, 2:47 PM'], ['Oct 24', 'Oct 24, 9:03 PM']],
    blocks: [
      ['t', 'FADE IN:'],
      ['h', 'EXT. ODEON CINEMA - NIGHT'],
      ['a', 'Light rain over the facade of a run-down neighborhood cinema. Half the letters on the marquee are dark: "OD ON". A poster announces "LAST SHOW — TONIGHT".'],
      ['a', 'HELENA (60), yellow raincoat, stops in front of the closed box office. She knocks on the glass with her knuckles.'],
      ['h', 'INT. ODEON CINEMA - LOBBY - NIGHT'],
      ['a', 'Worn red carpet, faded posters. TOMAS (25), an usher in a uniform two sizes too big, sweeps up old popcorn. The knocking startles him.'],
      ['c', 'TOMAS'], ['p', '(without opening the door)'], ['d', "We're closed, ma'am. The show already started."],
      ['c', 'HELENA'], ['d', "I know. I'm always late. Forty years of being late to this place."],
      ['a', 'Tomas hesitates. He glances toward the auditorium, then at the rain.'],
      ['c', 'TOMAS'], ['d', 'The manager will kill me.'],
    ],
  },
};

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// Uma cópia: a barra com página, arquivo e data, e a folha com o começo do roteiro. As cópias mais
// antigas têm menos texto, como rascunhos de antes.
function page(s, i, n) {
  const p = el('article', 'vstack__page');
  const bar = el('div', 'vstack__bar');
  bar.append(el('span', 'vstack__pg', s.page), el('b', null, s.file), el('span', 'vstack__when', s.stamps[i][1]));
  const sheet = el('div', 'vstack__sheet');
  const keep = Math.max(4, s.blocks.length - Math.round(i * (s.blocks.length - 4) / (n - 1)));
  for (const [kind, text] of s.blocks.slice(0, keep)) sheet.append(el('p', `vs-${kind}`, text));
  p.append(bar, sheet);
  return p;
}

export function versionsStack(root, { pt, reduced }) {
  const s = SCRIPT[pt ? 'pt' : 'en'];
  const n = s.stamps.length;
  const pagesBox = root.querySelector('.vstack__pages');
  const dates = root.querySelector('.vstack__dates');
  const pages = s.stamps.map((_, i) => page(s, i, n));
  pagesBox.append(...pages.slice().reverse());  // a mais nova por último, por cima das outras
  // Na linha do tempo, como no app: a mais antiga em cima e "Agora" embaixo.
  const marks = s.stamps.map(([label]) => el('li', null, label));
  dates.append(...marks.slice().reverse());

  let current = -1;
  function place(c) {
    pages.forEach((p, i) => {
      const d = i - c;  // 0 = na frente; positivo = mais atrás na pilha; negativo = já recuou
      let y, z, rx = 0, o;
      if (d >= 0) {
        y = -d * 30; z = -d * 80; o = Math.max(0, 1 - d * 0.1);
      } else {
        // A cópia da frente recua: sobe e tomba para trás por cima da pilha, sumindo aos poucos.
        // Fica um pouco à frente das outras no eixo z para o movimento aparecer inteiro.
        const e = Math.min(1, -d);
        y = -e * 240; z = 40 * e; rx = e * 62; o = Math.max(0, 1 - e * 1.4);
      }
      p.style.transform = `translate3d(-50%, ${y}px, ${z}px) rotateX(${rx}deg)`;
      p.style.opacity = o.toFixed(3);
      p.style.zIndex = String(n - i);
      p.style.visibility = o < 0.01 ? 'hidden' : 'visible';
    });
    const near = Math.min(n - 1, Math.floor(c + 0.35));  // a data troca quando a próxima cópia já está quase na frente
    if (near !== current) {
      current = near;
      marks.forEach((m, i) => m.classList.toggle('is-on', i === near));
    }
  }

  if (reduced) { root.classList.add('vstack--still'); place(0); return; }

  // O trecho de rolagem: o palco fica preso no meio da tela enquanto a caixa alta passa por ele.
  let ticking = false;
  function update() {
    ticking = false;
    const r = root.getBoundingClientRect();
    const stage = root.firstElementChild.getBoundingClientRect();
    const travel = r.height - stage.height;
    const top = parseFloat(getComputedStyle(root.firstElementChild).top) || 0;
    const t = travel > 0 ? Math.min(1, Math.max(0, (top - r.top) / travel)) : 0;
    place(t * (n - 1));
  }
  const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
  addEventListener('scroll', onScroll, { passive: true });
  addEventListener('resize', onScroll);
  update();
}
