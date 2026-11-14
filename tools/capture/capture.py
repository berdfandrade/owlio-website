#!/usr/bin/env python3
"""Tira as capturas do site direto do Owlio, em português e inglês, nos temas claro e escuro.

Abre o app de verdade numa tela virtual (Xephyr), com os roteiros de exemplo do repositório
do Owlio enriquecidos com fichas, avatares, relações, Beat Board e versões anteriores, e salva
cada tela em public/shots/<idioma>/<tema>/<nome>.webp. As configurações e os dados do app ficam
em .capture/, separados das suas.

Requisitos: Linux com X11, Xephyr, python3-xlib e Pillow, e o Owlio compilado.

uso: python3 tools/capture/capture.py [--app ../owlio] [--lang pt en] [--theme light dark]
"""
import argparse, base64, hashlib, io, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

from PIL import Image
from Xlib import X, XK, display
from Xlib.ext import xtest

SITE = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
WORK = SITE / '.capture'
SCREEN = ':5'
W, H = 1440, 900
THEMES = {'light': 1, 'dark': 2}   # ThemeManager::Mode

# Recortes dos detalhes (x0, y0, x1, y1) na janela de 1440x900.
CROPS = {
    'pt': {'elements': (600, 40, 880, 280), 'autocomplete': (560, 620, 1240, 860), 'dual': (560, 495, 1240, 680),
           'spell': (560, 250, 1260, 540)},
    'en': {'elements': (600, 40, 880, 280), 'autocomplete': (560, 640, 1240, 860), 'dual': (560, 250, 1300, 440),
           'spell': (560, 250, 1260, 540)},
}
# Onde clicar: a fala de Tomás que vira diálogo duplo, e o meio da palavra que leva um erro de digitação.
DUAL_AT = {'pt': (830, 607), 'en': (830, 371)}
# Botão Cancelar dentro do criador de avatar (1080x740) e da ficha do personagem (900x680).
CANCEL = {'avatar': (1005, 697), 'character': (716, 642)}
TYPO_AT = {'pt': (819, 298), 'en': (820, 298)}   # "fach|ada" / "fac|ade" na primeira página


# ----------------------------------------------------------------------------- dados de exemplo
def avatar(name):
    return base64.b64encode((HERE / 'avatars' / f'{name}.png').read_bytes()).decode()


def sample_pt(app):
    body = (app / 'examples/a_ultima_sessao.fountain').read_text(encoding='utf-8').rstrip() + '\n'
    cast = [('HELENA', '60', 'Professora aposentada', 'Protagonista', 'Teimosa, pontual em tudo menos no cinema',
             'Volta ao Cine Odeon na noite da última sessão.', 'helena'),
            ('TOMÁS', '25', 'Lanterninha', 'Coadjuvante', 'Tímido, cumpre ordens',
             'Trabalha no cinema há dois anos e não sabe o que vem depois.', 'tomas'),
            ('SEU JAIR', '72', 'Projecionista', 'Coadjuvante', 'Calado, guarda tudo',
             'Projeta filmes no Odeon desde 1979.', 'jair')]
    beats = [('Helena chega atrasada', 'A bilheteria está fechada, mas ela bate no vidro.', '#f2b13b'),
             ('Tomás abre a porta', 'Ele quebra a regra pela primeira vez.', '#5b8def'),
             ('A cabine de Seu Jair', 'O último rolo ainda está na máquina.', '#e0686b'),
             ('A última sessão', 'Três pessoas numa sala de 400 lugares.', '#46b37b'),
             ('Amanhecer', 'O letreiro se apaga de vez.', '#9c7be0')]
    out = [body, '', '/* owlio-characters']
    for n, age, occ, role, traits, syn, key in cast:
        out += [f'name: {n}', f'age: {age}', f'occupation: {occ}', f'role: {role}', f'traits: {traits}',
                f'synopsis: {syn}', f'photo: {avatar(key)}', '']
    out += ['*/', '', '/* owlio-beatboard']
    pos = [(80, 80), (380, 40), (680, 120), (380, 300), (680, 360)]
    for i, (t, x, c) in enumerate(beats, 1):
        out += [f'beat: {i}', f'frame: {pos[i - 1][0]} {pos[i - 1][1]} 240 150', f'color: {c}', f'title: {t}', f'text: {x}', '']
    out += [f'flow: {i} {i + 1}' for i in range(1, 5)] + ['*/', '']
    out += relations('TOMÁS', 'HELENA', 'SEU JAIR', 'aprendiz', 'antigo amor')
    return body, '\n'.join(out)


