"""
**AFTER MOON 릴스 · 샴페인 세 편 + 이어지는 커버.** 무음. 매장 영상 위에.

    python reel_champagne.py          셋 다 + 커버
    python reel_champagne.py cover    커버만

    out/moon/C1_샴페인.mp4   C2_조건.mp4   C3_파티.mp4     (12초, 무음)
    out/moon/CC1.jpg CC2.jpg CC3.jpg                       (커버 1080×1920)
    out/moon/_샴페인릴스격자.jpg

## 세 편이 나누는 것

    1  샴페인   30만원 → 샴페인 → 병이 들어오고 기포가 오른다
    2  조건     여자 3명 이상 → 같이 오면 한 병 → 선착순 2팀 → 현장에서
    3  파티     AFTER MOON → 09.26 SAT → 장소·시간 → 값 → 성비

한 편에 다 넣으면 12초에 여섯 가지를 말한다. 나누면 편마다 할 말이 하나다.

## 커버는 격자에서 이어진다

피드 세 장(Q1~Q3)과 같은 뼈대 — 후크 · 병 · 파티 — 인데 **뒤에 매장
영상**이 깔린다. 같은 판을 두 줄 올리면 격자에서 복사한 것처럼 보인다.
띠(조건 한 줄)와 병 뒤 은빛이 세 장을 잇는 건 같다.

곡은 안 넣는다. 인스타에서 음원을 얹어야 릴스가 돈다.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

import feed_champagne as fc
from fonts import KR, KRB
from poster_champagne import bottle_rgba
from poster_hook import silver_text
from poster_moon import DATE, TITLE
from reel_moon import (DIM, FPS, H, INK, M, NF, OUT, SAFE_TOP, U, W,
                       beat, clip_frames, darken, end_card, fade, finish, font,
                       footage, plate, put, step, text_rgba)
from reel_moon2 import SHOTS_ALL, encode_silent, logo
from render import out_expo

SHOT = {n: (t0, d) for n, t0, d in SHOTS_ALL}
T_END = 9.8
BAND = 1350
BAND_Y = (H - BAND) // 2


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


def bottle(h):
    b = bottle_rgba()
    w = int(b.shape[1] * h / b.shape[0])
    return cv2.resize(b, (w, h), interpolation=cv2.INTER_CUBIC)


def popin(img, rgba, cx, cy, t, t0, d=0.35, big=1.18):
    k = fade(t, t0, d)
    if k <= 0:
        return
    s = big - (big - 1) * out_expo(k)
    r = cv2.resize(rgba, None, fx=s, fy=s)
    put(img, r, cx - r.shape[1] / 2, cy - r.shape[0] / 2, k)


def base(cuts, t):
    """이 시각의 매장 컷. 어둡게 눌러 앞이 선다."""
    ci = max(j for j, (_, t0) in enumerate(cuts) if t >= t0)
    name, t0 = cuts[ci]
    files = clip_frames(name, *SHOT[name])
    nxt = cuts[ci + 1][1] if ci + 1 < len(cuts) else T_END + 2
    k = (t - t0) / max(0.01, nxt - t0)
    img = footage(files[min(len(files) - 1, int(k * len(files)))], 1.0 + 0.06 * k)
    img *= 0.74
    logo(img, M, SAFE_TOP + U * 2, 0.22)
    return img, ci, t0


# ── 1. 샴페인 ─────────────────────────────────────────
def reel_1():
    cuts = [('s_sign', 0.0), ('s_room', beat(4)), ('s_crowd', beat(12))]
    bs = bubble_set(150, 21)
    b = bottle(760)
    h1 = silver_text('30만원', font(KRB, 250), 0.0)
    h2 = silver_text('샴페인', font(KRB, 250), 0.0)
    lab = text_rgba('한 병 · 두 팀까지', KR, step(1), DIM)
    c1 = silver_text('여자 3명 이상', font(KRB, 120), 0.0)
    c2 = text_rgba('같이 오면 드려요', KR, step(2), INK)

    def frames():
        for i in range(NF):
            t = i / FPS
            img, ci, t0 = base(cuts, t)
            if ci == 0:
                darken(img, int(H * 0.30), int(H * 0.72), 0.55)
                popin(img, h1, W / 2, H * 0.42, t, 0.15)
                popin(img, h2, W / 2, H * 0.58, t, beat(2) - 0.1)
            elif ci == 1:
                img *= 0.82
                bubbles(img, bs, t, t0 + 0.2, 0.9)
                popin(img, b, W / 2, H * 0.50, t, t0, 0.5, 1.12)
                put(img, lab, (W - lab.shape[1]) / 2, H * 0.50 + 380 + U * 3, fade(t, t0 + 0.8))
            else:
                darken(img, int(H * 0.30), int(H * 0.70), 0.6)
                bubbles(img, bs, t, cuts[1][1] + 0.2, 0.3)
                if t < T_END:
                    popin(img, c1, W / 2, H * 0.44, t, t0)
                    put(img, c2, (W - c2.shape[1]) / 2, H * 0.44 + 90, fade(t, t0 + 0.3))
            end_card(img, t, T_END)
            yield finish(img)

    encode_silent('C1_샴페인', frames())


# ── 2. 조건 ───────────────────────────────────────────
def reel_2():
    cuts = [('s_crowd', 0.0), ('s_bar', beat(5)), ('s_room', beat(10)), ('s_sign2', beat(15))]
    bs = bubble_set(90, 22)
    b = bottle(420)
    lines = ['여자 3명 이상', '같이 오면 한 병', '선착순 2팀']
    big = [silver_text(t_, font(KRB, 150), 0.0) for t_ in lines]
    subs = [text_rgba(s_, KR, step(1), DIM) for s_ in ('셋이 오면 됩니다', '30만원 샴페인', '먼저 온 두 팀')]
    last = plate('2 TEAMS', step(3), 0.24)
    lastk = text_rgba('현장에서 드려요', KR, step(2), INK)

    def frames():
        for i in range(NF):
            t = i / FPS
            img, ci, t0 = base(cuts, t)
            darken(img, int(H * 0.28), int(H * 0.74), 0.8 if ci == 3 else 0.6)
            bubbles(img, bs, t, 0.3, 0.35)
            if ci < 3:
                popin(img, big[ci], W / 2, H * 0.44, t, t0)
                put(img, subs[ci], (W - subs[ci].shape[1]) / 2, H * 0.44 + 110, fade(t, t0 + 0.3))
                if ci == 1:
                    popin(img, b, W / 2, H * 0.70, t, t0 + 0.4, 0.5, 1.1)
            elif t < T_END:
                popin(img, last, W / 2, H * 0.42, t, t0)
                put(img, lastk, (W - lastk.shape[1]) / 2, H * 0.42 + 90, fade(t, t0 + 0.3))
            end_card(img, t, T_END)
            yield finish(img)

    encode_silent('C2_조건', frames())


# ── 3. 파티 ───────────────────────────────────────────
def reel_3():
    cuts = [('s_sign', 0.0), ('s_bar', beat(4)), ('s_grill', beat(9)), ('s_crowd', beat(13))]
    n1 = plate(TITLE, step(5), 0.16)
    n2 = plate(DATE, step(4), 0.06)
    rows = [('압구정 딥하우즈', '22:00 — 02:10'),
            ('9,900원', '웰컴샷 포함 · 남녀 같은 값'),
            ('1차 30명', '남녀 15 : 15 · 한쪽 차면 마감')]
    bigs = [silver_text(a, font(KRB, 140), 0.0) for a, _ in rows]
    smalls = [text_rgba(b_, KR, step(1), DIM) for _, b_ in rows]

    def frames():
        for i in range(NF):
            t = i / FPS
            img, ci, t0 = base(cuts, t)
            darken(img, int(H * 0.28), int(H * 0.72), 0.8 if ci == 0 else 0.6)
            if ci == 0:
                popin(img, n1, W / 2, H * 0.44, t, 0.1)
                popin(img, n2, W / 2, H * 0.44 + 120, t, beat(2) - 0.1)
            elif t < T_END:
                j = ci - 1
                popin(img, bigs[j], W / 2, H * 0.44, t, t0)
                put(img, smalls[j], (W - smalls[j].shape[1]) / 2, H * 0.44 + 100, fade(t, t0 + 0.3))
            end_card(img, t, T_END)
            yield finish(img)

    encode_silent('C3_파티', frames())


# ── 커버 ──────────────────────────────────────────────
COVER_SRC = [('s_sign', 0.55), ('s_room', 0.5), ('s_bar', 0.6)]


def covers():
    """피드 판 뒤에 매장 컷을 깐다. 띠·병·글은 feed_champagne 이 그린다."""
    img, b, bx, by = fc.sheet()
    for c, (name, frac) in enumerate(COVER_SRC):
        files = clip_frames(name, *SHOT[name])
        fr = footage(files[min(len(files) - 1, int(len(files) * frac))])
        tile = fr[BAND_Y:BAND_Y + BAND]
        tile = cv2.GaussianBlur(tile, (0, 0), 1.2) * 0.42
        img[:, c * W:(c + 1) * W] = img[:, c * W:(c + 1) * W] * 0.55 + tile
    tiles = fc.render(img, b, bx, by, ('CC1', 'CC2', 'CC3'), '_샴페인릴스격자.jpg', marks=True)
    # 릴스 커버는 1080×1920. 가운데 4:5 만 격자에 보인다. 위아래는 같은 컷을 어둡게
    for c, (name, frac) in enumerate(COVER_SRC):
        files = clip_frames(name, *SHOT[name])
        fr = footage(files[min(len(files) - 1, int(len(files) * frac))]) * 0.25
        full = Image.fromarray((np.clip(fr, 0, 1) * 255).astype(np.uint8))
        full.paste(tiles[c], (0, BAND_Y))
        full.save(os.path.join(OUT, f'CC{c + 1}.jpg'), quality=94)
    print('커버 완료: CC1 CC2 CC3')


def main(argv):
    if 'cover' in argv:
        covers()
        return
    reel_1()
    reel_2()
    reel_3()
    covers()


if __name__ == '__main__':
    main(sys.argv[1:])
