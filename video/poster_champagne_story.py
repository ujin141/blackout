"""
**AFTER MOON · 샴페인 스토리.** 한 장. 화려하되 검정·은색 안에서.

    python poster_champagne_story.py   →  out/moon/champagne_story.jpg

## 판

    30만원 / 샴페인       은색 금속 글자. 맨 위
    달 + 병               큰 달 앞에 병. 달빛이 병을 비추고, 빛줄기가 위로 뻗는다
    기포                  판 전체에 잔 거품이 오른다. 병 주변이 제일 촘촘하다
    조건 두 줄            여자 3명 이상 · 선착순 2팀
    AFTER MOON 09.26      마지막 두 줄. 예매 PARTYMOA

색은 병 하나다. 나머지는 검정·은색·흰색 — 크루 색. 화려함은 색이 아니라
빛(블룸)과 입자(기포)로 낸다.

인스타 UI 가 덮는 위 250 · 아래 320 은 비운다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import night, sky
from fonts import KR, KRB
from poster_champagne import LINES, SUB, SUB2, bottle_rgba
from poster_hook import BRAND_FONT, DIM, FAINT, INK, RULE, U, font, hh, probe, silver_text, step
from poster_kit import bloom, grain
from poster_lounge import bokeh
from poster_moon import CTA, CTA_KO, DATE, LOGO, OUT, TITLE, godrays, moonface, over, starfield, tracked, tracked_w

W, H = 1080, 1920
M = int(W * 0.082)
TOP, BOT = 250, 1600
CX = W // 2


def bubbles(img, n, cx, cy, spread, seed, a=1.0):
    """기포. 병 둘레가 촘촘하고 멀어질수록 성기다. 큰 놈은 테두리가 있다."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for _ in range(n):
        x = cx + rng.normal(0, spread)
        y = cy + rng.normal(0, spread * 1.6)
        if not (0 <= x < W and TOP - 80 <= y < BOT + 80):
            continue
        r = float(rng.choice([2, 3, 4, 6, 9, 13], p=[.30, .26, .18, .13, .08, .05]))
        k = rng.uniform(0.35, 1.0) * a
        d2 = (xx - x) ** 2 + (yy - y) ** 2
        if r >= 6:
            ring = np.exp(-((np.sqrt(d2) - r) ** 2) / (2 * (r * 0.22) ** 2))
            core = np.exp(-d2 / (2 * (r * 0.45) ** 2)) * 0.35
            img += (ring * 0.9 + core)[..., None] * k * np.float32([0.86, 0.88, 0.95])
        else:
            img += np.exp(-d2 / (2 * r ** 2))[..., None] * k * np.float32([0.9, 0.92, 1.0])


