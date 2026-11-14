#!/usr/bin/env python3
"""Grava um vídeo curto do Owlio em uso, para divulgação.

Abre o app numa tela virtual de 1920x1080 (Xephyr) com o mesmo roteiro de exemplo das capturas
do site, grava a tela com o ffmpeg enquanto um roteiro move o mouse, digita uma cena nova e passa
pelas telas principais, e depois junta abertura, legendas e encerramento num .mp4 (H.264).

Requisitos: os mesmos do capture.py, mais o ffmpeg com libx264.

uso: python3 tools/capture/video.py [--app ../claquete] [--lang pt|en] [--theme dark|light] [--out owlio.mp4]
"""
import argparse, math, random, shutil, subprocess, sys, time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from Xlib import X
from Xlib.ext import xtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import capture as cap  # noqa: E402

W, H, FPS = 1920, 1080, 30
FONT_BOLD = '/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf'
FONT_TEXT = '/usr/share/fonts/truetype/ubuntu/Ubuntu-L.ttf'

# Botões da barra de ferramentas na janela de 1920x1080.
BTN = {'script': (391, 72), 'cards': (440, 72), 'beats': (489, 72), 'relations': (538, 72),
       'timeline': (587, 72), 'versions': (218, 72), 'theme': (1861, 21)}
SCENE3 = (150, 268)  # a terceira cena no painel lateral

TEXT = {
    'pt': {
        'intro': ('Owlio', 'Editor de roteiros gratuito e de código aberto'),
        'outro': ('Owlio', 'Baixe grátis para Windows', 'berdfandrade.github.io/owlio-website'),
        'pages': 'Páginas de verdade, no padrão da indústria',
        'write': 'Enter e Tab escolhem o próximo elemento',
        'complete': 'Autocompletar para personagens e locais',
        'cards': 'Cada cena vira um cartão',
        'timeline': 'Linha do tempo com a estrutura da história',
        'relations': 'Mapa de relações entre os personagens',
        'beats': 'Beat Board para organizar as ideias',
        'versions': 'Versões: uma máquina do tempo do roteiro',
        'theme': 'Tema claro e escuro',
        'scene': [('heading', 'INT. CINE ODEON - CORREDOR - NOITE'),
                  ('action', 'Tomás acende a lanterna e guia Helena pelo corredor escuro. Ela passa a mão nos cartazes antigos.'),
                  ('cue', 'HE'), ('dialogue', 'Ainda tem cheiro de pipoca.'),
                  ('cue', 'TO'), ('dialogue', 'Tem cheiro de mofo, senhora.')],
    },
    'en': {
        'intro': ('Owlio', 'A free, open source screenwriting app'),
        'outro': ('Owlio', 'Free download for Windows', 'berdfandrade.github.io/owlio-website'),
        'pages': 'Real pages, industry-standard format',
        'write': 'Enter and Tab pick the next element',
        'complete': 'Autocomplete for characters and places',
        'cards': 'Every scene becomes an index card',
        'timeline': 'A timeline with your story structure',
        'relations': 'A map of how characters relate',
        'beats': 'A Beat Board for your ideas',
        'versions': 'Versions: a time machine for your script',
        'theme': 'Light and dark themes',
        'scene': [('heading', 'INT. ODEON CINEMA - HALLWAY - NIGHT'),
                  ('action', 'Tomas switches on his flashlight and leads Helena down the dark hallway. She runs her hand over the old posters.'),
                  ('cue', 'HE'), ('dialogue', 'It still smells like popcorn.'),
                  ('cue', 'TO'), ('dialogue', 'It smells like mold, ma\'am.')],
    },
}


