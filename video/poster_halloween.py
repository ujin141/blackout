"""
**BLACKOUT HALLOWEEN · 10.31 SAT.** 피드 세 장(이어짐) + 스토리 한 장.

    python poster_halloween.py   →  out/halloween/HW1.jpg HW2.jpg HW3.jpg · _할로윈격자.jpg
                                    out/halloween/HW_스토리.jpg

## 정해진 것만 적는다

날짜(10.31 토, 할로윈 당일)와 "분장하고 오면 술 서비스" 만 확정이다.
장소·값·라인업은 아직이라 **장소 곧 공개**로만 둔다. 없는 말은 안 쓴다.

## 셋을 잇는 것

    글자     HALLOWEEN 아홉 자를 아홉 칸에 한 자씩. 한 장에 딱 세 자 — HAL / LOW / EEN
             칸 경계에서 글자가 안 잘린다
    달       가운데 장 위에 큰 보름달. 빛줄기가 양옆 장까지 번진다
    박쥐     달 둘레에서 세 장을 가로질러 흩어진다
    땅       철창 울타리와 안개가 세 장 바닥을 지난다
    호박     셋째 장 울타리 앞에 하나. **색은 호박불 하나뿐** — 판은 검정·은색

비네트는 안 건다. 칸마다 가장자리를 누르면 격자에서 이음새가 보인다.

올리는 순서 HW3 → HW2 → HW1. 격자 새 글이 왼쪽 위.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import night, sky
from fonts import KR, KRB
from poster_hook import BRAND_FONT, DIM, FAINT, INK, U, font, hh, probe, silver_text, step
from poster_kit import bloom, grain
from poster_moon import LOGO, OUT as MOON_OUT, fbm, godrays, moonface, over, starfield, tracked, tracked_w

OUT = os.path.join(os.path.dirname(MOON_OUT), 'halloween')
os.makedirs(OUT, exist_ok=True)

WORD = 'HALLOWEEN'
DATE = '10.31 SAT'
PERK = '분장하고 오면 술 한 잔 서비스'
TBA = '장소 · 라인업 곧 공개'
SILVER = (196, 199, 210, 255)
BAT = (7, 7, 11, 255)
BAT_RIM = (78, 80, 94, 255)
EMBER = np.float32([1.0, 0.52, 0.12])          # 호박불. 판에서 유일한 색


# ── 박쥐 ──────────────────────────────────────────────
def _bez(p0, c, p1, n=8):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t ** 2 * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t ** 2 * p1[1])
            for t in np.linspace(0, 1, n)[1:]]


def _half(flap):
    """오른쪽 날개 반쪽. 윗변은 한 번 크게 휘고, 아랫변은 손가락 사이가 세 번 파인다."""
    tip = (1.0, -0.42 * flap)
    pts = [(0.10, -0.12)] + _bez((0.10, -0.12), (0.45, -0.62 * flap), tip, 12)
    fingers = [tip, (0.74, 0.02), (0.48, 0.10), (0.16, 0.14)]
    for p0, p1 in zip(fingers, fingers[1:]):
        mid = ((p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - 0.16)
        pts += _bez(p0, mid, p1, 8)
    return pts


def bat_points(cx, cy, s, rot=0.0, flap=1.0):
    half = _half(flap)
    body = [(0.06, 0.16), (0.03, 0.26), (0.0, 0.29), (-0.03, 0.26), (-0.06, 0.16)]
    head = [(-0.10, -0.12), (-0.07, -0.26), (-0.03, -0.17), (0.03, -0.17), (0.07, -0.26), (0.10, -0.12)]
    pts = half + body + [(-x, y) for x, y in reversed(half)] + head
    c, sn = np.cos(rot), np.sin(rot)
    return [(cx + (x * c - y * sn) * s, cy + (x * sn + y * c) * s) for x, y in pts]


def bats(d, spots):
    for cx, cy, s, rot, flap in spots:
        d.polygon(bat_points(cx, cy, s, rot, flap), fill=BAT)


def bat_swarm(n, cx, cy, spread_x, spread_y, smin, smax, seed, keep=None):
    rng = np.random.default_rng(seed)
    out = []
    while len(out) < n:
        x = cx + rng.normal(0, spread_x)
        y = cy + rng.normal(0, spread_y)
        if keep and not keep(x, y):
            continue
        s = smin + (smax - smin) * rng.random() ** 2.2
        out.append((x, y, s, rng.normal(0, 0.18), rng.uniform(0.7, 1.15)))
    return out


# ── 땅 ────────────────────────────────────────────────
def fence(d, W, base, h, pitch=58):
    top = base - h
    d.rectangle([0, top + h * 0.22, W, top + h * 0.22 + 7], fill=BAT)
    d.rectangle([0, base - h * 0.28, W, base - h * 0.28 + 7], fill=BAT)
    x = pitch // 2
    k = 0
    while x < W:
        hh_ = h * (1.0 if k % 5 else 1.12)
        t = base - hh_
        d.rectangle([x - 4, t, x + 4, base], fill=BAT)
        d.polygon([(x - 11, t + 4), (x, t - 24), (x + 11, t + 4)], fill=BAT)
        x += pitch
        k += 1
    d.rectangle([0, base, W, base + 400], fill=BAT)


def horizon(img, y, h, a=0.12):
    """울타리 뒤 달빛 받은 안개. 이게 있어야 검정 울타리가 검정 하늘에서 보인다."""
    yy = np.arange(img.shape[0], dtype=np.float32)
    band = np.exp(-(((yy - y) / h) ** 2))
    img += band[:, None, None] * np.float32([0.42, 0.43, 0.52]) * a


def tree(d, x, y, ang, length, width, depth, rng):
    """맨 나무. 가지가 갈라질수록 가늘고 짧고, 각도가 흔들린다."""
    x2 = x + np.cos(ang) * length
    y2 = y - np.sin(ang) * length
    d.line([(x, y), (x2, y2)], fill=BAT, width=max(1, int(width)))
    d.ellipse([x2 - width / 2, y2 - width / 2, x2 + width / 2, y2 + width / 2], fill=BAT)
    if depth == 0 or width < 1.2:
        return
    for k in range(2 if depth > 3 else int(rng.integers(2, 4))):
        da = rng.uniform(0.25, 0.65) * (1 if k % 2 else -1)
        tree(d, x2, y2, ang + da + rng.normal(0, 0.12), length * rng.uniform(0.62, 0.8),
             width * 0.62, depth - 1, rng)


def fog(img, y0, y1, seed, a=0.16):
    Hh, W = img.shape[:2]
    h = y1 - y0
    n = fbm(h, W, 5, seed=seed, base=3)
    n = cv2.GaussianBlur(n, (0, 0), sigmaX=W * 0.012, sigmaY=h * 0.05)
    ramp = np.clip(np.linspace(0, 1, h, dtype=np.float32) * 1.6, 0, 1)[:, None]
    img[y0:y1] += (n * ramp)[..., None] * np.float32([0.46, 0.47, 0.56]) * a


# ── 호박 ──────────────────────────────────────────────
def pumpkin(d, glow, cx, base, s):
    """몸통은 거의 검정. 눈·코·입만 불빛. glow 는 불빛 자리 마스크(L)."""
    h = s * 0.80
    top = base - h
    for dx, w, k in ((-0.40, 0.46, 0.92), (0.40, 0.46, 0.92), (-0.22, 0.60, 0.98), (0.22, 0.60, 0.98), (0, 0.66, 1.0)):
        ww = s * w
        hh2 = h * k
        d.ellipse([cx + dx * s - ww / 2, base - hh2, cx + dx * s + ww / 2, base], fill=(46, 24, 10, 255),
                  outline=(112, 58, 20, 255), width=3)
    d.rounded_rectangle([cx - s * 0.05, top - s * 0.16, cx + s * 0.05, top + s * 0.04], 6, fill=(22, 20, 16, 255))
    g = ImageDraw.Draw(glow)
    face = [
        [(cx - s * 0.30, top + h * 0.40), (cx - s * 0.13, top + h * 0.40), (cx - s * 0.20, top + h * 0.20)],
        [(cx + s * 0.30, top + h * 0.40), (cx + s * 0.13, top + h * 0.40), (cx + s * 0.20, top + h * 0.20)],
        [(cx - s * 0.05, top + h * 0.56), (cx + s * 0.05, top + h * 0.56), (cx, top + h * 0.45)],
        [(cx - s * 0.34, top + h * 0.63), (cx - s * 0.22, top + h * 0.72), (cx - s * 0.14, top + h * 0.64),
         (cx - s * 0.05, top + h * 0.74), (cx + s * 0.05, top + h * 0.64), (cx + s * 0.14, top + h * 0.74),
         (cx + s * 0.22, top + h * 0.64), (cx + s * 0.34, top + h * 0.63), (cx + s * 0.20, top + h * 0.86),
         (cx - s * 0.20, top + h * 0.86)],
    ]
    for p in face:
        g.polygon(p, fill=255)


def ember(img, glow):
    """호박불. 구멍은 밝게, 둘레는 번지게, 바닥에 불빛이 깔리게."""
    m = np.asarray(glow, np.float32) / 255.0
    core = cv2.GaussianBlur(m, (0, 0), 1.2)
    halo = cv2.GaussianBlur(m, (0, 0), 28) * 3.0
    wide = cv2.GaussianBlur(m, (0, 0), 90) * 6.0
    img[...] = img * (1 - core[..., None]) + np.float32([1.0, 0.78, 0.40]) * core[..., None]
    img += (halo + wide)[..., None] * EMBER * 0.55


def logo_img(w):
    lg = Image.open(LOGO).convert('RGBA')
    return lg.resize((w, max(1, round(lg.height * w / lg.width))), Image.LANCZOS)


def paste(pil, arr, x, y):
    pil.alpha_composite(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA'), (int(x), int(y)))


def finish(pil, glow, tag):
    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    ember(out, glow)
    bloom(out, 0.60, out.shape[1] * 0.006, 0.34)
    grain(out, 0.010)
    return out


# ══════════════════════════════════════════════════════════
#  피드 세 장
# ══════════════════════════════════════════════════════════

def feed():
    W, H = 1080, 1350
    RW = W * 3
    M = 88
    TOP = 90
    img = sky(RW, H, [(0.0, (0.034, 0.034, 0.050)), (0.40, (0.082, 0.080, 0.118)),
                      (0.78, (0.050, 0.050, 0.070)), (1.0, (0.030, 0.030, 0.040))])
    starfield(img, 40, 900, 360, seed=31)
    mcx, mcy, MR = W + W // 2, 360, 232
    godrays(img, mcx, mcy, MR, seed=5, a=0.20)
    yy, xx = np.mgrid[0:H, 0:RW].astype(np.float32)
    img += np.exp(-((xx - mcx) ** 2 + (yy - mcy) ** 2) / (2 * (MR * 1.8) ** 2))[..., None] * \
        np.float32([0.10, 0.10, 0.13])
    over(img, moonface(MR), mcx - MR, mcy - MR)
    horizon(img, H - 150, 150, 0.30)

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    # 첫 장 왼쪽 가장자리에 맨 나무. 달(둘째 장) · 호박(셋째 장) 과 무게를 맞춘다
    tree(d, 30, H - 40, np.deg2rad(84), 330, 30, 7, np.random.default_rng(3))
    # 박쥐. 달 앞은 크고 촘촘, 멀어질수록 작고 성기게. 글자 띠(620~960)는 비운다
    free = lambda x, y: not (600 < y < 990) and 60 < y < 1060
    bats(d, bat_swarm(7, mcx, mcy, 240, 110, 44, 104, seed=7, keep=free))
    bats(d, bat_swarm(20, mcx, 400, 1150, 220, 18, 48, seed=8, keep=free))

    base = H - 40
    fence(d, RW, base, 150)
    glow = Image.new('L', (RW, H), 0)
    pumpkin(d, glow, 2 * W + 790, base - 4, 190)
    pumpkin(d, glow, 2 * W + 600, base - 2, 110)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    fog(out, H - 260, H, seed=41, a=0.12)
    pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    # 머리
    fe = font(BRAND_FONT, step(-2))
    lg = logo_img(int(W * 0.17))
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, TOP + U * 2), 'BLACKOUT CREW', fe, 0.40, FAINT)
        pil.alpha_composite(lg, (x0 + W - M - lg.width, TOP + U))

    # HALLOWEEN. 아홉 칸에 한 자씩, 칸 가운데
    slot = RW / len(WORD)
    fw = font(BRAND_FONT, 40)
    for size in range(400, 60, -4):
        f = font(BRAND_FONT, size)
        if max(probe.textlength(ch, font=f) for ch in WORD) <= slot * 0.80:
            fw = f
            break
    ly = 640
    for i, ch in enumerate(WORD):
        m = silver_text(ch, fw, 0.0)
        paste(pil, m, slot * i + (slot - m.shape[1]) / 2, ly)
        lh = m.shape[0]
    d = ImageDraw.Draw(pil)

    # 글자 아래 한 줄씩
    y = ly + lh + U * 5
    f2 = font(KRB, step(3))
    d.text((M, y), '블랙아웃 할로윈 파티', font=f2, fill=INK)
    d.text((M, y + hh('블', f2) + U), 'BLACKOUT HALLOWEEN', font=font(BRAND_FONT, step(-1)), fill=DIM)
    fd = font(BRAND_FONT, step(4))
    tracked(d, (W + (W - tracked_w(DATE, fd, 0.06)) / 2, y - 6), DATE, fd, 0.06, INK)
    d.text((W + (W - probe.textlength('할로윈 당일 밤', font=font(KR, step(1)))) / 2, y + hh(DATE, fd) + U),
           '할로윈 당일 밤', font=font(KR, step(1)), fill=DIM)
    x3 = 2 * W + M
    d.text((x3, y), PERK, font=font(KRB, step(2)), fill=INK)
    d.text((x3, y + hh('분', font(KRB, step(2))) + U), TBA, font=font(KR, step(0)), fill=DIM)

    out = finish(pil, glow, 'feed')
    big = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    tiles = []
    for c in range(3):
        t = big.crop((c * W, 0, (c + 1) * W, H))
        t.save(os.path.join(OUT, f'HW{c + 1}.jpg'), quality=94)
        tiles.append(t)
        night(np.asarray(t, np.float32) / 255.0, f'HW{c + 1}')
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(os.path.join(OUT, '_할로윈격자.jpg'), quality=92)
    print('피드 완료: HW1 HW2 HW3')


# ══════════════════════════════════════════════════════════
#  스토리
# ══════════════════════════════════════════════════════════

def story():
    W, H = 1080, 1920
    M = 88
    TOP, BOT = 250, 1620                  # 위아래는 인스타 UI 가 덮는다
    img = sky(W, H, [(0.0, (0.018, 0.018, 0.028)), (0.36, (0.056, 0.054, 0.084)),
                     (0.78, (0.030, 0.030, 0.044)), (1.0, (0.014, 0.014, 0.020))])
    starfield(img, 60, 1300, 240, seed=32)
    mcx, mcy, MR = W // 2, 640, 300
    godrays(img, mcx, mcy, MR, seed=6, a=0.22)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-((xx - mcx) ** 2 + (yy - mcy) ** 2) / (2 * (MR * 1.7) ** 2))[..., None] * \
        np.float32([0.10, 0.10, 0.13])
    over(img, moonface(MR), mcx - MR, mcy - MR)
    horizon(img, H - 420, 170, 0.30)

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    free = lambda x, y: (y < 1000 or y > 1560) and y > TOP + 60
    bats(d, bat_swarm(5, mcx, mcy, 220, 180, 60, 120, seed=11, keep=free))
    bats(d, bat_swarm(12, mcx, 560, 440, 280, 18, 46, seed=12, keep=free))

    base = H - 270                        # 답장 바 위로 올린다
    fence(d, W, base, 160)
    glow = Image.new('L', (W, H), 0)
    pumpkin(d, glow, W - 230, base - 4, 220)
    pumpkin(d, glow, 210, base - 2, 120)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    fog(out, H - 540, H, seed=42, a=0.12)
    pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    fe = font(BRAND_FONT, step(-1))
    tracked(d, (M, TOP + U), 'BLACKOUT CREW', fe, 0.40, FAINT)
    lg = logo_img(int(W * 0.19))
    pil.alpha_composite(lg, (W - M - lg.width, TOP))
    d = ImageDraw.Draw(pil)

    # HALLOWEEN 한 줄, 판 폭 가득
    fw = font(BRAND_FONT, 40)
    for size in range(300, 40, -2):
        f = font(BRAND_FONT, size)
        if tracked_w(WORD, f, 0.02) <= W - M * 2:
            fw = f
            break
    y = 1000
    m = silver_text(WORD, fw, 0.02)
    paste(pil, m, (W - m.shape[1]) / 2, y)
    d = ImageDraw.Draw(pil)
    y += m.shape[0] + U * 3
    fd = font(BRAND_FONT, step(5))
    tracked(d, ((W - tracked_w(DATE, fd, 0.06)) / 2, y), DATE, fd, 0.06, INK)
    y += hh(DATE, fd) + U * 3
    f2 = font(KRB, step(3))
    d.text(((W - probe.textlength(PERK, font=f2)) / 2, y), PERK, font=f2, fill=INK)
    y += hh(PERK, f2) + U * 2
    f3 = font(KR, step(1))
    d.text(((W - probe.textlength(TBA, font=f3)) / 2, y), TBA, font=f3, fill=DIM)
    y += hh(TBA, f3)
    assert y < BOT - 60, y

    out = finish(pil, glow, 'story')
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'HW_스토리.jpg'), quality=94)
    night(out, 'HW_스토리')
    print('스토리 완료: HW_스토리')


if __name__ == '__main__':
    feed()
    story()
