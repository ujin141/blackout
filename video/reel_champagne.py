"""
**AFTER MOON 릴스 · 샴페인.** 딥하우즈 매장 영상 위에 병과 조건.

    python reel_champagne.py   →  out/moon/C_샴페인.mp4        (12초, 종 소리 114)
                                  out/moon/C_샴페인_무음.mp4   (인스타에서 음원 얹기)
                                  out/moon/CC.jpg              (커버 1080×1920)

## 흐름 (컷은 박에)

    0박   간판         30만원 → 샴페인     은색 글자 두 방
    4박   홀           병이 들어온다. 기포가 오른다
    10박  사람들       여자 3명 이상 같이 오면 한 병 · 선착순 2팀
    14박  바           AFTER MOON · 09.26 SAT · 조건 한 줄
    9.8초 끝판         예매 PARTYMOA

영상은 어둡게 눌러 은색 글자와 병이 앞에 선다. 색은 병 하나.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

from fonts import KR, KRB
from poster_champagne import bottle_rgba
from poster_hook import BRAND_FONT, silver_text
from poster_moon import DATE, TITLE
from reel_moon import (DIM, FAINT, FPS, H, INK, M, NF, OUT, SAFE_BOT, SAFE_TOP, U, W,
                       beat, clip_frames, darken, encode, end_card, fade, finish, font,
                       footage, plate, put, step, text_rgba)
from reel_moon2 import SHOTS_ALL, encode_silent, logo
from render import out_expo

SHOT = {n: (t0, d) for n, t0, d in SHOTS_ALL}
CUTS = [('s_sign', 0.0), ('s_room', beat(4)), ('s_crowd', beat(10)), ('s_bar', beat(14))]
T_END = 9.8


def bubble_set(n, seed):
    rng = np.random.default_rng(seed)
    return [(rng.uniform(W * 0.15, W * 0.85), rng.uniform(H * 0.35, H * 1.05),
             float(rng.choice([2, 3, 4, 6, 9, 13], p=[.28, .26, .18, .14, .09, .05])),
             rng.uniform(90, 220), rng.uniform(0.35, 1.0)) for _ in range(n)]


def bubbles(img, bs, t, t0, a=1.0):
    """기포 층. t0 부터 위로 오른다. cv2 로 그려서 프레임마다 가볍다."""
    k = fade(t, t0, 0.6) * a
    if k <= 0:
        return
    lay = np.zeros((H, W), np.float32)
    for x, y0, r, v, al in bs:
        y = y0 - v * (t - t0)
        if y < SAFE_TOP - 40:
            continue
        c = (int(x + np.sin((t - t0) * 2.1 + y0) * 6), int(y))
        if r >= 6:
            cv2.circle(lay, c, int(r), al * 0.9, 2, cv2.LINE_AA)
            cv2.circle(lay, c, max(1, int(r * 0.35)), al * 0.4, -1, cv2.LINE_AA)
        else:
            cv2.circle(lay, c, int(r), al, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.7)
    img += lay[..., None] * k * np.float32([0.88, 0.90, 0.97])


def main(argv):
    by = {n: clip_frames(n, *SHOT[n]) for n, _ in CUTS}
    bs = bubble_set(150, 21)

    b = bottle_rgba()
    bh = 760
    bw = int(b.shape[1] * bh / b.shape[0])
    b = cv2.resize(b, (bw, bh), interpolation=cv2.INTER_CUBIC)

    h1 = silver_text('30만원', font(KRB, 250), 0.0)
    h2 = silver_text('샴페인', font(KRB, 250), 0.0)
    c1 = silver_text('여자 3명 이상', font(KRB, 132), 0.0)
    c2 = silver_text('같이 오면 한 병', font(KRB, 132), 0.0)
    c3 = plate('2 TEAMS', step(2), 0.24)
    c3k = text_rgba('선착순 2팀 · 현장에서 드려요', KR, step(1), INK)
    n1 = plate(TITLE, step(4), 0.16)
    n2 = plate(DATE, step(3), 0.06)
    n3 = text_rgba('압구정 딥하우즈 · 22:00 — 02:10', KR, step(1), DIM)
    n4 = text_rgba('9,900원 · 웰컴샷 포함 · 1차 30명 · 남녀 15:15', KR, step(0), FAINT)

    def frames():
        for i in range(NF):
            t = i / FPS
            ci = max(j for j, (_, t0) in enumerate(CUTS) if t >= t0)
            name, t0 = CUTS[ci]
            files = by[name]
            nxt = CUTS[ci + 1][1] if ci + 1 < len(CUTS) else T_END + 2
            k = (t - t0) / max(0.01, nxt - t0)
            fi = min(len(files) - 1, int(k * len(files)))
            img = footage(files[fi], 1.0 + 0.06 * k)
            img *= 0.74                                        # 전체를 눌러 앞이 선다
            logo(img, M, SAFE_TOP + U * 2, 0.22)

            if ci == 0:
                darken(img, int(H * 0.30), int(H * 0.72), 0.55)
                k1 = fade(t, 0.15, 0.35)
                s = 1.18 - 0.18 * out_expo(k1)
                r = cv2.resize(h1, None, fx=s, fy=s) if k1 > 0 else h1
                put(img, r, (W - r.shape[1]) / 2, H * 0.42 - r.shape[0] / 2, k1)
                k2 = fade(t, beat(2) - 0.1, 0.35)
                s = 1.18 - 0.18 * out_expo(k2)
                r = cv2.resize(h2, None, fx=s, fy=s) if k2 > 0 else h2
                put(img, r, (W - r.shape[1]) / 2, H * 0.58 - r.shape[0] / 2, k2)
            elif ci == 1:
                img *= 0.82
                bubbles(img, bs, t, t0 + 0.2, 0.9)
                kb = fade(t, t0, 0.5)
                s = 1.12 - 0.12 * out_expo(kb)
                r = cv2.resize(b, None, fx=s, fy=s)
                put(img, r, (W - r.shape[1]) / 2, H * 0.50 - r.shape[0] / 2, kb)
                lab = text_rgba('한 병 · 두 팀까지', KR, step(1), DIM)
                put(img, lab, (W - lab.shape[1]) / 2, H * 0.50 + bh / 2 + U * 3, fade(t, t0 + 0.8))
            elif ci == 2:
                darken(img, int(H * 0.26), int(H * 0.78), 0.6)
                bubbles(img, bs, t, CUTS[1][1] + 0.2, 0.35)
                put(img, c1, (W - c1.shape[1]) / 2, H * 0.36, fade(t, t0, 0.35))
                put(img, c2, (W - c2.shape[1]) / 2, H * 0.36 + c1.shape[0] + U, fade(t, t0 + 0.25, 0.35))
                y = H * 0.36 + c1.shape[0] + U + c2.shape[0] + U * 5
                put(img, c3, (W - c3.shape[1]) / 2, y, fade(t, t0 + 0.7))
                put(img, c3k, (W - c3k.shape[1]) / 2, y + c3.shape[0] + U * 2, fade(t, t0 + 0.9))
            else:
                darken(img, int(H * 0.30), int(H * 0.74), 0.6)
                if t < T_END:
                    put(img, n1, (W - n1.shape[1]) / 2, H * 0.38, fade(t, t0, 0.35))
                    put(img, n2, (W - n2.shape[1]) / 2, H * 0.38 + n1.shape[0] + U * 2, fade(t, t0 + 0.2, 0.35))
                    y = H * 0.38 + n1.shape[0] + U * 2 + n2.shape[0] + U * 4
                    put(img, n3, (W - n3.shape[1]) / 2, y, fade(t, t0 + 0.45))
                    put(img, n4, (W - n4.shape[1]) / 2, y + n3.shape[0] + U, fade(t, t0 + 0.6))
            end_card(img, t, T_END)
            out = finish(img)
            if i == int(3.6 * FPS):
                Image.fromarray(out).save(os.path.join(OUT, 'CC.jpg'), quality=94)
            yield out

    if 'silent' in argv:
        encode_silent('C_샴페인_무음', frames())
    else:
        encode('C_샴페인', frames())
        encode_silent('C_샴페인_무음', frames())


if __name__ == '__main__':
    main(sys.argv[1:])