# ----------------------------------------------------------------------------- controle mais humano
class Driver(cap.Owlio):
    """O controle do capture.py com mouse que desliza e digitação no ritmo de uma pessoa."""

    def __init__(self, *a):
        super().__init__(*a)
        self.pos = (W // 2, H // 2)
        self.spare = 250  # teclas livres, usadas para letras acentuadas que o teclado virtual não tem

    def move(self, x, y, dur=0.7):
        x0, y0 = self.pos
        steps = max(2, int(dur * 60))
        for i in range(1, steps + 1):
            t = i / steps
            e = t * t * (3 - 2 * t)  # suave no começo e no fim
            xtest.fake_input(self.d, X.MotionNotify, x=round(x0 + (x - x0) * e), y=round(y0 + (y - y0) * e))
            self.d.sync()
            time.sleep(dur / steps)
        self.pos = (x, y)

    def press(self, button=1):
        xtest.fake_input(self.d, X.ButtonPress, button)
        xtest.fake_input(self.d, X.ButtonRelease, button)
        self.d.sync()

    def go(self, name, wait=1.4):
        x, y = BTN[name]
        self.move(x, y)
        time.sleep(0.25)
        self.press()
        time.sleep(wait)

    def scroll(self, ticks, down=True, gap=0.09):
        for _ in range(ticks):
            self.press(5 if down else 4)
            time.sleep(gap)

    def _keycode(self, ch):
        ks = ord(ch) if ord(ch) < 0x100 else cap.XK.string_to_keysym(ch)
        found = list(self.d.keysym_to_keycodes(ks))
        if found:
            code, index = found[0]
            return code, index % 2 == 1
        code, self.spare = self.spare, self.spare - 1
        self.d.change_keyboard_mapping(code, [(ks, ks)])
        self.d.sync()
        time.sleep(0.05)
        return code, False

    def write(self, text, speed=0.055):
        self.d.create_resource_object('window', self.top()).set_input_focus(X.RevertToParent, X.CurrentTime)
        shift = self._code('shift')
        for ch in text:
            code, shifted = self._keycode(ch)
            if shifted:
                xtest.fake_input(self.d, X.KeyPress, shift)
            xtest.fake_input(self.d, X.KeyPress, code)
            xtest.fake_input(self.d, X.KeyRelease, code)
            if shifted:
                xtest.fake_input(self.d, X.KeyRelease, shift)
            self.d.sync()
            time.sleep(speed * random.uniform(0.6, 1.5) + (0.12 if ch in ' .,' and random.random() < 0.3 else 0))


# ----------------------------------------------------------------------------- o roteiro do vídeo
def perform(o, t, mark):
    random.seed(7)
    time.sleep(1.0)
    mark('pages')
    o.move(1100, 600, 1.2)
    o.scroll(12, gap=0.12)
    time.sleep(0.8)
    o.scroll(12, down=False, gap=0.06)
    time.sleep(0.6)
    mark('pages', end=True)

    # Uma cena nova no fim do roteiro, digitada com o fluxo de elementos e o autocompletar.
    # Uma cena nova antes da cena 3, onde há roteiro embaixo para a tela rolar: ao clicar na cena no
    # painel, o cabeçalho fica perto do topo e a escrita acontece no meio da tela, longe da legenda.
    o.key('ctrl+equal', 0.4)
    o.key('ctrl+equal', 0.6)
    o.move(*SCENE3, 0.8)
    time.sleep(0.2)
    o.press()
    time.sleep(0.9)
    o.key('Return', 0.3)   # abre uma linha antes do cabeçalho da cena 3
    o.key('Up', 0.3)
    o.key('ctrl+1', 0.4)
    o.move(1500, 700, 0.6)
    mark('write')
    for kind, text in t['scene']:
        if kind == 'heading':
            o.write(text)
            o.key('Return', 0.6)
        elif kind == 'action':
            o.write(text, 0.035)
            o.key('Return', 0.6)
            mark('write', end=True)
        elif kind == 'cue':
            if not getattr(o, 'completing', False):
                mark('complete')
                o.completing = True
            o.write(text, 0.12)
            time.sleep(0.9)
            o.key('Tab', 0.5)
            o.key('Return', 0.4)
        else:
            o.write(text, 0.045)
            time.sleep(0.4)
            o.key('Return', 0.6)
    o.key('Escape', 0.3)
    o.key('BackSpace', 0.3)  # tira a linha de personagem vazia que sobrou depois da última fala
    time.sleep(1.4)
    mark('complete', end=True)
    o.key('ctrl+minus', 0.3)
    o.key('ctrl+minus', 0.6)

    for view, label, linger in (('cards', 'cards', 3.2), ('timeline', 'timeline', 3.4),
                                ('relations', 'relations', 3.2), ('beats', 'beats', 3.2)):
        mark(label)
        o.go(view, 0.4)
        o.move(1150, 560, 1.0)
        time.sleep(linger - 1.0)
        mark(label, end=True)

    o.go('script', 1.0)
    mark('versions')
    o.go('versions', 2.4)
    o.move(1180, 640, 0.6)
    for _ in range(3):
        o.key('Up', 1.1)
    time.sleep(1.0)
    o.key('Escape', 1.0)
    mark('versions', end=True)

    mark('theme')
    o.go('theme', 1.6)
    o.move(1100, 560, 0.8)
    time.sleep(0.8)
    o.go('theme', 1.4)
    mark('theme', end=True)
    time.sleep(0.6)


# ----------------------------------------------------------------------------- arte: legendas e cartelas
def font(path, size):
    return ImageFont.truetype(path, size)


def caption_png(text, path):
    """Uma pílula escura com o texto, centralizada embaixo, com sombra suave."""
    f = font(FONT_BOLD, 46)
    tw = f.getbbox(text)[2]
    pw, ph = tw + 96, 96
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    x0, y0 = (W - pw) // 2, H - ph - 70
    ImageDraw.Draw(shadow).rounded_rectangle((x0, y0 + 8, x0 + pw, y0 + ph + 8), 48, fill=(0, 0, 0, 120))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(16)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), 48, fill=(17, 19, 26, 236), outline=(91, 110, 245, 255), width=3)
    d.text((W // 2, y0 + ph // 2), text, font=f, fill=(244, 245, 250), anchor='mm')
    im.save(path)


def card_png(lines, path, logo):
    """Cartela de abertura ou encerramento: fundo noturno, logo e textos."""
    im = Image.new('RGB', (W, H), (12, 14, 24))
    glow = Image.new('RGB', (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).ellipse((W // 2 - 520, 120, W // 2 + 520, 860), fill=(52, 64, 150))
    im = Image.blend(im, glow.filter(ImageFilter.GaussianBlur(180)), 0.55)
    rnd = random.Random(3)
    d = ImageDraw.Draw(im)
    for _ in range(260):  # estrelas, como na tela de Versões
        x, y, r = rnd.randrange(W), rnd.randrange(H), rnd.choice((1, 1, 1, 2))
        c = rnd.randrange(120, 230)
        d.ellipse((x, y, x + r, y + r), fill=(c, c, min(255, c + 25)))
    owl = Image.open(logo).convert('RGBA').resize((230, 230), Image.LANCZOS)
    im.paste(owl, ((W - 230) // 2, 250), owl)
    d.text((W // 2, 560), lines[0], font=font(FONT_BOLD, 112), fill=(246, 247, 252), anchor='mm')
    d.text((W // 2, 668), lines[1], font=font(FONT_TEXT, 50), fill=(196, 202, 228), anchor='mm')
    if len(lines) > 2:
        d.text((W // 2, 760), lines[2], font=font(FONT_BOLD, 40), fill=(120, 140, 255), anchor='mm')
    im.save(path)


def compose(raw, marks, t, work, out, logo):
    card_png(t['intro'], work / 'intro.png', logo)
    card_png(t['outro'], work / 'outro.png', logo)
    caps = []
    for key, (a, b) in marks.items():
        p = work / f'cap-{key}.png'
        caption_png(t[key], p)
        caps.append((p, a, b))
    duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                              '-of', 'csv=p=0', str(raw)]).decode())
    intro, outro, fade = 3.0, 4.0, 0.6
    inputs = ['-loop', '1', '-t', str(intro), '-i', str(work / 'intro.png'), '-i', str(raw),
              '-loop', '1', '-t', str(outro), '-i', str(work / 'outro.png')]
    for p, _, _ in caps:
        inputs += ['-loop', '1', '-t', str(duration), '-i', str(p)]
    chain = [f'[1:v]fps={FPS},scale={W}:{H},format=yuv420p,setsar=1[v0]']
    last = 'v0'
    for i, (_, a, b) in enumerate(caps):
        k = 3 + i
        a, b = max(0.0, a), min(duration, b)
        chain.append(f'[{k}:v]format=rgba,fade=in:st={a:.2f}:d=0.35:alpha=1,fade=out:st={max(a, b - 0.35):.2f}:d=0.35:alpha=1[c{i}]')
        chain.append(f"[{last}][c{i}]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[v{i + 1}]")
        last = f'v{i + 1}'
    chain.append(f'[0:v]fps={FPS},format=yuv420p,setsar=1[in]')
    chain.append(f'[2:v]fps={FPS},format=yuv420p,setsar=1[out]')
    chain.append(f'[in][{last}]xfade=transition=fade:duration={fade}:offset={intro - fade}[x1]')
    chain.append(f'[x1][out]xfade=transition=fade:duration={fade}:offset={intro + duration - 2 * fade}[final]')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', ';'.join(chain), '-map', '[final]',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20', '-pix_fmt', 'yuv420p',
                    '-movflags', '+faststart', str(out)], check=True)


# ----------------------------------------------------------------------------- execução
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    near = next((p for p in (cap.SITE.parent / 'owlio', cap.SITE.parent / 'claquete') if (p / 'build/owlio').exists()),
                cap.SITE.parent / 'owlio')
    ap.add_argument('--app', default=str(near))
    ap.add_argument('--lang', default='pt', choices=['pt', 'en'])
    ap.add_argument('--theme', default='dark', choices=list(cap.THEMES))
    ap.add_argument('--out', default=str(cap.WORK / 'video' / 'owlio.mp4'))
    a = ap.parse_args()
    app = Path(a.app).resolve()
    exe = app / 'build/owlio'
    if not exe.exists():
        sys.exit(f'não achei {exe}: compile o Owlio antes (cmake --build build)')
    out = Path(a.out).resolve()
    work = cap.WORK / 'video' / f'{a.lang}-{a.theme}'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    raw = work / 'raw.mp4'
    cap.W, cap.H = W, H

    xephyr = subprocess.Popen(['Xephyr', cap.SCREEN, '-screen', f'{W}x{H}', '-title', 'Owlio (vídeo)', '-no-host-grab'],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    rec = o = None
    marks, opened = {}, {}
    try:
        base, script = cap.prepare(app, a.lang, a.theme)
        o = Driver(exe, base, script)
        o.move(W // 2, H // 2, 0.1)
        rec = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'x11grab', '-draw_mouse', '1', '-framerate', str(FPS),
                                '-video_size', f'{W}x{H}', '-i', cap.SCREEN, '-c:v', 'libx264', '-preset', 'ultrafast',
                                '-crf', '12', '-pix_fmt', 'yuv420p', str(raw)], stdin=subprocess.PIPE)
        t0 = time.monotonic()

        def mark(key, end=False):
            now = time.monotonic() - t0
            if end:
                marks[key] = (opened.pop(key), now)
            else:
                opened[key] = now

        time.sleep(0.5)
        perform(o, TEXT[a.lang], mark)
    finally:
        if rec:
            rec.communicate(b'q', timeout=30)
        if o:
            o.quit()
        xephyr.terminate()
    # A gravação começa uns instantes depois do t0; o atraso é pequeno perto da duração das legendas.
    compose(raw, marks, TEXT[a.lang], work, out, app / 'resources/owlio.png')
    print(f'vídeo em {out}')


if __name__ == '__main__':
    main()
