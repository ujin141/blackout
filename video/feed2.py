"""
인스타 피드 그리드 두 번째 세트 (4·5번).
첫 세트(feed.py)와 이어 보이게 만든다 — 가로선 높이(y=1058)와 바닥 그라데이션을
그대로 맞추고, 엠블럼을 두 장의 이음새에 정확히 걸쳐 놓는다.
python feed2.py  →  out/feed/feed_4.png, feed_5.png (+ feed2_full.png)
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KRB               # OS별 한글 폰트 (video/fonts.py)

TW, TH = 1080, 1350                 # 게시물 한 장
W, H = TW * 2, TH                   # 두 장을 이어붙인 전체
SAFE_T, SAFE_B = 135, 1215          # 그리드에서 잘리지 않는 구간
RULE_Y = 1058                       # ← 첫 세트와 같은 높이. 건드리면 안 이어진다.
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

# 첫 세트에서 이어지는 리듬으로 빛을 놓는다 (바깥쪽을 살려 각 장이 비지 않게)
for x, sp, an, al in [(120, 150, 0.16, 0.12), (400, 100, -0.06, 0.075),
                      (700, 120, 0.10, 0.085), (1080, 160, 0.0, 0.11),
                      (1460, 120, 0.12, 0.085), (1760, 100, -0.08, 0.075),
                      (2040, 150, -0.18, 0.12)]:
    beam(img, x, sp, an, al)
haze(img, W * 0.5, H * 0.40, W * 0.34, 0.10)
haze(img, W * 0.13, H * 0.42, W * 0.17, 0.055)
haze(img, W * 0.87, H * 0.42, W * 0.17, 0.055)

# 바닥 — 첫 세트와 같은 값
g = np.zeros((H, 1), np.float32)
g[int(H * 0.66):, 0] = np.linspace(0, 1, H - int(H * 0.66)) ** 1.7
img += g[..., None] * 0.05

# ── 이음새 규칙 ────────────────────────────────────────────
# 인스타 그리드는 타일 사이에 간격이 있다. 경계에 걸치는 건 그만큼 잘리고,
# 썸네일로 줄면 가는 획은 아예 안 보인다.
# 그래서 경계에 놓는 건 엠블럼 하나로 제한하고, 대신 획이 두꺼워 보이도록
# 아주 크게 쓴다. 글자는 절대 경계에 걸치지 않는다.
LOGO_H = 860                        # 이보다 작으면 가운데 번개가 썸네일에서 사라진다
SEAM_CLEAR = 90                     # 글자를 놓지 않는 경계 좌우 폭

# 엠블럼 — 이음새 정중앙. 절반씩 두 장에 걸린다.
logo(img, 'logo-mark.png', LOGO_H, W / 2, 620, glow=0.45, glow_r=60)

# 두 장을 관통하는 가로선 — 첫 세트와 같은 y

# 상단 — 각 장 안에서 끝난다
m = tmask('NIGHT', BRAND, 26, 0.34)
blit(img, m, TW * 0.5, 175, 0.45)
m = tmask('UNDERGROUND', BRAND, 26, 0.28)
blit(img, m, TW * 1.5, 175, 0.45)

# 가로선 아래 — 각 장 안에서 끝난다
m = tmask('MUSIC · CONTENT · COMMUNITY', BRAND, 25, 0.2)
blit(img, m, TW * 0.5, 1135, 0.62)
m = tmask('SEOUL · SINCE 2026', BRAND, 25, 0.24)
blit(img, m, TW * 1.5, 1135, 0.62)

# 두 장을 바깥에서 감싸는 세로 마커 — 한 쌍이라는 신호
for x in (150, W - 150):
    img[300:520, x:x + 2] += 0.22
    img[560:640, x:x + 2] += 0.10

# 비네팅 + 그레인
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / (W * 0.64)) ** 2 + ((yy - H / 2) / (H * 0.9)) ** 2)
img *= np.clip(1.1 - d ** 2.0, 0, 1)[..., None]
img += np.random.default_rng(8).standard_normal((H, W, 1)).astype(np.float32) * 0.016
# 가로선은 비네팅 뒤에 그린다 — 앞에 그리면 양 끝이 어두워져 옆 칸과 안 이어진다.
img[1058:1060, 0:W] += 0.30
img[1059:1060, int(W * 0.30):int(W * 0.70)] += 0.18
img = np.clip(img, 0, 1)

full = Image.fromarray((img * 255).astype(np.uint8))
full.save(os.path.join(OUT, 'feed2_full.png'), optimize=True)
for i in range(2):
    full.crop((i * TW, 0, (i + 1) * TW, TH)).save(
        os.path.join(OUT, f'feed_{i + 4}.png'), optimize=True)
print('->', OUT)
