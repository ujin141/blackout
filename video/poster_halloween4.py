"""
**BLACKOUT HALLOWEEN @ ZSPOT LOUNGE — 네온판.** 피드 세 장(이어짐) + 스토리.

    python poster_halloween4.py   →  out/halloween/HW1.jpg HW2.jpg HW3.jpg · _할로윈격자.jpg · HW_스토리.jpg

## 왜 네온인가

사진판은 딥하우즈 촬영본이었다 — 간판(dip houz)과 벽 그림이 그대로 보여서 **다른 가게 파티로 읽힌다.**
ZSPOT LOUNGE 사진이 오기 전까지는 어느 가게도 아닌 그림으로 간다.
라운지 바의 문법은 **벽돌 벽에 네온사인**이다. 클립아트처럼 안 보이려면 선 하나하나가
빛이어야 한다 — 관 안쪽은 하얗게 타고, 둘레는 색으로 번지고, 벽에 빛이 묻는다.

    HW1   네온 호박 (주황)         분장하고 오면 술 한 잔 서비스 (스티커)
    HW2   COSTUME PARTY 네온 (보라) · 박쥐
    HW3   네온 칵테일 (분홍)        ZSPOT LOUNGE · 주소
    셋    벽돌 벽이 세 장을 잇는다 · HALLOWEEN 네온 아홉 자 (HAL / LOW / EEN) · 아래 검정 띠

올리는 순서 HW3 → HW2 → HW1.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from poster_halloween import OUT, bat_points
from poster_halloween3 import (ADDR, BLACK, HANDLE, INK, ORANGE, TIME, VENUE, WORD, cond, kr, logo_img,
                               sticker, tape)
from poster_kit import grain

DATE = '10.30 FRI'                    # 10.30 금 22:00 → 10.31 토 03:00. 할로윈 전날 밤부터 당일 새벽까지
from poster_moon import fbm, tracked, tracked_w

NEON_OR = np.float32([1.0, 0.42, 0.06])
NEON_PU = np.float32([0.60, 0.20, 1.0])
NEON_PK = np.float32([1.0, 0.22, 0.58])


# ── 벽 ────────────────────────────────────────────────
def brick_wall(W, H, seed=3):
    """어두운 벽돌. 벽돌마다 밝기가 다르고, 줄눈은 더 어둡고, 전체에 얼룩."""
    rng = np.random.default_rng(seed)
    bw, bh, gap = 132, 56, 6
    base = np.zeros((H, W), np.float32)
    for r, y in enumerate(range(-bh, H + bh, bh + gap)):
        off = (bw // 2) * (r % 2)
        for x in range(-bw - off, W + bw, bw + gap):
            v = 0.55 + rng.random() * 0.45
            base[max(0, y):max(0, y + bh), max(0, x):max(0, x + bw)] = v
    stain = fbm(H, W, 6, seed=seed + 5, base=6)
    grit = fbm(H, W, 3, seed=seed + 9, base=120)
    lum = base * (0.65 + 0.55 * stain) * (0.85 + 0.3 * grit)
    lum = cv2.GaussianBlur(lum, (0, 0), 0.8)
    wall = lum[..., None] * np.float32([0.105, 0.062, 0.070])
    return wall


# ── 네온 ──────────────────────────────────────────────
def outline(mask, t):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (t, t))
    return np.clip(cv2.dilate(mask, k) - cv2.erode(mask, k), 0, 1)


def neon(img, line, col, k=1.0):
    """관 · 번짐 · 벽에 묻은 빛. line 은 0~1 선 마스크."""
    tube = cv2.GaussianBlur(line, (0, 0), 1.4)
    halo = cv2.GaussianBlur(line, (0, 0), 9) * 2.2
    wide = cv2.GaussianBlur(line, (0, 0), 34) * 3.2
    room = cv2.GaussianBlur(line, (0, 0), 140) * 9.0
    img += (halo + wide)[..., None] * col * 0.55 * k
    img += room[..., None] * col * 0.20 * k
    core = np.clip(col * 0.45 + 0.62, 0, 1)
    img[...] = img * (1 - tube[..., None]) + core * tube[..., None] * 1.1


def poly_mask(H, W, polys, ellipses=()):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon(p, fill=255)
    for e in ellipses:
        d.ellipse(e, fill=255)
    return np.asarray(m, np.float32) / 255.0


def lines_mask(H, W, segs, width):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for s in segs:
        d.line(s, fill=255, width=width, joint='curve')
    return np.asarray(m, np.float32) / 255.0


def arc_mask(H, W, arcs, width):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for box, a0, a1 in arcs:
        d.arc(box, a0, a1, fill=255, width=width)
    return np.asarray(m, np.float32) / 255.0


def pumpkin_neon(H, W, cx, cy, s, t=9):
    """호박 테두리 · 골 두 줄 · 꼭지 · 눈코입. 전부 네온 선."""
    lobes = [(cx + dx * s - w * s / 2, cy - h * s / 2, cx + dx * s + w * s / 2, cy + h * s / 2)
             for dx, w, h in ((-0.30, 0.62, 0.86), (0.30, 0.62, 0.86), (0, 0.70, 0.92))]
    body = poly_mask(H, W, [], lobes)
    line = outline(body, t)
    line = np.maximum(line, arc_mask(H, W, [((cx - s * 0.22, cy - s * 0.44, cx + s * 0.06, cy + s * 0.44), 110, 250),
                                            ((cx - s * 0.06, cy - s * 0.44, cx + s * 0.22, cy + s * 0.44), 290, 70)], t // 2 + 2) * 0.0)
    stem = lines_mask(H, W, [[(cx, cy - s * 0.44), (cx + s * 0.02, cy - s * 0.56), (cx + s * 0.10, cy - s * 0.62)]], t)
    leaf = arc_mask(H, W, [((cx + s * 0.04, cy - s * 0.66, cx + s * 0.26, cy - s * 0.50), 180, 360)], t)
    face = poly_mask(H, W, [
        [(cx - s * 0.30, cy - s * 0.02), (cx - s * 0.08, cy - s * 0.02), (cx - s * 0.17, cy - s * 0.22)],
        [(cx + s * 0.30, cy - s * 0.02), (cx + s * 0.08, cy - s * 0.02), (cx + s * 0.17, cy - s * 0.22)],
        [(cx - s * 0.04, cy + s * 0.10), (cx + s * 0.04, cy + s * 0.10), (cx, cy + s * 0.02)],
        [(cx - s * 0.32, cy + s * 0.16)] + [(cx + x * s, cy + s * (0.20 + (0.06 if i % 2 else 0)))
                                           for i, x in enumerate(np.linspace(-0.24, 0.24, 7))]
        + [(cx + s * 0.32, cy + s * 0.16), (cx + s * 0.18, cy + s * 0.34), (cx - s * 0.18, cy + s * 0.34)],
    ])
    face_line = outline(face, t)
    return np.clip(line + stem + leaf + face_line, 0, 1)


def cocktail_neon(H, W, cx, cy, s, t=9):
    """마티니 잔 · 올리브 · 빨대."""
    bowl = poly_mask(H, W, [[(cx - s * 0.42, cy - s * 0.40), (cx + s * 0.42, cy - s * 0.40), (cx, cy + s * 0.10)]])
    line = outline(bowl, t)
    stem = lines_mask(H, W, [[(cx, cy + s * 0.10), (cx, cy + s * 0.52)]], t)
    foot = arc_mask(H, W, [((cx - s * 0.22, cy + s * 0.48, cx + s * 0.22, cy + s * 0.60), 180, 360),
                           ((cx - s * 0.22, cy + s * 0.48, cx + s * 0.22, cy + s * 0.60), 0, 180)], t)
    drink = lines_mask(H, W, [[(cx - s * 0.30, cy - s * 0.28), (cx + s * 0.30, cy - s * 0.28)]], t // 2 + 2)
    olive = outline(poly_mask(H, W, [], [(cx - s * 0.16, cy - s * 0.30, cx - s * 0.02, cy - s * 0.16)]), t)
    pick = lines_mask(H, W, [[(cx - s * 0.20, cy - s * 0.34), (cx + s * 0.18, cy - s * 0.66)]], t // 2 + 2)
    return np.clip(line + stem + foot + drink + olive + pick, 0, 1)


def bats_neon(H, W, spots, t=6):
    return outline(poly_mask(H, W, [bat_points(x, y, s, r, 1.0) for x, y, s, r in spots]), t)


def text_neon(H, W, text, f, x, y, t=8, track=0.0):
    m = Image.new('L', (W, H), 0)
    tracked(ImageDraw.Draw(m), (x, y), text, f, track, 255)
    return outline(np.asarray(m, np.float32) / 255.0, t)


def finish(img):
    out = np.clip(img, 0, 1)
    H, W = out.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = ((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.70)) ** 2
    out *= np.clip(1 - 0.35 * v, 0.45, 1)[..., None]
    grain(out, 0.014)
    return out


# ══════════════════════════════════════════════════════════
#  피드 세 장
# ══════════════════════════════════════════════════════════

def feed():
    W, H = 1080, 1350
    RW = W * 3
    M = 80
    img = brick_wall(RW, H)

    neon(img, pumpkin_neon(H, RW, 460, 500, 520), NEON_OR, 1.0)
    neon(img, bats_neon(H, RW, [(860, 220, 70, -0.2), (980, 330, 46, 0.15), (1240, 250, 54, 0.1),
                                (1880, 230, 62, -0.15), (2010, 340, 40, 0.2)]), NEON_PU, 0.9)
    f_cp = cond(150, 'Bold Condensed')
    for i, (t, dy) in enumerate((('COSTUME', 300), ('PARTY', 460))):
        x = W + (W - tracked_w(t, f_cp, 0.04)) / 2
        neon(img, text_neon(H, RW, t, f_cp, x, dy, 8, 0.04), NEON_PU if i == 0 else NEON_OR, 0.9)
    neon(img, cocktail_neon(H, RW, 2 * W + 330, 520, 420), NEON_PK, 1.0)

    # HALLOWEEN 네온. 아홉 칸에 한 자씩
    slot = RW / len(WORD)
    probe = ImageDraw.Draw(Image.new('L', (8, 8)))
    for s in range(520, 60, -4):
        f = cond(s)
        if max(probe.textlength(ch, font=f) for ch in WORD) <= slot * 0.74:
            break
    ly = 760
    m = Image.new('L', (RW, H), 0)
    dm = ImageDraw.Draw(m)
    for i, ch in enumerate(WORD):
        b = dm.textbbox((0, 0), ch, font=f)
        dm.text((slot * i + (slot - (b[2] - b[0])) / 2 - b[0], ly - b[1]), ch, font=f, fill=255)
    neon(img, outline(np.asarray(m, np.float32) / 255.0, 12), NEON_OR, 1.15)

    out = finish(img)
    pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    fe = cond(26, 'SemiLight Condensed')
    lg = logo_img(int(W * 0.17))
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, 96), 'BLACKOUT CREW PRESENTS', fe, 0.40, INK + (220,))
        pil.alpha_composite(lg, (x0 + W - M - lg.width, 88))

    st = sticker(['분장하고 오면', '술 한 잔', '서비스'], 170, -10)
    pil.alpha_composite(st, (W - st.width + 10, 380))
    tp3 = tape(VENUE, cond(92), 3)
    pil.alpha_composite(tp3, (2 * W + W - tp3.width - 50, 220))
    ta = tape(ADDR, kr(38), 3, bg=(18, 12, 22), fg=INK)
    pil.alpha_composite(ta, (2 * W + W - ta.width - 60, 220 + tp3.height - 4))
    d = ImageDraw.Draw(pil, 'RGBA')

    by = H - 150
    d.rectangle([0, by, RW, H], fill=BLACK + (240,))
    d.rectangle([0, by, RW, by + 6], fill=ORANGE + (255,))
    fd = cond(88)
    tracked(d, (M, by + 30), DATE, fd, 0.04, INK + (255,))
    tracked(d, (W + (W - tracked_w(TIME, fd, 0.04)) / 2, by + 30), TIME, fd, 0.04, INK + (255,))
    t3 = HANDLE.upper()
    f3 = cond(64)
    tracked(d, (2 * W + W - M - tracked_w(t3, f3, 0.04), by + 42), t3, f3, 0.04, ORANGE + (255,))

    big = pil.convert('RGB')
    tiles = []
    for c in range(3):
        t = big.crop((c * W, 0, (c + 1) * W, H))
        t.save(os.path.join(OUT, f'HW{c + 1}.jpg'), quality=94)
        tiles.append(t)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(os.path.join(OUT, '_할로윈격자.jpg'), quality=92)
    print('피드 완료')


# ══════════════════════════════════════════════════════════
#  스토리
# ══════════════════════════════════════════════════════════

def story():
    W, H = 1080, 1920
    M = 80
    TOP = 250
    img = brick_wall(W, H, seed=4)
    neon(img, pumpkin_neon(H, W, W // 2, 660, 520), NEON_OR, 1.0)
    neon(img, bats_neon(H, W, [(150, 470, 64, -0.2), (250, 580, 40, 0.15), (900, 430, 56, 0.1), (960, 560, 36, -0.1)]),
         NEON_PU, 0.9)
    probe = ImageDraw.Draw(Image.new('L', (8, 8)))
    for s in range(400, 60, -4):
        f = cond(s)
        if probe.textlength(WORD, font=f) <= W - M * 2 - 20:
            break
    ly = 1010
    m = Image.new('L', (W, H), 0)
    dm = ImageDraw.Draw(m)
    b = dm.textbbox((0, 0), WORD, font=f)
    dm.text(((W - (b[2] - b[0])) / 2 - b[0], ly - b[1]), WORD, font=f, fill=255)
    neon(img, outline(np.asarray(m, np.float32) / 255.0, 11), NEON_OR, 1.15)
    lh = b[3] - b[1]

    out = finish(img)
    pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    fe = cond(30, 'SemiLight Condensed')
    tracked(d, (M, TOP + 6), 'BLACKOUT CREW PRESENTS', fe, 0.40, INK + (220,))
    lg = logo_img(int(W * 0.19))
    pil.alpha_composite(lg, (W - M - lg.width, TOP))
    st = sticker(['분장하고 오면', '술 한 잔', '서비스'], 150, -10)
    pil.alpha_composite(st, (W - st.width + 30, 600))
    tp = tape('COSTUME PARTY', cond(70), -3)
    pil.alpha_composite(tp, ((W - tp.width) // 2, ly - tp.height - 6))
    d = ImageDraw.Draw(pil, 'RGBA')
    y = ly + lh + 40
    fd = cond(124)
    tracked(d, ((W - tracked_w(DATE, fd, 0.04)) / 2, y), DATE, fd, 0.04, INK + (255,))
    y += 140
    ft = cond(72)
    tracked(d, ((W - tracked_w(TIME, ft, 0.04)) / 2, y), TIME, ft, 0.04, ORANGE + (255,))
    y += 94
    tp3 = tape(VENUE, cond(66), 0)
    pil.alpha_composite(tp3, ((W - tp3.width) // 2, int(y)))
    y += tp3.height + 12
    d = ImageDraw.Draw(pil, 'RGBA')
    fk = kr(34)
    d.text(((W - d.textlength(ADDR, font=fk)) / 2, y), ADDR, font=fk, fill=INK + (255,))
    y += 48
    assert y < 1640, y

    pil.convert('RGB').save(os.path.join(OUT, 'HW_스토리.jpg'), quality=94)
    print('스토리 완료')


if __name__ == '__main__':
    feed()
    story()
