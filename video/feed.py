"""
인스타 피드 그리드용 3분할 세트.
가로로 이어지는 한 장(3240x1350)을 만들고 1080x1350 세 장으로 자른다.
프로필 그리드는 정사각으로 잘리므로 핵심 요소는 세로 135~1215 안에 둔다.
python feed.py  →  out/feed/feed_1.png ~ feed_3.png (+ feed_full.png)
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
KRB = 'C:/Windows/Fonts/malgunbd.ttf'

TW, TH = 1080, 1350          # 게시물 한 장
W, H = TW * 3, TH            # 이어붙인 전체
SAFE_T, SAFE_B = 135, 1215   # 그리드에서 잘리지 않는 구간
OUT = os.path.join(HERE, 'out', 'feed')
os.makedirs(OUT, exist_ok=True)


def tmask(text, path, size, track_em=0.0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 80, asc + desc + 60), 0)
    d = ImageDraw.Draw(im)
    x = 40
    for c, wc in zip(text, ws):
        d.text((x, 30), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


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


def logo(dst, name, height, cx, cy, glow=0.4, glow_r=40):
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    a = np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3] / 255.0
    blit(dst, a, cx, cy, 1.0, glow=glow, glow_r=glow_r)


def beam(dst, x, spread, angle, a):
    layer = np.zeros((H // 2, W // 2), np.float32)
    L = H
    pts = np.array([[x / 2, -40],
                    [x / 2 - spread / 2 + np.sin(angle) * L, L],
                    [x / 2 + spread / 2 + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= (np.linspace(1, 0, H // 2, dtype=np.float32) ** 1.35)[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 26)
    dst += cv2.resize(layer, (W, H))[..., None] * a


def haze(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r, 0, 1) ** 2.2
    dst += cv2.resize(g, (W, H))[..., None] * a


# ── 조립 ───────────────────────────────────────────────────
img = np.zeros((H, W, 3), np.float32)
rng = np.random.default_rng(4)

# 세 칸을 가로지르는 빛
for x, sp, an, al in [(430, 150, 0.16, 0.10), (900, 110, -0.08, 0.085),
                      (1400, 130, 0.10, 0.10), (1620, 90, 0.0, 0.075),
                      (1900, 120, -0.12, 0.10), (2380, 140, 0.08, 0.09),
                      (2820, 120, -0.16, 0.085)]:
    beam(img, x, sp, an, al)
haze(img, W * 0.5, H * 0.42, W * 0.30, 0.10)
haze(img, W * 0.16, H * 0.55, W * 0.16, 0.035)
haze(img, W * 0.84, H * 0.55, W * 0.16, 0.035)

# 바닥
g = np.zeros((H, 1), np.float32)
g[int(H * 0.66):, 0] = np.linspace(0, 1, H - int(H * 0.66)) ** 1.7
img += g[..., None] * 0.05

# 가운데: 로고
logo(img, 'logo-mark.png', 560, W / 2, 560, glow=0.5, glow_r=52)
logo(img, 'logo-word.png', 78, W / 2, 940, glow=0.35, glow_r=26)

# 세 칸을 관통하는 가로선 (그리드에서 이어져 보이는 핵심)
img[1058:1060, 120:W - 120] += 0.30
img[1059:1060, int(W * 0.28):int(W * 0.72)] += 0.25

# 슬로건 — 가운데 칸을 넘어 좌우로 걸침
m = tmask('WHERE THE LIGHTS FADE,   THE MUSIC TAKES OVER.', BRAND, 30, 0.24)
blit(img, m, W / 2, 1130, 0.62, glow=0.25, glow_r=16)

# 왼쪽 칸
for i, txt in enumerate(['HOUSE', 'TECHNO', 'MINIMAL']):
    m = tmask(txt, BRAND, 40, 0.3)
    blit(img, m, TW * 0.5, 560 + i * 84, 0.75, glow=0.25, glow_r=16)
m = tmask('SEOUL · DJ CREW', BRAND, 22, 0.34)
blit(img, m, TW * 0.5, 940, 0.45)

# 오른쪽 칸
m = tmask('창립 멤버 모집 중', KRB, 54)
blit(img, m, TW * 2.5, 560, 0.95, glow=0.35, glow_r=24)
for i, txt in enumerate(['DJ · PRODUCER', 'VISUAL · PHOTO', 'VIDEO · CONTENT']):
    m = tmask(txt, BRAND, 24, 0.24)
    blit(img, m, TW * 2.5, 660 + i * 52, 0.5)
m = tmask('@blackoutcrew_official', BRAND, 26, 0.12)
blit(img, m, TW * 2.5, 940, 0.8, glow=0.25, glow_r=14)

# 비네팅 + 그레인
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.9)) ** 2)
img *= np.clip(1.1 - d ** 2.0, 0, 1)[..., None]
img += np.random.default_rng(8).standard_normal((H, W, 1)).astype(np.float32) * 0.016
img = np.clip(img, 0, 1)

full = Image.fromarray((img * 255).astype(np.uint8))
full.save(os.path.join(OUT, 'feed_full.png'), optimize=True)
for i in range(3):
    full.crop((i * TW, 0, (i + 1) * TW, TH)).save(
        os.path.join(OUT, f'feed_{i + 1}.png'), optimize=True)
print('->', OUT)
