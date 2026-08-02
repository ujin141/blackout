"""
인스타 스토리용 포스터 — 풀파티 × 솔로파티 (1080x1920).

물결(코스틱) 무늬를 코드로 그려 풀파티 느낌을 내되, 브랜드 톤대로 흑백만 쓴다.
날짜·장소·시간은 아래 상수만 고치면 된다.
python poster_pool.py  →  out/poster/pool_solo.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KR, KRB           # OS별 한글 폰트

# ── 여기만 고치면 됨 ───────────────────────────────────────
DATE_EN = 'COMING SOON'             # 예: 'SAT 08.23'
DATE_KR = '일정 공개 예정'            # 예: '8월 23일 토요일'
TIME_KR = '시간 추후 공지'            # 예: '오후 2시 — 밤 10시'
VENUE   = 'VENUE TBA'               # 예: 'SEOUL · 강남'
NOTE_KR = '예약 · 문의는 DM'
LINEUP  = ['V', 'LYNN', 'AROS', 'TS']
# ──────────────────────────────────────────────────────────

W, H = 1080, 1920
SAFE_T, SAFE_B = 260, 1660          # 스토리 UI가 덮는 위·아래
OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)


def tmask(text, path, size, track_em=0.0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 90, asc + desc + 70), 0)
    d = ImageDraw.Draw(im)
    x = 45
    for c, wc in zip(text, ws):
        d.text((x, 35), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    lo, hi = 8, 400
    for _ in range(22):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def blit(dst, m, cx, cy, a=1.0, glow=0.0, glow_r=24):
    m = m.astype(np.float32)
    if m.max() > 1.5:
        m /= 255.0
    layers = [(m, 1.0)]
    if glow > 0:
        pad = int(glow_r * 1.6) + 4
        mp = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        layers.insert(0, (cv2.GaussianBlur(mp, (0, 0), glow_r * 0.55), glow))
    for lm, la in layers:
        h, w = lm.shape
        x0, y0 = int(cx - w / 2), int(cy - h / 2)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        dst[sy0:sy1, sx0:sx1] += lm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * (a * la)


def logo_alpha(name, height):
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    return np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3] / 255.0


def caustics(seed=0):
    """수면에 생기는 물결 무늬 — 얇은 흰 선"""
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    x, y = xx * 0.012, yy * 0.012
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37)) +
         0.8 * np.sin((x + y) * 0.85 + 0.9 * np.sin(x * 0.21)))
    lines = np.clip(1 - np.abs(np.sin(f * 1.7)) * 7.5, 0, 1) ** 1.4
    lines = cv2.GaussianBlur(lines, (0, 0), 1.3)
    return cv2.resize(lines, (W, H), interpolation=cv2.INTER_LINEAR)


def beam(dst, x, spread, angle, a):
    layer = np.zeros((H // 2, W // 2), np.float32)
    L = H
    pts = np.array([[x / 2, -40],
                    [x / 2 - spread / 2 + np.sin(angle) * L, L],
                    [x / 2 + spread / 2 + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= (np.linspace(1, 0, H // 2, dtype=np.float32) ** 1.4)[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 26)
    dst += cv2.resize(layer, (W, H))[..., None] * a


def rule(dst, y, x0, x1, a, th=2):
    dst[y:y + th, int(x0):int(x1)] += a


# ── 조립 ───────────────────────────────────────────────────
img = np.zeros((H, W, 3), np.float32)

# 조명
for x, sp, an, al in [(210, 150, 0.15, 0.075), (560, 120, -0.05, 0.065), (900, 150, -0.16, 0.075)]:
    beam(img, x, sp, an, al)

# 물결 — 아래로 갈수록 진하게 (수면)
c = caustics()
grad = np.clip((np.arange(H, dtype=np.float32) - H * 0.26) / (H * 0.74), 0, 1) ** 1.3
img += (c * grad[:, None])[..., None] * 0.40

# 수면 경계선
rule(img, int(H * 0.262), 0, W, 0.13, 1)

# ── 상단 ──────────────────────────────────────────────────
mk = logo_alpha('logo-mark.png', 108)
blit(img, mk, W / 2, SAFE_T + 60, 0.95, glow=0.3, glow_r=22)
m = tmask('BLACKOUT CREW PRESENTS', BRAND, 21, 0.32)
blit(img, m, W / 2, SAFE_T + 160, 0.55)

# ── 타이틀 ────────────────────────────────────────────────
s = fit('POOL PARTY', BRAND, 880, 0.06)
m = tmask('POOL PARTY', BRAND, s, 0.06)
blit(img, m, W / 2, 640, 1.0, glow=0.4, glow_r=30)

s = fit('×', BRAND, 120)
m = tmask('×', BRAND, s)
blit(img, m, W / 2, 790, 0.9, glow=0.45, glow_r=34)

s = fit('SOLO PARTY', BRAND, 880, 0.06)
m = tmask('SOLO PARTY', BRAND, s, 0.06)
blit(img, m, W / 2, 940, 1.0, glow=0.4, glow_r=30)

m = tmask('풀파티 × 솔로파티', KRB, 44)
blit(img, m, W / 2, 1050, 0.72, glow=0.22, glow_r=16)

rule(img, 1130, 300, W - 300, 0.30)

# ── 라인업 ────────────────────────────────────────────────
m = tmask('LINE UP', BRAND, 20, 0.36)
blit(img, m, W / 2, 1200, 0.5)
m = tmask('  ·  '.join(LINEUP), BRAND, 46, 0.12)
blit(img, m, W / 2, 1280, 0.95, glow=0.3, glow_r=20)

# ── 정보 ──────────────────────────────────────────────────
m = tmask(DATE_EN, BRAND, 54, 0.16)
blit(img, m, W / 2, 1420, 1.0, glow=0.32, glow_r=22)
m = tmask(DATE_KR, KRB, 34)
blit(img, m, W / 2, 1490, 0.7)
m = tmask(TIME_KR, KR, 28)
blit(img, m, W / 2, 1540, 0.5)
m = tmask(VENUE, BRAND, 26, 0.28)
blit(img, m, W / 2, 1595, 0.6)

# ── 하단 ──────────────────────────────────────────────────
m = tmask('@BLACKOUTCREW_OFFICIAL', BRAND, 24, 0.16)
blit(img, m, W / 2, SAFE_B + 30, 0.85, glow=0.25, glow_r=14)
m = tmask(NOTE_KR, KR, 26)
blit(img, m, W / 2, SAFE_B + 85, 0.5)

# ── 마감 ──────────────────────────────────────────────────
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.80)) ** 2)
img *= np.clip(1.1 - d ** 2.0, 0, 1)[..., None]
img += np.random.default_rng(11).standard_normal((H, W, 1)).astype(np.float32) * 0.015
img = np.clip(img, 0, 1)

p = os.path.join(OUT, 'pool_solo.png')
Image.fromarray((img * 255).astype(np.uint8)).save(p, optimize=True)
print('->', p)
