"""
**파티모아 · 썸소울 한 줄.** 릴스 하나 + 피드 둘. 새 호스트가 올라왔다는 판.

    python reel_somesoul.py   →  out/partymoa/S_썸소울.mp4  (릴스 12초)
                                 out/partymoa/SC.jpg          (릴스 커버 1080×1920)
                                 out/partymoa/S1.jpg S2.jpg   (피드 1080×1350)
                                 out/partymoa/_썸소울격자.jpg

## 한 줄이 한 판

격자에서 [릴스 커버 | S1 | S2] 로 놓인다. 올리는 순서는 S2 → S1 → 릴스.
셋을 잇는 건 썸소울 로고의 연보라 빛 덩어리 하나 — 세 칸에 걸쳐 흐른다 —
와 노란 선. 앞 줄(RDA·REA·RFA)과 같은 규칙.

    커버   새 파티 · 썸소울           사진 카드
    S1     매주 토요일 18:30 · 신림    시간 · 조건
    S2     값                         프리미엄 · 본파티 · 애프터, 남녀 따로

## 사실만

썸소울이 준 것만 적는다. 매주 토 18:30, 신림역 도보 2분, 본파티 18:30–21:30,
애프터 21:30–00:30, 남녀 30:30, 안주·주류 무제한, 술 못 먹어도 참여 가능,
값 여섯 개. "게하파티" 는 그쪽 이름이다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from feed_partymoa import ACC, ACCENT, BRAND, DEEP, DOTS, M, WHITE, font
from feed_partymoa9 import cta_plate, head
from fonts import KR, KRB
from render import out_cubic, out_expo
from reel_partymoa import (DUR, FPS, H, INK, INK_D, NF, OUT, SAFE_BOT, SAFE_TOP,
                           SUB, U, W, encode, end_card, fade, finish, fit_text,
                           logo_rgba, plate, pop, purple_bg, put, symbol_bg, text)

PM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'partymoa', 'public')
PHOTO = os.path.join(PM, 'covers', 'somesoul-love-in-seoul.jpg')
LOGO = os.path.join(PM, 'crews', 'somesoul.png')
URL = 'partymoa.com/party/somesoul-20260912'
BPM = 132.0
BGM = 'bgm_garage.wav'
LAV = np.float32([0.78, 0.66, 0.96])         # 썸소울 로고의 연보라
PURPLE = np.float32(BRAND) / 255
DEEPC = np.float32(DEEP) / 255

FW, FH = 1080, 1350
BAND_Y = (H - FH) // 2

PRICES = [('프리미엄', '본파티 + 애프터', 50000, 63000),
          ('본파티', '18:30 – 21:30', 37000, 47000),
          ('애프터', '21:30 – 00:30', 25000, 25000)]


def won(n):
    return f'{n:,}원'


def card(w, h, r=40):
    """사진을 둥근 카드로. 로고를 오른쪽 아래에."""
    im = Image.open(PHOTO).convert('RGB')
    im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    top = max(0, (im.height - h) // 2 - int(h * 0.08))
    im = im.crop((0, top, w, top + h))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    out.paste(im, (0, 0), mask)
    lg = Image.open(LOGO).convert('RGBA')
    ls = int(h * 0.22)
    lg = lg.resize((ls, ls), Image.LANCZOS)
    lm = Image.new('L', (ls, ls), 0)
    ImageDraw.Draw(lm).ellipse([0, 0, ls - 1, ls - 1], fill=255)
    out.paste(lg, (w - ls - 24, h - ls - 24), lm)
    return np.asarray(out, np.float32) / 255.0


def lavender(img, cx, cy, r, a=0.55):
    """연보라 빛 덩어리. 로고 색을 판에 번지게."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.exp(-(((xx - cx) / r) ** 2 + ((yy - cy) / (r * 0.8)) ** 2))
    img[...] = img * (1 - g[..., None] * a) + LAV * g[..., None] * a


# ══════════════════════════════════════════════════════════
#  피드 두 장 + 커버 — 한 장의 판을 셋으로 자른다
# ══════════════════════════════════════════════════════════

def row_sheet():
    RW = W * 3
    yy = np.linspace(0, 1, FH, dtype=np.float32)[:, None, None]
    a = PURPLE * (1 - yy ** 1.4) + DEEPC * (yy ** 1.4)
    a = np.repeat(a, RW, axis=1)
    # 연보라 덩어리 하나가 세 칸을 지난다. 가운데 칸 위쪽에서 시작해 오른쪽으로
    lavender(a, RW * 0.55, FH * 0.30, RW * 0.30, 0.5)
    lavender(a, RW * 0.18, FH * 0.75, RW * 0.16, 0.25)
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    d.line([(M, int(FH * 0.86)), (RW - M, int(FH * 0.86))], fill=WHITE + (110,), width=2)
    ly = int(FH * 0.60)
    d.line([(0, ly), (RW, ly)], fill=ACCENT + (255,), width=6)
    return pil, ly


