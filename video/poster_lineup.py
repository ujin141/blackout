"""
**AFTER MOON 라인업.** 스토리 한 장, 피드 세 장.

    python poster_lineup.py
        out/moon/라인업_스토리.jpg
        out/moon/L1.jpg · L2.jpg · L3.jpg · _라인업격자.jpg

## 앞 판을 버린 이유

가로줄 그은 표였다. 시간이 왼쪽 칸에 서고 이름이 오른쪽에 서고 줄마다
선을 그었다. 정보는 다 들어갔는데 **시간이 흐른다는 게 안 보였다** —
다섯 줄이 그냥 목록이라 22:00 과 02:10 사이에 거리가 없었다.

피드는 더 나빴다. 이름을 전부 칸 왼쪽에 붙여 놨더니 아래 시간 막대와
이름이 아무 관계도 없어 보였고 오른쪽 절반이 통째로 비었다.

## 이번 판

    스토리   세로 등뼈. 밤이 위에서 아래로 흐른다. 줄마다 긋던
             가로선을 없애고 선 하나로 다섯 마디를 잇는다
    피드     이름을 자기 시간 구간 위에 올린다. 위아래로 번갈아
             매달아서 막대가 이름을 꿰고 지나가게 만든다

## 이름이 자기 구간 안에 들어가는가

구간 하나가 3064px 중 613px 이다. Michroma 로 LYNN 을 132 크기로 쓰면
472px 이라 들어간다. **전에는 이 계산을 안 해 보고** 겹칠 거라 지레
짐작해서 왼쪽에 쌓았다.

칸 경계를 타는 이름만 자기 구간이 더 많이 걸친 칸 쪽으로 민다. LYNN 과
AROS 둘뿐이고 밀어도 이름 가운데는 자기 구간 안에 남는다.

위아래는 순서대로 번갈아 간다. 이웃한 두 이름이 같은 쪽에 안 서니까
가로로 붙어도 안 겹친다.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fest_kit import night, sky, vignette
from fonts import KR
from poster_kit import bloom, grain
from poster_lounge import bokeh
from poster_moon import (ARC_BOT, CTA, CTA_KO, DATE, LEAD, LOGO, OUT, TITLE,
                         metal, moonface, over, tracked, tracked_w)

BRAND_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'assets', 'Michroma-Regular.ttf')

U = 12
BASE = 26
INK = (244, 245, 248, 255)
DIM = (168, 171, 180, 255)
FAINT = (120, 123, 132, 255)
RULE = (68, 71, 80, 255)
SPINE = (96, 99, 110, 255)

# (이름, 시작, 끝). **숫자는 여기서만 나온다**
LINEUP = [
    ('BHO', '22:00', '22:50'),
    ('LYNN', '22:50', '23:40'),
    ('LII', '23:40', '00:30'),
    ('AROS', '00:30', '01:20'),
    ('TS', '01:20', '02:10'),
]
STRIP = '9,900원 · 1차 30명 · 남녀 15:15 · 웰컴샷 포함'

probe = ImageDraw.Draw(Image.new('L', (8, 8)))


def step(n):
    return int(round(BASE * 1.28 ** n))


def font(p, s):
    return ImageFont.truetype(p, s)


def hh(t, f):
    """**글자 상자 아래끝.** 잉크 높이로 줄을 넘기면 PIL 이 상자 위에서
    그리기 때문에 줄이 서로 올라탄다."""
    return probe.textbbox((0, 0), t, font=f)[3]


def mins(t):
    h, m = (int(x) for x in t.split(':'))
    v = h * 60 + m
    return v - 22 * 60 if v >= 22 * 60 else v + 2 * 60


TOTAL = mins(LINEUP[-1][2])                        # 250 분


def silver(text, f, track=0.06):
    asc, desc = f.getmetrics()
    im = Image.new('L', (int(tracked_w(text, f, track)) + 24, asc + desc), 0)
    tracked(ImageDraw.Draw(im), (12, 0), text, f, track, 255)
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    m = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) / 255.0
    return metal(*m.shape, m)


def put(pil, plate, x, y):
    pil.alpha_composite(
        Image.fromarray((np.clip(plate, 0, 1) * 255).astype(np.uint8), 'RGBA'),
        (int(x), int(y)))


def fit(text, room, cap, track=0.06):
    for sz in range(cap, 30, -2):
        g = font(BRAND_FONT, sz)
        if tracked_w(text, g, track) <= room:
            return g
    return font(BRAND_FONT, 30)


def finish(pil, W, H, tag, vig=0.30):
    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.60, W * 0.018, 0.28)
    vignette(out, vig, 2.0)
    grain(out, 0.009)
    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    im.save(os.path.join(OUT, f'{tag}.jpg'), quality=94)
    night(out, tag)
    return im


def logo_at(pil, W, x, y, frac):
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * frac)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    pil.alpha_composite(lg, (int(x), int(y)))
    return lg.height


# ══════════════════════════════════════════════════════════
#  1. 스토리 — 세로 등뼈
# ══════════════════════════════════════════════════════════
#
# 밤이 위에서 아래로 흐른다. 선 하나가 22:00 에서 02:10 까지 내려가고
# 마디마다 점이 박힌다. **줄 사이 가로선을 안 긋는다** — 그으면 다섯이
# 서로 끊긴 항목이 되고, 이어진 하나의 밤이 아니게 된다.

def story(W=1080, H=1920, top=270, bot=1630):
    M = int(W * 0.082)
    img = sky(W, H, [(0.0, (0.050, 0.050, 0.064)),
                     (0.46, (0.092, 0.092, 0.115)),
                     (1.0, (0.038, 0.038, 0.050))])
    bokeh(img, n=18, seed=3, y0=0.02, y1=0.24)
    bokeh(img, n=10, seed=8, y0=0.72, y1=0.97)

    # 달은 왼쪽 아래에서 반쯤 잠긴다. 등뼈와 이름이 오른쪽에 몰리니
    # 무게를 반대편에 둬야 판이 안 기운다
    MR = int(W * 0.34)
    mf = moonface(MR)
    mf[..., :3] *= 0.34
    over(img, mf, -int(MR * 0.72), H - int(MR * 0.98))

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    # ── 윗단: 로고와 날짜를 한 줄에 마주 세운다 ──
    lh = logo_at(pil, W, M, top, 0.26)
    fdate = font(BRAND_FONT, step(0))
    wd = tracked_w(DATE, fdate, 0.16)
    tracked(d, (W - M - wd, top + lh - hh(DATE, fdate)), DATE, fdate, 0.16, DIM)
    y = top + lh + U * 3
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 4

    # 이름은 판 폭을 다 쓴다. 이 판에서 제일 큰 글자
    mark = silver(TITLE, fit(TITLE, W - M * 2, 200, 0.10), 0.10)
    put(pil, mark, M, y)
    y += mark.shape[0] + U * 3

    flead = font(KR, step(-1))
    d.text((M, y), LEAD, font=flead, fill=FAINT)
    flab = font(BRAND_FONT, step(-2))
    wl = tracked_w('LINE UP', flab, 0.40)
    tracked(d, (W - M - wl, y + hh(LEAD, flead) - hh('LINE UP', flab)),
            'LINE UP', flab, 0.40, DIM)
    y += hh(LEAD, flead) + U * 7

    # ── 아랫단이 먹는 높이를 먼저 뺀다. 남는 게 등뼈 자리다 ──
    fstrip = font(KR, step(-1))
    fcta = font(BRAND_FONT, step(0))
    ffoot = font(KR, step(-2))
    lower = 2 + U * 3 + hh(STRIP, fstrip) + U * 3 + 2 + U * 3 + hh(CTA, fcta)
    y_end = bot - lower - U * 7

    # ── 등뼈 ──
    ftime = font(BRAND_FONT, step(-1))
    timew = int(max(tracked_w(a, ftime, 0.14) for _, a, _ in LINEUP))
    sx = M + timew + U * 4                       # 선이 서는 자리
    nx = sx + U * 5                              # 이름이 서는 자리
    room = W - M - nx
    # 다섯 줄이 같은 크기여야 한다. 줄마다 맞추면 TS 만 커져서
    # 라인업이 아니라 TS 광고가 된다
    fname = fit(max((n for n, _, _ in LINEUP), key=len), room, 128)
    plates = {n: silver(n, fname) for n, _, _ in LINEUP}
    band = (y_end - y) / len(LINEUP)

    d.line([(sx, y), (sx, y_end)], fill=SPINE, width=2)
    for i, (n, a, _) in enumerate(LINEUP):
        cy = y + band * i
        d.ellipse([sx - 7, cy - 7, sx + 7, cy + 7], fill=(206, 209, 219, 255))
        p = plates[n]
        py = cy + (band - p.shape[0]) / 2
        put(pil, p, nx, py)
        tracked(d, (M, cy - hh(a, ftime) / 2), a, ftime, 0.14, FAINT)
    # 끝 시각. 마지막 마디 아래에 한 번만
    d.ellipse([sx - 5, y_end - 5, sx + 5, y_end + 5], fill=SPINE)
    tracked(d, (M, y_end - hh('02:10', ftime) // 2), LINEUP[-1][2],
            ftime, 0.14, (88, 91, 100, 255))

    # ── 아랫단 ──
    y = bot - lower
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    d.text((M, y), STRIP, font=fstrip, fill=DIM)
    y += hh(STRIP, fstrip) + U * 3
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    fgen = font(BRAND_FONT, step(-2))
    d.text((M, y + (hh(CTA, fcta) - hh(ARC_BOT, fgen)) // 2), ARC_BOT,
           font=fgen, fill=FAINT)
    wc = tracked_w(CTA, fcta, 0.20)
    wk = probe.textlength(CTA_KO + ' ', font=ffoot)
    d.text((W - M - wc - wk, y + hh(CTA, fcta) - hh(CTA_KO, ffoot)), CTA_KO,
           font=ffoot, fill=FAINT)
    tracked(d, (W - M - wc, y), CTA, fcta, 0.20, (214, 217, 226, 255))

    finish(pil, W, H, '라인업_스토리', vig=0.34)


# ══════════════════════════════════════════════════════════
#  2. 피드 세 장 — 막대가 이름을 꿰고 지나간다
# ══════════════════════════════════════════════════════════

FW, FH = 1080, 1350
COLS = 3
RW = FW * COLS
FM = int(FW * 0.082)
BAR_Y = 700                                        # 판 가운데. 위아래로 매단다
BAR0, BAR1 = FM, RW - FM


def x_of(minute):
    return BAR0 + (BAR1 - BAR0) * minute / TOTAL


def overlap(x0, x1, col):
    return min(x1, (col + 1) * FW) - max(x0, col * FW)


def slots(fname):
    """이름을 어디에 놓을지 미리 다 계산한다."""
    out = []
    for i, (n, a, b) in enumerate(LINEUP):
        x0, x1 = x_of(mins(a)), x_of(mins(b))
        w = tracked_w(n, fname, 0.06)
        # 구간이 더 많이 걸친 칸으로. 밀어도 이름 가운데는 구간 안에 남는다
        col = max(range(COLS), key=lambda c: overlap(x0, x1, c))
        lo, hi = col * FW + FM, (col + 1) * FW - FM - w
        x = min(max((x0 + x1) / 2 - w / 2, lo), hi)
        out.append((n, a, b, x0, x1, x, i % 2 == 0))
    return out


def strip_bg():
    """세 칸짜리 배경. **밝기를 올려 둔다** — 어두우면 피드에서 검은
    사각형으로 보이고, 그러면 셋이 이어진 것도 안 보인다."""
    img = sky(RW, FH, [(0.0, (0.066, 0.066, 0.082)),
                       (0.44, (0.110, 0.110, 0.138)),
                       (1.0, (0.048, 0.048, 0.062))])
    bokeh(img, n=34, seed=3, y0=0.02, y1=0.30)
    bokeh(img, n=18, seed=8, y0=0.70, y1=0.98)
    MR = int(FW * 0.30)
    mf = moonface(MR)
    mf[..., :3] *= 0.52
    over(img, mf, RW - int(FW * 0.10) - MR, -int(MR * 0.50))
    return img


def sheet_draw():
    """세 칸을 가로지르는 것만 여기서 그린다 — 막대와 이름."""
    img = strip_bg()
    pil = Image.fromarray(
        (np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    fname = font(BRAND_FONT, 132)
    ftime = font(BRAND_FONT, step(-1))

    d.line([(BAR0, BAR_Y), (BAR1, BAR_Y)], fill=(86, 89, 100, 255), width=3)
    for i, (n, a, b, x0, x1, x, up) in enumerate(slots(fname)):
        # 다섯 구간이 막대를 나눠 갖는다. 눈금이 경계고, 이름은 자기
        # 구간 바로 위(또는 아래)에 선다
        d.line([(x0 + 3, BAR_Y), (x1 - 3, BAR_Y)],
               fill=(198, 202, 214, 255), width=6)
        for xx in (x0, x1):
            d.line([(xx, BAR_Y - U * 3), (xx, BAR_Y + U * 3)],
                   fill=(150, 154, 166, 255), width=2)

        p = silver(n, fname)
        # 막대에서 띄운다. 붙으면 막대가 이름의 밑줄로 보인다
        py = BAR_Y - U * 8 - p.shape[0] if up else BAR_Y + U * 8
        put(pil, p, x, py)
        line = f'{i + 1:02d}   {a} — {b}'
        ty = py - U * 3 - hh(line, ftime) if up else py + p.shape[0] + U * 3
        tracked(d, (x + 12, ty), line, ftime, 0.14, DIM)
    return pil


def panel(sheet, col):
    tile = sheet.crop((col * FW, 0, (col + 1) * FW, FH)).convert('RGBA')
    d = ImageDraw.Draw(tile)

    # 칸마다 머리글을 다시 단다. 타임라인에서는 옆 칸이 안 보인다
    fe = font(BRAND_FONT, step(-2))
    tracked(d, (FM, 150), f'{TITLE}   ·   {DATE}', fe, 0.22, DIM)
    d.text((FM, 150 + hh(TITLE, fe) + U * 2), '라인업',
           font=font(KR, step(-1)), fill=FAINT)
    if col == 0:
        logo_at(tile, FW, FM, 150 + hh(TITLE, fe) + U * 9, 0.26)
    d.text((FM, 1218), STRIP + ' · 예매 파티모아',
           font=font(KR, step(-1)), fill=DIM)

    return finish(tile, FW, FH, f'L{col + 1}', vig=0.26)


def feed():
    sheet = sheet_draw()
    tiles = [panel(sheet, c) for c in range(COLS)]
    g = Image.new('RGB', (FW * 3 + 16, FH), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (FW + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_라인업격자.jpg'), quality=92)


def main():
    story()
    feed()
    print('완료:', OUT)


if __name__ == '__main__':
    main()
