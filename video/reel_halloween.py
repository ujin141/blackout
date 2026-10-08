"""
**BLACKOUT HALLOWEEN 릴스 세 편 + 이어지는 커버.** 네온판 · 곡 셋 다 다르게.

    python audio_halloween.py      (곡 먼저)
    python reel_halloween.py       →  out/halloween/R1_할로윈.mp4 R2_코스튬.mp4 R3_장소.mp4 (12초)
                                      out/halloween/RC1.jpg RC2.jpg RC3.jpg · _릴스커버격자.jpg
    python reel_halloween.py cover

## 세 편

    R1  할로윈   bgm_organ      어두운 벽 → 네온 호박이 깜빡이며 켜진다 → 박쥐 → HALLOWEEN → 10.30 FRI
    R2  코스튬   bgm_musicbox   COSTUME · PARTY 가 켜지고 박쥐 떼가 지나간다 → 마녀 · 고양이 · 좀비 …
    R3  장소     bgm_carpenter  네온 맥주잔 → ZSPOT LOUNGE → 주소 → 22:00 — 03:00

끝 2.4초는 셋 다 같은 끝판 — 로고 · 날짜 · 장소 · @zspot_lounge.

## 네온을 싸게 그리는 법

네온 한 줄은 블러를 네 번 건다(관 · 번짐 · 넓은 번짐 · 벽에 묻는 빛). 프레임마다 하면 느리다.
**요소마다 한 번만 구워 두고**(빛 층 + 관 마스크) 프레임에서는 세기만 곱한다.
켜질 때 깜빡임은 정해진 순서로 — 꺼짐 · 켜짐 · 반쯤 · 꺼짐 · 켜짐 — 진짜 네온관처럼.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

from poster_halloween import OUT, bat_points
from poster_halloween3 import ADDR, HANDLE, INK, ORANGE, TIME, VENUE, WORD, cond, kr, logo_img, tape
from poster_halloween4 import (NEON_OR, NEON_PU, NEON_WH, NEON_YE, beer_neon, brick_wall, neon, outline, poly_mask,
                               pumpkin_neon, text_neon)
from poster_kit import grain
from poster_moon import tracked, tracked_w
from render import out_expo

W, H, FPS = 1080, 1920, 30
DUR = 12.0
NF = int(DUR * FPS)
T_END = 9.6
DATE = '10.30 FRI'
SAFE_TOP = 250
M = 80


# ── 네온 굽기 ─────────────────────────────────────────
def bake(line, col, k=1.0):
    """(빛 층, 관 마스크). 프레임에서 wall*(1-tube*a) + light*a."""
    z = np.zeros((H, W, 3), np.float32)
    neon(z, line, col, k)
    tube = cv2.GaussianBlur(line, (0, 0), 1.4)
    return z, tube


def lay(img, baked, a):
    if a <= 0:
        return
    light, tube = baked
    img *= (1 - tube[..., None] * a)
    img += light * a


def flicker(t, t0, seed=0):
    """켜질 때 깜빡임. t0 부터 0.7초. 그 뒤엔 아주 살짝 떨린다."""
    if t < t0:
        return 0.0
    d = t - t0
    seq = [0, 1, 0, 0, 0.4, 1, 0, 1, 1, 0.2, 1, 1, 1, 1]
    if d < 0.7:
        return float(seq[int(d / 0.05) % len(seq)])
    return 0.96 + 0.04 * np.sin(t * 37 + seed)


def bat_sprite(s):
    """
    날아다니는 박쥐 한 마리 — 판에 한 번 굽는다.

    처음엔 포스터용 neon() 을 그대로 썼다가 **박쥐마다 네모난 빛 상자**가 생겼다. neon() 은
    벽에 묻는 빛까지 아주 넓게 번지는데, 작은 판에서 그게 판 끝에서 잘린 것이다.
    날아다니는 건 번짐을 짧게 하고, 판을 넉넉히 잡고, 가장자리로 갈수록 0 이 되게 깎는다.
    """
    S = int(s * 4.2)
    line = outline(poly_mask(S, S, [bat_points(S / 2, S / 2, s, 0, 1.0)]), 6)
    tube = cv2.GaussianBlur(line, (0, 0), 1.3)
    halo = cv2.GaussianBlur(line, (0, 0), 5) * 2.0 + cv2.GaussianBlur(line, (0, 0), 14) * 2.2
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    win = np.clip(1 - np.hypot(xx - S / 2, yy - S / 2) / (S / 2), 0, 1) ** 1.5
    light = (halo * win)[..., None] * NEON_PU * 0.55
    core = np.clip(NEON_PU * 0.45 + 0.62, 0, 1)
    light += core * tube[..., None] * 1.1
    return light.astype(np.float32), tube


def add_sprite(img, spr, x, y, a=1.0):
    light, tube = spr
    h, w = tube.shape
    x, y = int(x - w / 2), int(y - h / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sl = (slice(y0 - y, y1 - y), slice(x0 - x, x1 - x))
    img[y0:y1, x0:x1] *= (1 - tube[sl][..., None] * a)
    img[y0:y1, x0:x1] += light[sl] * a


# ── 글 ────────────────────────────────────────────────
def rgba(im):
    return np.asarray(im.convert('RGBA'), np.float32) / 255.0


def txt(text, f, fill, track=0.0):
    probe = ImageDraw.Draw(Image.new('L', (8, 8)))
    w = int(tracked_w(text, f, track)) + 16
    b = probe.textbbox((0, 0), text, font=f)
    im = Image.new('RGBA', (w, b[3] + 12), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(im), (8, 4), text, f, track, fill)
    return rgba(im)


def put(img, a, cx, y, alpha=1.0, scale=1.0):
    if alpha <= 0:
        return
    if scale != 1.0:
        a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = a.shape[:2]
    x = int(cx - w / 2)
    y = int(y - h / 2)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = a[y0 - y:y1 - y, x0 - x:x1 - x]
    al = s[..., 3:4] * alpha
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - al) + s[..., :3] * al


def fade(t, t0, d=0.35):
    return float(np.clip((t - t0) / d, 0, 1))


def pop(img, a, cx, cy, t, t0, d=0.35):
    k = fade(t, t0, d)
    if k > 0:
        put(img, a, cx, cy, k, 1.15 - 0.15 * out_expo(k))


def head(img):
    put(img, HEAD, M + HEAD.shape[1] / 2, SAFE_TOP + 20)
    put(img, LOGO_A, W - M - LOGO_A.shape[1] / 2, SAFE_TOP + 18)


def wall_frame(base, t):
    """벽은 처음엔 거의 꺼져 있다가 네온이 켜지면서 드러난다."""
    return base * (0.55 + 0.45 * fade(t, 0.2, 1.2))


# ── 공통 ──────────────────────────────────────────────
WALL = brick_wall(W, H, seed=7)
HEAD = txt('BLACKOUT CREW PRESENTS', cond(30, 'SemiLight Condensed'), INK + (220,), 0.40)
LOGO_A = rgba(logo_img(int(W * 0.19)))
BAT = bat_sprite(56)
BAT_S = bat_sprite(34)


def end_card(img, t):
    """
    끝판. **앞 장면을 먼저 다 끄고(0.3초) 그다음 글을 올린다.** 같이 겹치게 하면
    반투명한 글 두 벌이 0.5초 동안 포개져서 아무것도 안 읽힌다.
    """
    off = fade(t, T_END - 0.3, 0.3)
    if off <= 0:
        return
    img *= 1 - 0.985 * off
    k = fade(t, T_END, 0.4)
    if k <= 0:
        return
    put(img, END_LOGO, W / 2, H * 0.34, k)
    put(img, END_DATE, W / 2, H * 0.43, k)
    put(img, END_TIME, W / 2, H * 0.49, k)
    put(img, END_VENUE, W / 2, H * 0.56, k)
    put(img, END_ADDR, W / 2, H * 0.61, k)
    put(img, END_HANDLE, W / 2, H * 0.66, k)


END_LOGO = rgba(logo_img(int(W * 0.40)))
END_DATE = txt(DATE, cond(130), INK + (255,), 0.04)
END_TIME = txt(TIME, cond(70), ORANGE + (255,), 0.04)
END_VENUE = rgba(tape(VENUE, cond(70), 0))
END_ADDR = txt(ADDR, kr(36), INK + (255,))
END_HANDLE = txt(HANDLE.upper(), cond(54), ORANGE + (255,), 0.04)


def finish(img):
    out = np.clip(img, 0, 1)
    grain(out, 0.012)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def encode(name, frames, bgm):
    dst = os.path.join(OUT, f'{name}.mp4')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', os.path.join(OUT, bgm), '-map', '0:v', '-map', '1:a',
           '-af', f'afade=t=out:st={DUR - 0.8:.2f}:d=0.8', '-t', f'{DUR:.2f}',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium', '-movflags', '+faststart',
           '-c:a', 'aac', '-b:a', '192k', dst]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    print('완료:', dst)


def halloween_word(cy, size=None):
    probe = ImageDraw.Draw(Image.new('L', (8, 8)))
    f = cond(size) if size else None
    if f is None:
        for s in range(400, 60, -4):
            f = cond(s)
            if probe.textlength(WORD, font=f) <= W - M * 2 - 20:
                break
    x = (W - tracked_w(WORD, f, 0.0)) / 2
    return bake(text_neon(H, W, WORD, f, x, cy, 11), NEON_OR, 1.15)


# ══════════════════════════════════════════════════════════
#  R1 할로윈
# ══════════════════════════════════════════════════════════

def reel_1():
    pk = bake(pumpkin_neon(H, W, W // 2, 680, 520), NEON_OR, 1.0)
    word = halloween_word(1075)
    s1 = txt(DATE, cond(124), INK + (255,), 0.04)
    s2 = txt(TIME, cond(72), ORANGE + (255,), 0.04)
    s3 = txt('할로윈 전날 밤, 새벽 3시까지', kr(42), INK + (255,))
    cp = rgba(tape('COSTUME PARTY', cond(70), -3))
    bats = [(150, 470, 0.0), (930, 430, 0.4), (130, 860, 0.7), (950, 880, 1.0)]

    def frames():
        for i in range(NF):
            t = i / FPS
            img = wall_frame(WALL, t)
            lay(img, pk, flicker(t, 0.3, 1))
            for j, (bx, by, ph) in enumerate(bats):
                a = flicker(t, 1.3 + j * 0.15, j)
                add_sprite(img, BAT if j % 2 == 0 else BAT_S, bx + np.sin(t * 2 + ph) * 18,
                           by + np.cos(t * 2.6 + ph) * 12, a)
            lay(img, word, flicker(t, 3.60, 3))          # 곡 드롭(3.75초)에 켜진다
            head(img)
            if t < T_END:
                pop(img, cp, W / 2, 972, t, 4.3)
                pop(img, s1, W / 2, 1440, t, 5.0)
                pop(img, s2, W / 2, 1540, t, 5.6)
                put(img, s3, W / 2, 1620, fade(t, 6.4))
            end_card(img, t)
            yield finish(img)

    encode('R1_할로윈', frames(), 'bgm_organ.wav')


# ══════════════════════════════════════════════════════════
#  R2 코스튬
# ══════════════════════════════════════════════════════════

def reel_2():
    f_cp = cond(230, 'Bold Condensed')
    w1 = bake(text_neon(H, W, 'COSTUME', f_cp, (W - tracked_w('COSTUME', f_cp, 0.04)) / 2, 520, 10, 0.04), NEON_PU, 1.0)
    w2 = bake(text_neon(H, W, 'PARTY', f_cp, (W - tracked_w('PARTY', f_cp, 0.04)) / 2, 770, 10, 0.04), NEON_OR, 1.0)
    rng = np.random.default_rng(4)
    lanes = [1420, 1470, 1690, 1740]          # 머리글 · COSTUME · PARTY · 큰 글 자리를 피한다
    flock = [(rng.uniform(-0.4, 0.4), lanes[k % len(lanes)] + rng.uniform(-30, 30), rng.uniform(260, 420), rng.random() < 0.5)
             for k in range(14)]
    words = ['마녀', '고양이', '좀비', '뱀파이어', '해골', '뭐든 OK']
    big = [txt(w_, kr(150), INK + (255,)) for w_ in words]
    sub = txt('뭐 입고 올지 정했어요?', kr(46), INK + (230,))
    s1 = txt(DATE, cond(124), INK + (255,), 0.04)
    s2 = txt(TIME, cond(72), ORANGE + (255,), 0.04)

    def frames():
        for i in range(NF):
            t = i / FPS
            img = wall_frame(WALL, t)
            lay(img, w1, flicker(t, 0.2, 1))
            lay(img, w2, flicker(t, 0.8, 2))
            # 박쥐 떼가 왼쪽에서 오른쪽으로
            for t0, y, v, small in flock:
                x = (t - 1.6 - t0) * v * 1.0 - 100
                if -150 < x < W + 150 and 1.6 < t < 6.8:
                    add_sprite(img, BAT_S if small else BAT, x, y + np.sin(t * 6 + y) * 14, 1.0)
            head(img)
            if t < T_END:
                if 2.2 <= t < 3.2:
                    put(img, sub, W / 2, 1150, fade(t, 2.2))
                for k, b in enumerate(big):
                    t0 = 3.2 + k * 0.55                      # 곡 드롭(3.2초)부터
                    if t0 <= t < t0 + 0.55:
                        put(img, b, W / 2, 1180, 1.0, 1.12 - 0.12 * out_expo(fade(t, t0, 0.2)))
                pop(img, s1, W / 2, 1400, t, 7.0)
                pop(img, s2, W / 2, 1510, t, 7.6)
            end_card(img, t)
            yield finish(img)

    encode('R2_코스튬', frames(), 'bgm_musicbox.wav')


# ══════════════════════════════════════════════════════════
#  R3 장소
# ══════════════════════════════════════════════════════════

def reel_3():
    glass, foam = beer_neon(H, W, W // 2 - 50, 790, 560)      # 웰컴드링크가 생맥이라 맥주잔
    ck = bake(glass, NEON_YE, 1.0)
    fm = bake(foam, NEON_WH, 0.8)
    vn = rgba(tape(VENUE, cond(110), -3))
    ad = txt(ADDR, kr(44), INK + (255,))
    s1 = txt(DATE, cond(124), INK + (255,), 0.04)
    s2 = txt(TIME, cond(72), ORANGE + (255,), 0.04)
    hd = txt(HANDLE.upper(), cond(60), ORANGE + (255,), 0.04)

    def frames():
        for i in range(NF):
            t = i / FPS
            img = wall_frame(WALL, t)
            lay(img, ck, flicker(t, 0.3, 4))
            lay(img, fm, flicker(t, 0.6, 5))
            for j, (bx, by) in enumerate(((180, 470), (900, 540))):
                add_sprite(img, BAT_S, bx + np.sin(t * 2.2 + j) * 16, by + np.cos(t * 2.8 + j) * 10, flicker(t, 1.0 + j * 0.2, j))
            head(img)
            if t < T_END:
                pop(img, vn, W / 2, 1230, t, 1.6)
                put(img, ad, W / 2, 1340, fade(t, 2.4))
                pop(img, s1, W / 2, 1440, t, 4.0)            # 곡 드롭(4.0초)
                pop(img, s2, W / 2, 1540, t, 4.6)
                put(img, hd, W / 2, 1625, fade(t, 6.4))
            end_card(img, t)
            yield finish(img)

    encode('R3_장소', frames(), 'bgm_carpenter.wav')


# ══════════════════════════════════════════════════════════
#  커버 — 세 장이 이어진다 (가운데 4:5 띠)
# ══════════════════════════════════════════════════════════

def covers():
    RW = W * 3
    BAND = 1350
    BY = (H - BAND) // 2
    img = brick_wall(RW, H, seed=11)
    # 줄 하나가 세 장을 꿴다
    line = np.zeros((H, RW), np.float32)
    cv2.line(line, (40, BY + 920), (RW - 40, BY + 920), 1.0, 8, cv2.LINE_AA)
    neon(img, line, NEON_PU, 0.8)
    neon(img, pumpkin_neon(H, RW, W // 2, BY + 380, 400), NEON_OR, 1.0)
    neon(img, outline(poly_mask(H, RW, [bat_points(W + x, BY + y, s, r, 1.0) for x, y, s, r in
                                        ((300, 360, 120, -0.2), (720, 300, 90, 0.15), (560, 520, 70, 0.1))]), 7), NEON_PU, 1.0)
    glass, foam = beer_neon(H, RW, 2 * W + W // 2 - 40, BY + 350, 380)
    neon(img, glass, NEON_YE, 1.0)
    neon(img, foam, NEON_WH, 0.8)
    big = cond(230, 'Bold Condensed')
    for c, (t, col) in enumerate((('10.30', NEON_OR), ('FRI', NEON_PU), ('22:00', NEON_YE))):
        x = c * W + (W - tracked_w(t, big, 0.04)) / 2
        neon(img, text_neon(H, RW, t, big, x, BY + 640, 10, 0.04), col, 1.0)
    out = np.clip(img, 0, 1)
    pil = Image.fromarray((out * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    lg = logo_img(int(W * 0.17))
    fe = cond(26, 'SemiLight Condensed')
    labels = ['01  할로윈', '02  코스튬', '03  장소']
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, BY + 70), 'BLACKOUT CREW PRESENTS', fe, 0.40, INK + (220,))
        pil.alpha_composite(lg, (x0 + W - M - lg.width, BY + 62))
        d.text((x0 + M, BY + 1000), labels[c], font=kr(40), fill=INK + (255,))
        d.polygon([(x0 + W - M - 170, BY + 1004), (x0 + W - M - 170, BY + 1046), (x0 + W - M - 136, BY + 1025)],
                  fill=INK + (255,))
        d.text((x0 + W - M - 120, BY + 1000), '릴스', font=kr(40), fill=INK + (255,))
    d.text((2 * W + M, BY + 1080), VENUE + ' · B1', font=cond(52), fill=ORANGE + (255,))
    big_img = pil.convert('RGB')
    tiles = []
    for c in range(3):
        t = big_img.crop((c * W, 0, (c + 1) * W, H))
        t.save(os.path.join(OUT, f'RC{c + 1}.jpg'), quality=94)
        tiles.append(t.crop((0, BY, W, BY + BAND)))
    g = Image.new('RGB', (W * 3 + 16, BAND), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(os.path.join(OUT, '_릴스커버격자.jpg'), quality=92)
    print('커버 완료: RC1 RC2 RC3')


if __name__ == '__main__':
    args = sys.argv[1:]
    if 'cover' in args:
        covers()
    else:
        picked = [a for a in args if a in ('1', '2', '3')] or ['1', '2', '3']
        for p in picked:
            {'1': reel_1, '2': reel_2, '3': reel_3}[p]()
        if not [a for a in args if a in ('1', '2', '3')]:
            covers()