def sample_en(app):
    """O exemplo em inglês já traz fichas e Beat Board: só ganha avatares e relações."""
    orig = (app / 'examples/the_last_show.fountain').read_text(encoding='utf-8')
    photos = {'HELENA': avatar('helena'), 'TOMAS': avatar('tomas'), 'JAIR': avatar('jair')}
    a = orig.index('/* owlio-characters'); b = orig.index('*/', a)
    cast = re.sub(r'(name: (\S+)\n(?:[a-z]+: .*\n)*)', lambda m: m.group(1) + f'photo: {photos[m.group(2)]}\n', orig[a:b])
    full = orig[:a] + cast + orig[b:].rstrip() + '\n\n' + '\n'.join(relations('TOMAS', 'HELENA', 'JAIR', 'apprentice', 'old flame'))
    return orig, full


def relations(t, h, j, work, love):
    return ['/* owlio-relations', f'node: 420 120 {t}', f'node: 200 420 {h}', f'node: 640 420 {j}',
            '', f'link: {t}', f'with: {j}', 'kind: work', f'label: {work}',
            '', f'link: {h}', f'with: {t}', 'kind: friendship',
            '', f'link: {h}', f'with: {j}', 'kind: love', f'label: {love}', '*/', '']


def prepare(app, lang, theme):
    """Cópia do roteiro, versões anteriores e configurações isoladas para uma rodada."""
    base = WORK / lang
    if base.exists():
        shutil.rmtree(base)
    name = 'a_ultima_sessao.fountain' if lang == 'pt' else 'the_last_show.fountain'
    body, full = (sample_pt if lang == 'pt' else sample_en)(app)
    script = base / name
    script.parent.mkdir(parents=True)
    script.write_text(full, encoding='utf-8')
    # Versões anteriores: rascunhos com menos cenas, em dias passados (Versões lê o nome do arquivo).
    digest = hashlib.sha1(str(script.resolve()).encode()).hexdigest()[:8]
    backups = base / 'data/Owlio/Owlio/backups' / f'{script.stem}-{digest}'
    backups.mkdir(parents=True)
    scenes = [m.start() for m in re.finditer(r'^(INT|EXT)\.', body, re.M)]
    stamps = ['2026-10-21 09-12-40', '2026-10-24 21-03-11', '2026-10-29 14-47-05', '2026-11-03 10-20-33',
              '2026-11-06 18-55-02', '2026-11-09 11-31-48', '2026-11-11 22-08-19', '2026-11-12 16-40-00']
    for i, stamp in enumerate(stamps):
        n = min(len(scenes), 2 + i * len(scenes) // len(stamps))
        cut = scenes[n] if n < len(scenes) else len(body)
        (backups / f'{script.stem} {stamp}.fountain').write_text(body[:cut].rstrip() + '\n', encoding='utf-8')
    conf = base / 'config/Owlio/Owlio.conf'
    conf.parent.mkdir(parents=True)
    conf.write_text(f"[General]\nlanguage={'pt_BR' if lang == 'pt' else 'en'}\nscriptLanguage={lang}\ntheme={THEMES[theme]}\nreopenLast=false\n"
                    "keepBackups=true\nautosaveMinutes=0\ntargetPages=5\nzoom=1\ncardsAsList=false\nspellCheck=true\n")
    return base, script


# ----------------------------------------------------------------------------- controle do app
class Owlio:
    def __init__(self, exe, base, script):
        env = dict(os.environ, DISPLAY=SCREEN, XDG_CONFIG_HOME=str(base / 'config'), XDG_DATA_HOME=str(base / 'data'))
        qt = Path.home() / 'Qt/6.8.3/gcc_64/lib'
        if qt.exists():
            env['LD_LIBRARY_PATH'] = f"{qt}:{Path.home() / 'Qt/extra/usr/lib/x86_64-linux-gnu'}"
        self.proc = subprocess.Popen([str(exe), str(script)], env=env, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL, start_new_session=True)
        self.d = display.Display(SCREEN)
        self.root = self.d.screen().root
        for _ in range(80):
            time.sleep(0.25)
            if self.windows():
                break
        else:
            raise RuntimeError('o Owlio não abriu uma janela')
        self.main = self.windows()[0]
        win = self.d.create_resource_object('window', self.main)
        win.configure(x=0, y=0, width=W, height=H)
        self.d.sync()
        time.sleep(2.5)

    def windows(self, popups=False):
        """As janelas visíveis do app, de baixo para cima. Dicas e menus (janelas temporárias, sem
        gerenciador) só entram com popups=True, para não serem confundidos com diálogos."""
        pid_atom = self.d.intern_atom('_NET_WM_PID')
        out = []
        for win in self.root.query_tree().children:
            p = win.get_full_property(pid_atom, X.AnyPropertyType)
            attrs = win.get_attributes()
            if p and p.value[0] == self.proc.pid and attrs.map_state == X.IsViewable and (popups or not attrs.override_redirect):
                out.append(win.id)
        return out

    def top(self):
        return self.windows()[-1]

    def geom(self, wid):
        win = self.d.create_resource_object('window', wid)
        g = win.get_geometry()
        t = win.translate_coords(self.root, 0, 0)
        return -t.x, -t.y, g.width, g.height

    def _code(self, name):
        alias = {'ctrl': 'Control_L', 'shift': 'Shift_L', 'enter': 'Return', 'esc': 'Escape', ',': 'comma',
                 'space': 'space', 'up': 'Up', 'end': 'End'}
        return self.d.keysym_to_keycode(XK.string_to_keysym(alias.get(name.lower(), name)))

    def key(self, combo, wait=0.35):
        self.d.create_resource_object('window', self.top()).set_input_focus(X.RevertToParent, X.CurrentTime)
        self.d.sync()
        time.sleep(0.1)
        codes = [self._code(p) for p in combo.split('+')]
        for c in codes:
            xtest.fake_input(self.d, X.KeyPress, c)
        for c in reversed(codes):
            xtest.fake_input(self.d, X.KeyRelease, c)
        self.d.sync()
        time.sleep(wait)

    def type(self, text):
        for ch in text:
            self.key('shift+' + ch.lower() if ch.isupper() else ch, 0.12)

    def click(self, x, y, times=1, button=1, inside=None):
        ox, oy, _, _ = self.geom(inside or self.main)
        xtest.fake_input(self.d, X.MotionNotify, x=ox + x, y=oy + y)
        self.d.sync()
        time.sleep(0.15)
        for _ in range(times):
            xtest.fake_input(self.d, X.ButtonPress, button)
            xtest.fake_input(self.d, X.ButtonRelease, button)
            self.d.sync()
            time.sleep(0.08)
        time.sleep(0.6)

    def wait_dialog(self):
        for _ in range(50):
            if len(self.windows()) > 1:
                break
            time.sleep(0.2)
        time.sleep(0.9)

    def wait_windows(self, count):
        """Espera até o app ter só `count` janelas abertas (os diálogos fecham com algum atraso)."""
        for _ in range(40):
            if len(self.windows()) <= count:
                time.sleep(0.3)
                return
            time.sleep(0.2)
        raise RuntimeError(f'o Owlio continuou com {len(self.windows())} janelas abertas (esperava {count})')

    def grab(self, wid=None):
        """A imagem da janela como aparece na tela (com menus e diálogos por cima)."""
        x, y, w, h = self.geom(wid or self.main)
        sw, sh = self.d.screen().width_in_pixels, self.d.screen().height_in_pixels
        if x < 0: w += x; x = 0
        if y < 0: h += y; y = 0
        w, h = min(w, sw - x), min(h, sh - y)
        raw = self.root.get_image(x, y, w, h, X.ZPixmap, 0xffffffff)
        return Image.frombytes('RGB', (w, h), raw.data, 'raw', 'BGRX')

    def grab_popups(self, before):
        """Menus e listas arredondados são janelas com canal alfa. Sem compositor na tela virtual, os
        cantos transparentes saem pretos; aqui cada uma é lida com o alfa e composta sobre `before`,
        a imagem da janela tirada antes de o menu abrir."""
        shot = self.grab()
        mx, my, _, _ = self.geom(self.main)
        for wid in self.windows(popups=True):
            win = self.d.create_resource_object('window', wid)
            g = win.get_geometry()
            if wid == self.main or g.depth != 32:
                continue
            x, y, w, h = self.geom(wid)
            raw = win.get_image(0, 0, w, h, X.ZPixmap, 0xffffffff)
            menu = Image.frombytes('RGBa', (w, h), raw.data, 'raw', 'BGRa').convert('RGBA')
            box = (x - mx, y - my, x - mx + w, y - my + h)
            under = before.crop(box).convert('RGBA')
            under.alpha_composite(menu)
            shot.paste(under.convert('RGB'), box[:2])
        return shot

    def quit(self):
        self.proc.terminate()
        self.proc.wait(10)


def run(exe, app, lang, theme, out):
    base, script = prepare(app, lang, theme)
    o = Owlio(exe, base, script)
    shots = {}
    try:
        shots['script'] = o.grab()
        for name, combo in (('cards', 'ctrl+shift+c'), ('beat-board', 'ctrl+shift+b'),
                            ('relations', 'ctrl+shift+m'), ('timeline', 'ctrl+shift+l')):
            o.key(combo, 1.6)
            shots[name] = o.grab()
        o.key('ctrl+shift+r', 0.8)
        o.key('ctrl+shift+h', 2.6); o.key('Up', 1.0); o.key('Up', 1.3)
        shots['versions'] = o.grab()
        o.key('esc', 1.0)
        o.key('F1'); o.wait_dialog(); shots['shortcuts'] = o.grab(o.top()); o.key('esc', 1.0)
        o.key('ctrl+,'); o.wait_dialog(); o.click(67, 152, inside=o.top()); shots['settings'] = o.grab(o.top()); o.key('esc', 1.0)
        o.key('ctrl+p'); o.wait_dialog(); shots['print'] = o.grab(o.top()); o.key('esc', 1.0)
        o.click(239, 512); o.wait_dialog(); shots['cast'] = o.grab(o.top()); o.key('esc', 1.0)
        o.click(90, 586, times=2); o.wait_dialog(); shots['character'] = o.grab(o.top())
        o.click(241, 208, inside=o.top()); time.sleep(1.5); shots['avatar'] = o.grab(o.top())
        # O criador de avatar não fecha com Esc: Cancelar nele e depois na ficha.
        o.click(*CANCEL['avatar'], inside=o.top()); o.wait_windows(2)
        o.click(*CANCEL['character'], inside=o.top()); o.wait_windows(1)
        before = o.grab()
        o.click(720, 72); time.sleep(0.6); shots['elements'] = o.grab_popups(before); o.key('esc', 0.6)
        o.key('ctrl+shift+f', 1.2); shots['focus'] = o.grab(); o.key('ctrl+shift+f', 1.0)
        # Corretor: um erro de digitação no meio de uma palavra, o cursor sai dela e o botão direito abre as sugestões.
        tx, ty = TYPO_AT[lang]
        o.click(tx, ty); o.type('x'); o.key('end', 0.8)
        before = o.grab()
        o.click(tx - 12, ty, button=3); time.sleep(0.9); shots['spell'] = o.grab_popups(before)
        o.key('esc', 0.5); o.key('ctrl+z', 0.6)
        # Autocompletar: um nome de personagem começado no fim do roteiro.
        o.click(860, 300); o.key('ctrl+end', 0.6); o.key('enter'); o.key('enter'); o.key('ctrl+3')
        o.type('HE'); time.sleep(1.2); shots['autocomplete'] = o.grab()
        o.key('esc')
        for _ in range(6):
            o.key('ctrl+z', 0.25)
        time.sleep(0.6)
        shots['script-end'] = o.grab()
        o.click(*DUAL_AT[lang]); o.key('ctrl+shift+d', 1.0); shots['dual'] = o.grab(); o.key('ctrl+z', 0.6)
    finally:
        o.quit()
        shutil.rmtree(base / 'data/Owlio/Owlio/recovery', ignore_errors=True)
    for name, box in CROPS[lang].items():
        shots[name] = shots[name].crop(box)
    folder = out / lang / theme
    folder.mkdir(parents=True, exist_ok=True)
    for name, im in shots.items():
        im.save(folder / f'{name}.webp', 'WEBP', quality=88, method=6)
    (WORK / 'raw' / lang / theme).mkdir(parents=True, exist_ok=True)
    for name, im in shots.items():
        im.save(WORK / 'raw' / lang / theme / f'{name}.png')
    print(f'{lang}/{theme}: {len(shots)} capturas em {folder.relative_to(SITE)}')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    near = next((p for p in (SITE.parent / 'owlio', SITE.parent / 'claquete') if (p / 'build/owlio').exists()), SITE.parent / 'owlio')
    ap.add_argument('--app', default=str(near), help='pasta do repositório do Owlio, já compilado (padrão: ../owlio)')
    ap.add_argument('--lang', nargs='+', default=['pt', 'en'], choices=['pt', 'en'])
    ap.add_argument('--theme', nargs='+', default=['light', 'dark'], choices=list(THEMES))
    ap.add_argument('--out', default=str(SITE / 'public/shots'))
    a = ap.parse_args()
    app = Path(a.app).resolve()
    exe = app / 'build/owlio'
    if not exe.exists():
        sys.exit(f'não achei {exe}: compile o Owlio antes (cmake --build build)')
    xephyr = subprocess.Popen(['Xephyr', SCREEN, '-screen', f'{W}x{H}', '-title', 'Owlio (capturas do site)', '-no-host-grab'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    try:
        for lang in a.lang:
            for theme in a.theme:
                run(exe, app, lang, theme, Path(a.out))
    finally:
        xephyr.terminate()


if __name__ == '__main__':
    main()