def main():
    img = sky(W, H, [(0.0, (0.022, 0.022, 0.032)),
                     (0.45, (0.060, 0.058, 0.086)),
                     (1.0, (0.020, 0.020, 0.030))])
    starfield(img, TOP - 60, BOT + 60, 220, seed=9)
    bokeh(img, n=14, seed=3, y0=0.10, y1=0.36)
    bokeh(img, n=10, seed=8, y0=0.62, y1=0.90)

    # ── 달 + 병 자리
    b = bottle_rgba()
    bh = 700
    bw = int(b.shape[1] * bh / b.shape[0])
    b = cv2.resize(b, (bw, bh), interpolation=cv2.INTER_CUBIC)
    by = 520
    bx = CX - bw // 2
    mcy = by + int(bh * 0.52)
    MR = 360

    godrays(img, CX, mcy, MR, seed=5, a=0.16)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - CX) ** 2 + (yy - mcy) ** 2) / (2 * (MR * 1.5) ** 2)))[..., None] * \
        np.float32([0.10, 0.10, 0.14])
    mf = moonface(MR)
    mf[..., :3] *= 0.92
    over(img, mf, CX - MR, mcy - MR)
    # 달 앞, 병 뒤에 어둠 한 겹. 달이 너무 밝으면 병이 묻힌다
    img *= 1 - 0.28 * np.exp(-(((xx - CX) / (bw * 0.75)) ** 2) - (((yy - mcy) / (bh * 0.5)) ** 2))[..., None]

    # 기포. 병 둘레 촘촘, 판 전체 성기게
    bubbles(img, 190, CX, mcy, 260, seed=21, a=0.85)
    bubbles(img, 120, CX, mcy, 520, seed=22, a=0.5)
    # 바닥 그림자
    img *= 1 - 0.45 * np.exp(-(((xx - CX) / (bw * 0.5)) ** 2) - (((yy - (by + bh)) / (U * 2.5)) ** 2))[..., None]

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    pil.alpha_composite(Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8), 'RGBA'), (bx, by))
    # 병 앞을 지나는 기포 몇 개. 뒤에만 있으면 병이 판에 붙어 보인다
    front = np.zeros((H, W, 3), np.float32)
    bubbles(front, 46, CX, mcy, 300, seed=23, a=0.7)
    fa = np.clip(front.max(axis=2), 0, 1)
    fr = np.dstack([np.clip(front / np.maximum(fa[..., None], 1e-3), 0, 1), fa[..., None]])
    pil.alpha_composite(Image.fromarray((fr * 255).astype(np.uint8), 'RGBA'))
    d = ImageDraw.Draw(pil)

    # ── 머리
    fe = font(BRAND_FONT, step(-1))
    tracked(d, (M, TOP + U), 'BLACKOUT CREW', fe, 0.40, FAINT)
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.19)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    pil.alpha_composite(lg, (W - M - lw, TOP))

    # ── 후크. 한 줄, 판 폭 가득. 스토리는 병이 주인공이라 글은 한 줄로 받는다
    hook = ' '.join(LINES)
    col = W - M * 2
    fh = font(KRB, 40)
    for size in range(300, 34, -2):
        f = font(KRB, size)
        if tracked_w(hook, f, -0.02) <= col:
            fh = f
            break
    h = silver_text(hook, fh, -0.02)
    y = TOP + U * 6
    pil.alpha_composite(Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8), 'RGBA'),
                        (CX - h.shape[1] // 2, y))
    y += h.shape[0]
    assert y < by + 40, (y, by)

    # ── 조건. 병 아래, 가운데
    y = by + bh + U * 3
    f1, f2 = font(KRB, step(3)), font(KR, step(1))
    d.text((CX - probe.textlength(SUB, font=f1) / 2, y), SUB, font=f1, fill=INK)
    y += hh(SUB, f1) + U
    d.text((CX - probe.textlength(SUB2, font=f2) / 2, y), SUB2, font=f2, fill=DIM)
    y += hh(SUB2, f2) + U * 3

    # 은선 두 줄 사이에 파티 정보
    d.line([(M, y), (W - M, y)], fill=(120, 124, 138, 255), width=1)
    y += U * 2
    fn, fd = font(BRAND_FONT, step(1)), font(BRAND_FONT, step(1))
    line = f'{TITLE}   ·   {DATE}'
    wl = tracked_w(line, fn, 0.16)
    tracked(d, (CX - wl / 2, y), line, fn, 0.16, INK)
    y += hh(line, fn) + U
    fk = font(KR, step(0))
    t = '압구정 딥하우즈 · 22:00 — 02:10 · 9,900원 · 웰컴샷 포함'
    d.text((CX - probe.textlength(t, font=fk) / 2, y), t, font=fk, fill=DIM)
    y += hh(t, fk) + U * 2
    d.line([(M, y), (W - M, y)], fill=(120, 124, 138, 255), width=1)
    y += U * 2
    fc, ff = font(BRAND_FONT, step(1)), font(KR, step(-1))
    wk = probe.textlength(CTA_KO + '  ', font=ff)
    wc = tracked_w(CTA, fc, 0.22)
    x = CX - (wk + wc) / 2
    d.text((x, y + hh(CTA, fc) - hh(CTA_KO, ff)), CTA_KO, font=ff, fill=FAINT)
    tracked(d, (x + wk, y), CTA, fc, 0.22, (214, 217, 226, 255))
    y += hh(CTA, fc)
    if y > BOT:
        print(f'  ! 아래 안전선 {y - BOT}px 넘음')

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.55, W * 0.022, 0.42)
    grain(out, 0.010)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(OUT, 'champagne_story.jpg'), quality=94)
    night(out, 'champagne_story')
    print('완료: champagne_story.jpg')


if __name__ == '__main__':
    main()
