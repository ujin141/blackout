"""
카카오톡 채팅방 배경 (1440x3120).

말풍선과 글씨가 위에 얹히므로 대비를 낮게 간다.
로고는 워터마크 수준으로만 넣고, 가운데(대화가 쌓이는 구간)는 비워 둔다.
python kakao_bg.py  →  out/kakao/kakao_bg_1.png, kakao_bg_2.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')

W, H = 1440, 3120                 # 요즘 폰 비율(9:19.5)에 맞춘 넉넉한 크기
TOP_UI = 320                      # 상단 방 이름 · 뒤로가기가 덮는 구간
BOT_UI = 420                      # 하단 입력창이 덮는 구간
OUT = os.path.join(HERE, 'out', 'kakao')
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


def logo_alpha(name, height):
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    return np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3] / 255.0


def beam(dst, x, spread, angle, a):
    layer = np.zeros((H // 2, W // 2), np.float32)
    L = H
    pts = np.array([[x / 2, -60],
                    [x / 2 - spread / 2 + np.sin(angle) * L, L],
                    [x / 2 + spread / 2 + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= (np.linspace(1, 0, H // 2, dtype=np.float32) ** 1.5)[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 34)
    dst += cv2.resize(layer, (W, H))[..., None] * a


def haze(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H:5, 0:W:5].astype(np.float32)
    g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r, 0, 1) ** 2.3
    dst += cv2.resize(g, (W, H))[..., None] * a


def base():
    """공통 바탕 — 아주 어둡게"""
    img = np.zeros((H, W, 3), np.float32)
    for x, sp, an, al in [(260, 190, 0.14, 0.030), (720, 150, -0.04, 0.026),
                          (1180, 180, -0.16, 0.030)]:
        beam(img, x, sp, an, al)
    haze(img, W * 0.5, H * 0.26, W * 0.85, 0.022)
    # 바닥 은은한 광
    g = np.zeros((H, 1), np.float32)
    g[int(H * 0.70):, 0] = np.linspace(0, 1, H - int(H * 0.70)) ** 2.0
    img += g[..., None] * 0.030
    return img


def finish(img, seed=3):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.80)) ** 2 + ((yy - H / 2) / (H * 0.80)) ** 2)
    img *= np.clip(1.08 - d ** 2.1, 0, 1)[..., None]
    img += np.random.default_rng(seed).standard_normal((H, W, 1)).astype(np.float32) * 0.011
    return np.clip(img, 0, 1)


# ── 1) 가운데 엠블럼 워터마크 ──────────────────────────────
img = base()
mk = logo_alpha('logo-mark.png', 980)
blit(img, mk, W / 2, H * 0.42, 0.085, glow=0.05, glow_r=70)     # 아주 흐리게
m = tmask('BLACKOUT CREW', BRAND, 40, 0.34)
blit(img, m, W / 2, TOP_UI + 90, 0.16)
m = tmask('WHERE THE LIGHTS FADE,  THE MUSIC TAKES OVER.', BRAND, 21, 0.2)
blit(img, m, W / 2, H - BOT_UI - 70, 0.11)
Image.fromarray((finish(img) * 255).astype(np.uint8)).save(
    os.path.join(OUT, 'kakao_bg_1.png'), optimize=True)

# ── 2) 위쪽에 로고, 아래는 비움 ────────────────────────────
img = base()
lock = logo_alpha('logo-lockup.png', 640)
blit(img, lock, W / 2, TOP_UI + 330, 0.20, glow=0.10, glow_r=60)
m = tmask('SEOUL · DJ CREW · EST. 2026', BRAND, 24, 0.3)
blit(img, m, W / 2, TOP_UI + 700, 0.13)
# 하단에 가로선 하나만
img[H - BOT_UI - 130:H - BOT_UI - 128, 260:W - 260] += 0.05
Image.fromarray((finish(img, 7) * 255).astype(np.uint8)).save(
    os.path.join(OUT, 'kakao_bg_2.png'), optimize=True)

print('->', OUT)
