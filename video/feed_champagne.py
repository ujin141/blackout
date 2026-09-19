"""
**AFTER MOON · 샴페인 세 장.** 블랙아웃 계정, 한 줄에 셋.

    python feed_champagne.py   →  out/moon/Q1.jpg Q2.jpg Q3.jpg · _샴페인격자.jpg

## 한 줄이 한 판

    Q1   30만원 / 샴페인          여자 3명 이상 같이 오면 한 병
    Q2   병                        가운데 크게. 은빛이 양옆 칸으로 번진다
    Q3   AFTER MOON 09.26         조건 · 예매 PARTYMOA

셋을 잇는 건 둘이다. **띠** — 조건 한 줄이 세 칸 아래쪽을 같은 높이로
지난다. **빛** — 병 뒤 은빛이 왼쪽·오른쪽 칸 가장자리까지 닿는다.
비네트는 안 건다. 칸마다 가장자리를 어둡게 하면 격자에서 이음새가 보인다.

올리는 순서 Q3 → Q2 → Q1. 격자 새 글이 왼쪽 위.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import sky
from fonts import KR, KRB
from poster_champagne import LINES, SUB, SUB2, bottle_rgba
from poster_hook import BRAND_FONT, DIM, FAINT, INK, RULE, U, font, hh, probe, silver_text, step
from poster_kit import bloom, grain
from poster_lounge import bokeh
from poster_moon import ARC_BOT, CTA, CTA_KO, DATE, LEAD, LOGO, OUT, TITLE, tracked, tracked_w

W, H = 1080, 1350
RW = W * 3
M = int(W * 0.082)
TOP, BOT = 90, 1266
BAND_Y = int(H * 0.80)                 # 띠. 세 칸이 같은 높이
FACTS = ['22:00 — 02:10', '9,900원 · 웰컴샷 포함', '1차 30명 · 남녀 15 : 15', '혼자 와도 됩니다']


def sheet():
    img = sky(RW, H, [(0.0, (0.030, 0.030, 0.038)),
                      (0.55, (0.052, 0.052, 0.066)),
                      (1.0, (0.026, 0.026, 0.034))])
    bokeh(img, n=40, seed=3, y0=0.02, y1=0.30)
    bokeh(img, n=20, seed=8, y0=0.66, y1=0.96)

    # 병. 가운데 칸, 띠 위까지
    b = bottle_rgba()
    bh = int(BAND_Y - U * 9 - (TOP + U * 6))
    bw = int(b.shape[1] * bh / b.shape[0])
    b = cv2.resize(b, (bw, bh), interpolation=cv2.INTER_CUBIC)
    bx = W + (W - bw) // 2
    by = TOP + U * 6
    yy, xx = np.mgrid[0:H, 0:RW].astype(np.float32)
    # 은빛. 양옆 칸 가장자리까지 닿게 넓게
    img += np.exp(-(((xx - (bx + bw / 2)) / (W * 0.55)) ** 2)
                  - (((yy - (by + bh * 0.55)) / (bh * 0.5)) ** 2))[..., None] * \
        np.float32([0.11, 0.115, 0.15])
    img *= 1 - 0.4 * np.exp(-(((xx - (bx + bw / 2)) / (bw * 0.5)) ** 2)
                            - (((yy - (by + bh)) / (U * 2.5)) ** 2))[..., None]
    return img, b, bx, by


def band(d):
    """조건 한 줄이 세 칸을 지난다. 칸 경계에서 글자가 끊겨도 된다 —
    격자에서는 이어지고, 한 장씩 볼 때는 띠라는 걸 안다."""
    d.line([(0, BAND_Y), (RW, BAND_Y)], fill=RULE, width=1)
    f = font(KR, step(2))
    unit = f'{SUB}   ·   {SUB2}   ·   '
    x = M
    y = BAND_Y + U * 2
    while x < RW:
        d.text((x, y), unit, font=f, fill=INK)
        x += probe.textlength(unit, font=f)
    d.line([(0, y + hh(unit, f) + U * 2), (RW, y + hh(unit, f) + U * 2)], fill=RULE, width=1)


def render(img, b, bx, by, names=('Q1', 'Q2', 'Q3'), grid='_샴페인격자.jpg', marks=False):
    """판 위에 글을 얹고 세 장으로 자른다. 릴스 커버도 같은 함수로 뽑는다 —
    marks 가 True 면 칸마다 ▶ 릴스 표시를 단다."""
    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    pil.alpha_composite(Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8), 'RGBA'), (bx, by))
    d = ImageDraw.Draw(pil)
    band(d)

    fe = font(BRAND_FONT, step(-2))
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.17)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, TOP + U * 2), 'BLACKOUT CREW', fe, 0.40, FAINT)
        pil.alpha_composite(lg, (x0 + W - M - lw, TOP + U))
        n = font(BRAND_FONT, step(-2))
        tracked(d, (x0 + M, BOT - hh('0', n)), f'{c + 1:02d} / 03', n, 0.30, FAINT)
        if marks:
            d.polygon([(x0 + W - M - 150, BOT - 34), (x0 + W - M - 150, BOT), (x0 + W - M - 122, BOT - 17)], fill=(214, 217, 226, 255))
            d.text((x0 + W - M - 108, BOT - 34), '릴스 · 12초', font=font(KR, step(-2)), fill=FAINT)

    # ── Q1. 후크
    col = W - M * 2
    fh = font(KRB, 40)
    for size in range(460, 34, -2):
        f = font(KRB, size)
        if all(tracked_w(t, f, 0.0) <= col for t in LINES):
            fh = f
            break
    hooks = [silver_text(t, fh, 0.0) for t in LINES]
    y = TOP + U * 6
    for h in hooks:
        pil.alpha_composite(Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8), 'RGBA'), (M, y))
        y += h.shape[0] + int(U * 0.4)
    y += U * 3
    fs = font(KRB, step(2))
    d.text((M, y), SUB, font=fs, fill=INK)
    y += hh(SUB, fs) + U
    d.text((M, y), SUB2, font=font(KR, step(1)), fill=DIM)
    assert y + 60 < BAND_Y - U * 2

    # ── Q2. 병 위에 작은 말 하나
    f2 = font(KR, step(0))
    t2 = '한 병 · 두 팀까지'
    d.text((W + W // 2 - probe.textlength(t2, font=f2) / 2, BAND_Y - U * 3 - hh(t2, f2)), t2, font=f2, fill=DIM)

    # ── Q3. 파티 정보
    x0 = 2 * W
    fname, fdate, flead = font(BRAND_FONT, step(3)), font(BRAND_FONT, step(4)), font(KR, step(0))
    y = TOP + U * 7
    tracked(d, (x0 + M, y), TITLE, fname, 0.20, INK)
    y += hh(TITLE, fname) + U * 2
    tracked(d, (x0 + M, y), DATE, fdate, 0.04, INK)
    y += hh(DATE, fdate) + U
    d.text((x0 + M, y), LEAD, font=flead, fill=FAINT)
    y += hh(LEAD, flead) + U * 4
    d.line([(x0 + M, y), (x0 + W - M, y)], fill=RULE, width=1)
    y += U * 3
    fv = font(KRB, step(2))
    for line in FACTS:
        d.text((x0 + M, y), line, font=fv, fill=(230, 232, 239, 255))
        y += hh(line, fv) + int(U * 1.4)
    y += U * 2
    fcta, ffoot, fgen = font(BRAND_FONT, step(1)), font(KR, step(-1)), font(BRAND_FONT, step(-2))
    d.text((x0 + M, y + (hh(CTA, fcta) - hh(ARC_BOT, fgen)) // 2), ARC_BOT, font=fgen, fill=FAINT)
    y += hh(CTA, fcta) + U * 2
    wk = probe.textlength(CTA_KO + ' ', font=ffoot)
    d.text((x0 + M, y + hh(CTA, fcta) - hh(CTA_KO, ffoot)), CTA_KO, font=ffoot, fill=FAINT)
    tracked(d, (x0 + M + wk, y), CTA, fcta, 0.20, (214, 217, 226, 255))
    assert y + hh(CTA, fcta) < BAND_Y - U * 2, (y, BAND_Y)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.60, W * 0.020, 0.30)
    grain(out, 0.010)
    big = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    tiles = []
    for c in range(3):
        t = big.crop((c * W, 0, (c + 1) * W, H))
        t.save(os.path.join(OUT, f'{names[c]}.jpg'), quality=94)
        tiles.append(t)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, grid), quality=92)
    print('완료:', ' '.join(names))
    return tiles


def main():
    render(*sheet())


if __name__ == '__main__':
    main()