def logo_line(d, x, y):
    f = font(KRB, 34)
    S = 0.42
    for px, py in DOTS:
        cx, cy = x + px * S, y + py * S
        d.ellipse([cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2], fill=WHITE)
    cx, cy = x + ACC[0] * S, y + ACC[1] * S
    d.ellipse([cx - 2.6, cy - 2.6, cx + 2.6, cy + 2.6], fill=ACCENT)
    d.text((x + 48, y + 4), '파티모아', font=f, fill=WHITE)


def footer(d, x0):
    fb = font(KR, 22)
    y = int(FH * 0.86) + 22
    d.text((x0 + M, y), 'partymoa.com', font=fb, fill=WHITE + (200,))
    r = 'App Store'
    d.text((x0 + W - M - d.textlength(r, font=fb), y), r, font=fb, fill=WHITE + (200,))


def feeds():
    sheet, ly = row_sheet()
    tiles = {}

    # ── 커버 (칸 0). 사진 카드 + 새 파티
    b = sheet.crop((0, 0, W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    f = font(KR, 34)
    d.text((M, 200), '새 호스트', font=f, fill=ACCENT)
    fh = font(KRB, 150)
    d.text((M, 236), '썸소울', font=fh, fill=WHITE)
    ph = 300
    c = card(W - M * 2, ph, 36)
    cp = Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8), 'RGBA')
    b.alpha_composite(cp, (M, ly - ph - 50))
    d.polygon([(M, ly + 40), (M, ly + 92), (M + 44, ly + 66)], fill=ACCENT)
    d.text((M + 64, ly + 44), '릴스 · 12초', font=font(KR, 34), fill=WHITE + (220,))
    fc = font(KRB, 34)
    cta = '예매 → 프로필 링크'
    pw, ph2 = int(fc.getlength(cta) + 72), 92
    cy0 = int(FH * 0.86) - 92 - 48
    d.rounded_rectangle([M, cy0, M + pw, cy0 + ph2], 22, fill=ACCENT)
    d.text((M + 36, cy0 + (ph2 - 34) / 2 - 4), cta, font=fc, fill=(20, 12, 60))
    footer(d, 0)
    full = Image.new('RGB', (W, H), DEEP)
    full.paste(b.convert('RGB'), (0, BAND_Y))
    full.save(os.path.join(OUT, 'SC.jpg'), quality=94)
    tiles['SC'] = b.convert('RGB')

    # ── S1 (칸 1). 언제 · 어디 · 조건
    b = sheet.crop((W, 0, 2 * W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, ['매주 토요일', '18:30'], '신림역 도보 2분 · 본파티 3시간 · 애프터 00:30까지', 150, 250)
    # 글은 노란 선(60%) 위에서 끝난다. 선을 타고 넘으면 겹쳐 보인다
    fs = font(KRB, 38)
    for k, line in enumerate(('안주 · 주류 무제한', '술 못 먹어도 참여 가능', '남녀 30 : 30')):
        yy = y + 36 + k * 58
        d.ellipse([M, yy + 12, M + 16, yy + 28], fill=ACCENT)
        d.text((M + 34, yy), line, font=fs, fill=WHITE)
    cta_plate(d, '예매 → 프로필 링크', int(FH * 0.86) - 92 - 48)
    footer(d, 0)
    b.convert('RGB').save(os.path.join(OUT, 'S1.jpg'), quality=94)
    tiles['S1'] = b.convert('RGB')

    # ── S2 (칸 2). 값
    b = sheet.crop((2 * W, 0, 3 * W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    # 표 전체가 노란 선 위에 들어가야 한다. 제목 한 줄, 줄 간격 84
    y = head(d, ['입장권 세 가지'], '여 · 남 따로. 예매할 때 고르면 돼요', 120, 250)
    y += 36
    fl = font(KRB, 36)
    fn = font(KR, 26)
    fp = font(KRB, 32)
    for name, note, pf, pm in PRICES:
        d.line([(M, y), (W - M, y)], fill=WHITE + (70,), width=1)
        y += 14
        d.text((M, y), name, font=fl, fill=WHITE)
        d.text((M, y + 44), note, font=fn, fill=WHITE + (180,))
        s1 = f'여 {won(pf)}'
        s2 = f'남 {won(pm)}'
        d.text((W - M - d.textlength(s1, font=fp), y), s1, font=fp, fill=ACCENT)
        d.text((W - M - d.textlength(s2, font=fp), y + 40), s2, font=fp, fill=WHITE)
        y += 84
    d.line([(M, y), (W - M, y)], fill=WHITE + (70,), width=1)
    assert y < ly - 8, f'값 표가 노란 선을 넘는다: {y} >= {ly}'
    cta_plate(d, '예매 → 프로필 링크', int(FH * 0.86) - 92 - 48)
    footer(d, 0)
    b.convert('RGB').save(os.path.join(OUT, 'S2.jpg'), quality=94)
    tiles['S2'] = b.convert('RGB')

    g = Image.new('RGB', (W * 3 + 16, FH * 2 + 8), (255, 255, 255))
    for i, k in enumerate(('SC', 'S1', 'S2')):
        g.paste(tiles[k], (i * (W + 8), 0))
    for i, k in enumerate(('RDA', 'REA', 'RFA')):
        p = os.path.join(OUT, f'{k}.jpg')
        if os.path.exists(p):
            im = Image.open(p).crop((0, BAND_Y, W, BAND_Y + FH))
            g.paste(im, (i * (W + 8), FH + 8))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_썸소울격자.jpg'), quality=92)
    print('피드 완료: SC S1 S2')


# ══════════════════════════════════════════════════════════
#  릴스 — 새 호스트, 12초
# ══════════════════════════════════════════════════════════

def reel():
    beat = 60 / BPM
    B = lambda n: n * beat
    bg = purple_bg()
    lavender(bg, W * 0.7, H * 0.32, W * 0.55, 0.45)
    symbol_bg(bg, 0.05, 0.55, 1.0)
    lg = logo_rgba(36)
    h1 = fit_text('파티모아에', KRB, W - M * 2, 130)
    h2 = fit_text('새 파티', KRB, W - M * 2, 170, ACCENT + (255,))
    name = fit_text('썸소울', KRB, W - M * 2, 190)
    sub = text('매주 토요일 18:30 · 신림역 도보 2분', KR, 40, SUB)
    cw = W - M * 2
    ch = int(cw * 0.62)
    c = card(cw, ch, 40)
    facts = ['본파티 18:30 – 21:30', '애프터 21:30 – 00:30', '안주 · 주류 무제한',
             '술 못 먹어도 참여 가능', '남녀 30 : 30']
    pr = [text(f'{n}  여 {won(pf)} · 남 {won(pm)}', KRB, 38) for n, _, pf, pm in PRICES]
    t_name = B(2.5)
    t_card = B(5)
    t_facts = B(9)
    t_price = B(16)
    t_end = B(20)

    def frames():
        for i in range(NF):
            t = i / FPS
            img = bg.copy()
            put(img, lg, M, SAFE_TOP + U * 4)
            if t < t_name:
                pop(img, h1, W / 2, H * 0.40, t, 0.0, 0.35)
                pop(img, h2, W / 2, H * 0.40 + 190, t, B(0.75), 0.35)
            elif t < t_card:
                pop(img, name, W / 2, H * 0.40, t, t_name, 0.35)
                put(img, sub, (W - sub.shape[1]) / 2, H * 0.40 + 150, fade(t, t_name + 0.2))
            elif t < t_end:
                k = fade(t, t_card, 0.5)
                cy = SAFE_TOP + U * 12 + (1 - out_expo(k)) * 200
                put(img, c, M, cy, k)
                nm = text('썸소울 · 서울게하파티', KRB, 44)
                put(img, nm, M, cy + ch + U * 3, fade(t, t_card + 0.2))
                y = cy + ch + U * 3 + 80
                if t < t_price:
                    for j, ln in enumerate(facts):
                        kk = fade(t, t_facts + j * B(0.9), 0.25) if t >= t_facts else 0
                        if kk <= 0:
                            continue
                        m = text(ln, KRB, 46)
                        put(img, m, M + 34, y + j * 70, kk)
                        cv2.circle(img, (M + 12, int(y + j * 70 + 30)), 8, (1.0, 0.89, 0.30), -1, cv2.LINE_AA)
                else:
                    for j, m in enumerate(pr):
                        kk = fade(t, t_price + j * B(0.6), 0.25)
                        put(img, m, M, y + j * 66, kk)
            end_card(img, t, t_end)
            yield finish(img)

    encode('S_썸소울', frames(), BGM)


if __name__ == '__main__':
    feeds()
    reel()
