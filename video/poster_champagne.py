"""
**AFTER MOON 포스터 · 샴페인.** 여자 셋 이상 오면 30만원 샴페인 한 병, 두 팀까지.

    python poster_champagne.py   →  out/moon/champagne_피드.jpg · champagne_스토리.jpg

## 판

후크 판(poster_hook)과 같은 뼈대다. 다른 건 하나 — 달 자리에 **병**이 선다.
사진은 흰 배경이라 물을 부어 따고(flood fill), 가장자리를 한 픽셀 녹인다.
병 뒤에 은빛 한 겹을 깔아서 검정 판에서 떠 보이게 한다.

    30만원          숫자가 먼저. 샴페인보다 값이 멈추게 한다
    샴페인
    여자 3명 이상 같이 오면 한 병 · 선착순 2팀

## 없는 말은 안 쓴다

병 이름·브랜드·용량은 안 적는다. 사진에 라벨이 있으니 그걸로 충분하고,
적었다가 현장 병이 다르면 그게 사고다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import night, sky, vignette
from fonts import KR, KRB
from poster_hook import (BRAND_FONT, DIM, FAINT, INK, RULE, STRIP, U, fit, font,
                         hh, probe, silver_text, step)
from poster_kit import bloom, grain
from poster_lounge import bokeh
from poster_moon import ARC_BOT, CTA, CTA_KO, DATE, LEAD, LOGO, OUT, TITLE, tracked, tracked_w

HERE = os.path.dirname(os.path.abspath(__file__))
BOTTLE = os.path.join(HERE, 'assets', 'champagne.jpg')

LINES = ['30만원', '샴페인']
SUB = '여자 3명 이상 같이 오면 한 병'
SUB2 = '선착순 2팀 · 현장에서 드려요'


def bottle_rgba():
    """흰 배경을 물 부어 따기. 라벨의 흰색은 병 안에 갇혀 있어 안 빠진다."""
    im = cv2.imread(BOTTLE)
    h, w = im.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1)]:
        cv2.floodFill(im.copy(), mask, seed, (0, 0, 0), (2, 2, 2), (2, 2, 2),
                      cv2.FLOODFILL_MASK_ONLY | 4)
    a = (mask[1:-1, 1:-1] == 0).astype(np.float32)
    a = cv2.erode(a, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(a, (0, 0), 0.8)
    rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    ys, xs = np.where(a > 0.02)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return np.dstack([rgb[y0:y1, x0:x1], a[y0:y1, x0:x1, None]])


def build(W, H, top, bot, tag):
    M = int(W * 0.082)
    col = int((W - M * 2) * 0.66)          # 후크는 왼쪽 2/3. 오른쪽은 병 자리

    fsub = font(KRB, step(2))
    fsub2 = font(KR, step(1))
    fname = font(BRAND_FONT, step(1))
    fdate = font(BRAND_FONT, step(2))
    flead = font(KR, step(-1))
    fstrip = font(KR, step(-1))
    fcta, ffoot = font(BRAND_FONT, step(0)), font(KR, step(-2))
    fgen = font(BRAND_FONT, step(-2))

    lower = (hh(TITLE, fname) + U * 2 + hh(DATE, fdate) + U + hh(LEAD, flead)
             + U * 4 + 2 + U * 3 + hh(STRIP, fstrip) + U * 3 + 2
             + U * 3 + hh(CTA, fcta))

    y_hook = top + U * 5
    avail = (bot - lower - U * 5) - y_hook
    subs_h = U * 2 + hh(SUB, fsub) + U + hh(SUB2, fsub2)
    fh = font(KRB, 40)
    for size in range(440, 34, -2):
        f = font(KRB, size)
        if any(tracked_w(t, f, 0.0) > col for t in LINES):
            continue
        tall = sum(hh(t, f) for t in LINES) + int(U * 0.4)
        if tall + subs_h <= avail:
            fh = f
            break
    hooks = [silver_text(t, fh, 0.0) for t in LINES]
    tall = sum(h.shape[0] for h in hooks) + int(U * 0.4)
    y = y_hook

    # ── 방 ──
    img = sky(W, H, [(0.0, (0.030, 0.030, 0.038)),
                     (0.55, (0.052, 0.052, 0.066)),
                     (1.0, (0.026, 0.026, 0.034))])
    bokeh(img, n=16, seed=3, y0=0.02, y1=0.30)
    bokeh(img, n=8, seed=8, y0=0.66, y1=0.96)

    # ── 병 ──  후크 오른쪽, 아래 글 위까지
    b = bottle_rgba()
    bh = int((bot - lower - U * 4) - (top + U * 5))
    bw = int(b.shape[1] * bh / b.shape[0])
    b = cv2.resize(b, (bw, bh), interpolation=cv2.INTER_CUBIC)
    bx = W - M - bw + int(U * 1.5)
    by = top + U * 5
    # 뒤에 은빛 한 겹. 검정 판에 흰 병이 오려 붙인 것처럼 보이지 않게
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - (bx + bw / 2)) / (bw * 0.9)) ** 2)
                  - (((yy - (by + bh * 0.55)) / (bh * 0.42)) ** 2))[..., None] * \
        np.float32([0.10, 0.105, 0.135])
    # 바닥 그림자
    img *= 1 - 0.35 * np.exp(-(((xx - (bx + bw / 2)) / (bw * 0.45)) ** 2)
                             - (((yy - (by + bh)) / (U * 2.2)) ** 2))[..., None]

    img += np.exp(-(((xx - W * 0.5) / (W * 0.62)) ** 2)
                  - (((yy - H) / (H * 0.30)) ** 2))[..., None] * \
        np.float32([0.030, 0.030, 0.042])

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    pil.alpha_composite(Image.fromarray((np.clip(b, 0, 1) * 255).astype(np.uint8), 'RGBA'), (bx, by))
    d = ImageDraw.Draw(pil)

    fe = font(BRAND_FONT, step(-2))
    tracked(d, (M, top + U * 2), 'BLACKOUT CREW', fe, 0.40, FAINT)

    # ── 후크 ──
    for h in hooks:
        pil.alpha_composite(
            Image.fromarray((np.clip(h, 0, 1) * 255).astype(np.uint8), 'RGBA'), (M, y))
        y += h.shape[0] + int(U * 0.4)
    # 조건은 후크와 아래 정보 **사이 한가운데**. 후크 밑에 붙이면 그 아래가
    # 텅 비고, 아래에 붙이면 후크가 떠 보인다. 빈 자리를 반으로 나눈다
    sub_h = hh(SUB, fsub) + U + hh(SUB2, fsub2)
    y = y + (bot - lower - U * 2 - y - sub_h) // 2
    d.text((M, y), SUB, font=fsub, fill=INK)
    y += hh(SUB, fsub) + U
    d.text((M, y), SUB2, font=fsub2, fill=DIM)

    # ── 아래 ──
    y = bot - lower
    tracked(d, (M, y), TITLE, fname, 0.20, INK)
    y += hh(TITLE, fname) + U * 2
    tracked(d, (M, y), DATE, fdate, 0.04, INK)
    y += hh(DATE, fdate) + U
    d.text((M, y), LEAD, font=flead, fill=FAINT)
    y += hh(LEAD, flead) + U * 4
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    d.text((M, y), STRIP, font=fstrip, fill=DIM)
    y += hh(STRIP, fstrip) + U * 3
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    d.text((M, y + (hh(CTA, fcta) - hh(ARC_BOT, fgen)) // 2), ARC_BOT, font=fgen, fill=FAINT)
    wc = tracked_w(CTA, fcta, 0.20)
    wk = probe.textlength(CTA_KO + ' ', font=ffoot)
    d.text((W - M - wc - wk, y + hh(CTA, fcta) - hh(CTA_KO, ffoot)), CTA_KO, font=ffoot, fill=FAINT)
    tracked(d, (W - M - wc, y), CTA, fcta, 0.20, (214, 217, 226, 255))

    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.17)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    pil.alpha_composite(lg, (W - M - lw, top + U))

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.60, W * 0.020, 0.30)
    vignette(out, 0.34, 1.9)
    grain(out, 0.010)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(OUT, f'{tag}.jpg'), quality=94)
    night(out, tag)


def main():
    build(1080, 1350, 90, 1266, 'champagne_피드')
    build(1080, 1920, 280, 1600, 'champagne_스토리')
    print('완료:', OUT)


if __name__ == '__main__':
    main()
