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
    호박     셋째 장 무덤 사이에 둘
    묘지     울타리 앞에 묘비가 세 장을 지난다. 안개 속에 붉은 눈이 몇 쌍

## 무섭게

핏빛 달 · 글자에서 흘러내리는 피 · 묘비 · 어둠 속 눈 · 모서리 거미줄 · 맨 나무 둘.
색은 **피 빨강과 호박불** 둘. 나머지는 검정·은색.

비네트는 한 장씩이 아니라 **세 장을 붙인 판 전체**에 건다. 그래야 이음새가 안 보인다.

올리는 순서 HW3 → HW2 → HW1. 격자 새 글이 왼쪽 위.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import night, sky, vignette
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


# ── 무서운 것들 ───────────────────────────────────────
BLOOD = np.float32([0.46, 0.02, 0.035])
BLOOD_HI = np.float32([0.85, 0.16, 0.14])
EYE = np.float32([1.0, 0.10, 0.06])


def blood_moon(R):
    """핏빛 달. 은색 달 표면을 그대로 두고 색만 붉게 가라앉힌다."""
    mf = moonface(R)
    mf[..., 0] *= 0.95
    mf[..., 1] *= 0.30
    mf[..., 2] *= 0.28
    return mf


def moon_halo(img, cx, cy, R):
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dd = (xx - cx) ** 2 + (yy - cy) ** 2
    img += np.exp(-dd / (2 * (R * 1.5) ** 2))[..., None] * np.float32([0.26, 0.030, 0.035])
    img += np.exp(-dd / (2 * (R * 4.0) ** 2))[..., None] * np.float32([0.07, 0.010, 0.014])


def dripping(m, seed, n=(2, 4), max_len=160):
    """
    글자 밑에서 피가 흘러내린다. m 은 silver_text 가 준 RGBA.

    글자 아래쪽 30% 를 붉게 물들이고, 밑변에서 몇 줄기를 떨어뜨린다.
    줄기는 끝이 둥글게 맺힌다 — 막대로 끝나면 페인트다.
    """
    rng = np.random.default_rng(seed)
    h, w = m.shape[:2]
    pad = max_len + 30
    out = np.zeros((h + pad, w, 4), np.float32)
    out[:h] = m
    t = np.clip((np.arange(h, dtype=np.float32) / h - 0.62) / 0.38, 0, 1)[:, None, None]
    rgb = out[:h, :, :3]
    out[:h, :, :3] = rgb * (1 - t * 0.85) + BLOOD * t * 0.85 + BLOOD_HI * t * 0.15 * rgb.mean(-1, keepdims=True)
    a = m[..., 3]
    bottom = np.full(w, -1)
    for x in range(w):
        ys = np.where(a[:, x] > 0.6)[0]
        if len(ys):
            bottom[x] = ys.max()
    cols = [x for x in range(4, w - 4) if bottom[x] > h * 0.6]
    if not cols:
        return out
    k = int(rng.integers(n[0], n[1] + 1))
    lay = np.zeros((h + pad, w), np.float32)
    for x in rng.choice(cols, size=min(k, len(cols)), replace=False):
        y0 = int(bottom[x]) - 4
        L = int(rng.uniform(0.25, 1.0) * max_len)
        ww = rng.uniform(5, 11)
        cv2.line(lay, (int(x), y0), (int(x), y0 + L), 1.0, int(ww), cv2.LINE_AA)
        cv2.circle(lay, (int(x), y0 + L), int(ww * 0.85), 1.0, -1, cv2.LINE_AA)
        # 밑변을 따라 살짝 번진 자리
        cv2.ellipse(lay, (int(x), y0 + 2), (int(ww * 1.6), int(ww * 0.7)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 0.8)
    shade = np.clip(np.linspace(0.8, 1.15, h + pad, dtype=np.float32), 0, 1.2)[:, None, None]
    col = BLOOD * shade
    hi = cv2.GaussianBlur(np.roll(lay, -2, axis=1) - lay, (0, 0), 1.0).clip(0, 1)
    col = col + hi[..., None] * BLOOD_HI * 0.9
    na = np.maximum(out[..., 3], lay)
    mix = lay[..., None] * (1 - out[..., 3:4])
    out[..., :3] = out[..., :3] + col * mix
    out[..., 3] = na
    return out


def tomb(d, cx, base, w, h, kind, lean=0.0):
    """묘비. 둥근 머리 · 십자가 · 기운 판."""
    fill, rim = (10, 8, 10, 255), (70, 30, 32, 255)
    if kind == 0:
        pts = [(cx - w / 2, base), (cx - w / 2, base - h + w / 2)]
        pts += [(cx + np.cos(a) * w / 2, base - h + w / 2 - np.sin(a) * w / 2) for a in np.linspace(np.pi, 0, 14)]
        pts += [(cx + w / 2, base - h + w / 2), (cx + w / 2, base)]
    elif kind == 1:
        t = w * 0.26
        pts = [(cx - t / 2, base), (cx - t / 2, base - h * 0.62), (cx - w / 2, base - h * 0.62),
               (cx - w / 2, base - h * 0.62 - t), (cx - t / 2, base - h * 0.62 - t), (cx - t / 2, base - h),
               (cx + t / 2, base - h), (cx + t / 2, base - h * 0.62 - t), (cx + w / 2, base - h * 0.62 - t),
               (cx + w / 2, base - h * 0.62), (cx + t / 2, base - h * 0.62), (cx + t / 2, base)]
    else:
        pts = [(cx - w / 2, base), (cx - w / 2 + 6, base - h), (cx + w / 2 + 6, base - h + 10), (cx + w / 2, base)]
    c, s = np.cos(lean), np.sin(lean)
    pts = [(cx + (x - cx) * c - (y - base) * s, base + (x - cx) * s + (y - base) * c) for x, y in pts]
    d.polygon(pts, fill=fill, outline=rim)


def graveyard(d, W, base, seed, n, hmin, hmax, avoid=()):
    rng = np.random.default_rng(seed)
    xs = np.sort(rng.uniform(40, W - 40, n))
    for x in xs:
        if any(a0 < x < a1 for a0, a1 in avoid):
            continue
        h = rng.uniform(hmin, hmax)
        tomb(d, x, base + rng.uniform(-6, 10), h * rng.uniform(0.5, 0.7), h,
             int(rng.integers(0, 3)), rng.normal(0, 0.07))


def eyes(glow, spots):
    """어둠 속 눈. 둘씩 짝, 가로로 길게."""
    g = ImageDraw.Draw(glow)
    for x, y, s in spots:
        for dx in (-s * 1.6, s * 1.6):
            g.ellipse([x + dx - s, y - s * 0.45, x + dx + s, y + s * 0.45], fill=255)


def eye_glow(img, glow):
    m = np.asarray(glow, np.float32) / 255.0
    core = cv2.GaussianBlur(m, (0, 0), 0.8)
    halo = cv2.GaussianBlur(m, (0, 0), 10) * 4.0
    img[...] = img * (1 - core[..., None]) + np.float32([1.0, 0.55, 0.40]) * core[..., None]
    img += halo[..., None] * EYE * 0.55


def web(d, cx, cy, R, a0, a1, spokes=7, rings=7):
    """모서리 거미줄. 살은 곧게, 고리는 가운데로 처지게."""
    col = (150, 148, 156, 150)
    angs = np.linspace(a0, a1, spokes)
    for a in angs:
        d.line([(cx, cy), (cx + np.cos(a) * R, cy + np.sin(a) * R)], fill=col, width=1)
    for k in range(1, rings + 1):
        r = R * k / rings
        for a, b in zip(angs, angs[1:]):
            p0 = (cx + np.cos(a) * r, cy + np.sin(a) * r)
            p1 = (cx + np.cos(b) * r, cy + np.sin(b) * r)
            mid = (cx + np.cos((a + b) / 2) * r * 0.86, cy + np.sin((a + b) / 2) * r * 0.86)
            d.line([p0] + _bez(p0, mid, p1, 6), fill=col, width=1)


def logo_img(w):
    lg = Image.open(LOGO).convert('RGBA')
    return lg.resize((w, max(1, round(lg.height * w / lg.width))), Image.LANCZOS)


def paste(pil, arr, x, y):
    pil.alpha_composite(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA'), (int(x), int(y)))


def finish(pil, glow, eye_mask):
    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    ember(out, glow)
    eye_glow(out, eye_mask)
    bloom(out, 0.58, out.shape[1] * 0.006, 0.36)
    vignette(out, 0.42, 1.8)
    grain(out, 0.018)
    return out


def night_sky(W, H):
    img = sky(W, H, [(0.0, (0.010, 0.008, 0.012)), (0.40, (0.040, 0.014, 0.020)),
                     (0.80, (0.085, 0.022, 0.026)), (1.0, (0.020, 0.008, 0.010))])
    return img


# ══════════════════════════════════════════════════════════
#  피드 세 장
# ══════════════════════════════════════════════════════════

def feed():
    W, H = 1080, 1350
    RW = W * 3
    M = 88
    TOP = 90
    img = night_sky(RW, H)
    starfield(img, 40, 700, 180, seed=31)
    mcx, mcy, MR = W + W // 2, 360, 236
    moon_halo(img, mcx, mcy, MR)
    over(img, blood_moon(MR), mcx - MR, mcy - MR)
    horizon(img, H - 170, 170, 0.22)
    img += np.exp(-((np.arange(H, dtype=np.float32) - (H - 170)) / 170) ** 2)[:, None, None] * \
        np.float32([0.10, 0.012, 0.014])

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    web(d, 0, 0, 300, np.deg2rad(4), np.deg2rad(86))
    web(d, RW, 0, 300, np.deg2rad(94), np.deg2rad(176))
    tree(d, 30, H - 40, np.deg2rad(82), 340, 32, 7, np.random.default_rng(3))
    tree(d, RW - 30, H - 40, np.deg2rad(98), 320, 30, 7, np.random.default_rng(9))
    free = lambda x, y: not (600 < y < 1000) and 60 < y < 1040
    bats(d, bat_swarm(8, mcx, mcy, 240, 120, 44, 108, seed=7, keep=free))
    bats(d, bat_swarm(22, mcx, 400, 1150, 230, 18, 50, seed=8, keep=free))

    base = H - 40
    fence(d, RW, base - 70, 130)
    graveyard(d, RW, base, 21, 26, 70, 150, avoid=((2 * W + 470, 2 * W + 920),))
    glow = Image.new('L', (RW, H), 0)
    pumpkin(d, glow, 2 * W + 800, base - 2, 190)
    pumpkin(d, glow, 2 * W + 600, base - 2, 110)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    fog(out, H - 300, H, seed=41, a=0.20)
    pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    eye_mask = Image.new('L', (RW, H), 0)
    eyes(eye_mask, [(380, H - 130, 5), (1450, H - 115, 4), (1900, H - 150, 3.5), (2380, H - 120, 5)])

    fe = font(BRAND_FONT, step(-2))
    lg = logo_img(int(W * 0.17))
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, TOP + U * 2), 'BLACKOUT CREW', fe, 0.40, FAINT)
        pil.alpha_composite(lg, (x0 + W - M - lg.width, TOP + U))

    slot = RW / len(WORD)
    fw = font(BRAND_FONT, 40)
    for size in range(400, 60, -4):
        f = font(BRAND_FONT, size)
        if max(probe.textlength(ch, font=f) for ch in WORD) <= slot * 0.80:
            fw = f
            break
    ly = 620
    lh = 0
    for i, ch in enumerate(WORD):
        m = dripping(silver_text(ch, fw, 0.0), seed=100 + i, n=(1, 3), max_len=120)
        paste(pil, m, slot * i + (slot - m.shape[1]) / 2, ly)
        lh = max(lh, silver_text(ch, fw, 0.0).shape[0])
    d = ImageDraw.Draw(pil)

    y = ly + lh + 150
    f2 = font(KRB, step(3))
    d.text((M, y), '블랙아웃 할로윈 파티', font=f2, fill=INK)
    d.text((M, y + hh('블', f2) + U), 'BLACKOUT HALLOWEEN', font=font(BRAND_FONT, step(-1)), fill=DIM)
    fd = font(BRAND_FONT, step(4))
    tracked(d, (W + (W - tracked_w(DATE, fd, 0.06)) / 2, y - 6), DATE, fd, 0.06, INK)
    sub = '할로윈 당일 밤'
    d.text((W + (W - probe.textlength(sub, font=font(KR, step(1)))) / 2, y + hh(DATE, fd) + U),
           sub, font=font(KR, step(1)), fill=DIM)
    x3 = 2 * W + M
    d.text((x3, y), PERK, font=font(KRB, step(2)), fill=INK)
    d.text((x3, y + hh('분', font(KRB, step(2))) + U), TBA, font=font(KR, step(0)), fill=DIM)

    out = finish(pil, glow, eye_mask)
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
    TOP, BOT = 250, 1620
    img = night_sky(W, H)
    starfield(img, 60, 900, 140, seed=32)
    mcx, mcy, MR = W // 2, 640, 300
    moon_halo(img, mcx, mcy, MR)
    over(img, blood_moon(MR), mcx - MR, mcy - MR)
    horizon(img, H - 440, 170, 0.22)
    img += np.exp(-((np.arange(H, dtype=np.float32) - (H - 440)) / 200) ** 2)[:, None, None] * \
        np.float32([0.10, 0.012, 0.014])

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    web(d, 0, 0, 230, np.deg2rad(4), np.deg2rad(86))
    web(d, W, 0, 230, np.deg2rad(94), np.deg2rad(176))
    free = lambda x, y: (y < 980 or y > 1560) and y > TOP + 60
    bats(d, bat_swarm(6, mcx, mcy, 220, 180, 60, 124, seed=11, keep=free))
    bats(d, bat_swarm(12, mcx, 560, 440, 280, 18, 46, seed=12, keep=free))

    base = H - 270
    fence(d, W, base - 40, 110)
    graveyard(d, W, base, 23, 10, 80, 160, avoid=((W - 380, W - 80), (120, 320)))
    glow = Image.new('L', (W, H), 0)
    pumpkin(d, glow, W - 230, base - 2, 220)
    pumpkin(d, glow, 220, base - 2, 120)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    fog(out, H - 560, H, seed=42, a=0.20)
    pil = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    eye_mask = Image.new('L', (W, H), 0)
    eyes(eye_mask, [(470, base - 60, 5), (640, base - 40, 4)])

    fe = font(BRAND_FONT, step(-1))
    tracked(d, (M, TOP + U), 'BLACKOUT CREW', fe, 0.40, FAINT)
    lg = logo_img(int(W * 0.19))
    pil.alpha_composite(lg, (W - M - lg.width, TOP))
    d = ImageDraw.Draw(pil)

    fw = font(BRAND_FONT, 40)
    for size in range(300, 40, -2):
        f = font(BRAND_FONT, size)
        if tracked_w(WORD, f, 0.02) <= W - M * 2:
            fw = f
            break
    y = 960
    m0 = silver_text(WORD, fw, 0.02)
    m = dripping(m0, seed=7, n=(5, 7), max_len=110)
    paste(pil, m, (W - m.shape[1]) / 2, y)
    d = ImageDraw.Draw(pil)
    y += m0.shape[0] + 110
    fd = font(BRAND_FONT, step(5))
    tracked(d, ((W - tracked_w(DATE, fd, 0.06)) / 2, y), DATE, fd, 0.06, INK)
    y += hh(DATE, fd) + U * 3
    f2 = font(KRB, step(3))
    d.text(((W - probe.textlength(PERK, font=f2)) / 2, y), PERK, font=f2, fill=INK)
    y += hh(PERK, f2) + U * 2
    f3 = font(KR, step(1))
    d.text(((W - probe.textlength(TBA, font=f3)) / 2, y), TBA, font=f3, fill=DIM)
    y += hh(TBA, f3)
    assert y < BOT - 40, y

    out = finish(pil, glow, eye_mask)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'HW_스토리.jpg'), quality=94)
    night(out, 'HW_스토리')
    print('스토리 완료: HW_스토리')


if __name__ == '__main__':
    feed()
    story()
