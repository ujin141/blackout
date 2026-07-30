"""
카카오톡·인스타·트위터 링크 미리보기용 카드 이미지 (1200x630).
python make_og.py  →  assets/img/og-image.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')

W, H = 1200, 630


def beam(dst, x, spread, angle, a):
    layer = np.zeros((H, W), np.float32)
    L = H * 1.6
    pts = np.array([[x, -40],
                    [x - spread + np.sin(angle) * L, L],
                    [x + spread + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= np.linspace(1.0, 0.0, H, dtype=np.float32)[:, None] ** 1.4
    layer = cv2.GaussianBlur(layer, (0, 0), 26)
    dst += layer[..., None] * a


def haze(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
    dst += (np.clip(1 - d, 0, 1) ** 2.2)[..., None] * a


def paste_alpha(dst, path, height, cx, cy, glow=0.0):
    im = Image.open(path).convert('RGBA')
    w = int(im.width * height / im.height)
    im = im.resize((w, height), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)[..., 3] / 255.0
    layers = [(a, 1.0)]
    if glow:
        pad = 90                       # 글로우가 사각형으로 잘리지 않게 여백 확보
        ap = cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        layers.insert(0, (cv2.GaussianBlur(ap, (0, 0), 26), glow))
    for m, la in layers:
        h, w2 = m.shape
        x0, y0 = int(cx - w2 / 2), int(cy - h / 2)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x0 + w2), min(H, y0 + h)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        dst[sy0:sy1, sx0:sx1] += m[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * la


def text(dst, s, size, cx, cy, track, a=1.0):
    f = ImageFont.truetype(BRAND, size)
    tr = int(size * track)
    widths = [f.getlength(c) for c in s]
    total = int(sum(widths) + tr * (len(s) - 1))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 40, asc + desc + 20), 0)
    d = ImageDraw.Draw(im)
    x = 20
    for c, wc in zip(s, widths):
        d.text((x, 10), c, font=f, fill=255)
        x += wc + tr
    m = np.asarray(im).astype(np.float32) / 255.0
    h, w2 = m.shape
    x0, y0 = int(cx - w2 / 2), int(cy - h / 2)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w2), min(H, y0 + h)
    dst[sy0:sy1, sx0:sx1] += m[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * a


img = np.zeros((H, W, 3), np.float32)
for i, (x, sp, an, al) in enumerate([(210, 46, 0.18, 0.16), (470, 34, -0.1, 0.12),
                                     (760, 40, 0.12, 0.13), (1010, 30, -0.16, 0.10)]):
    beam(img, x, sp, an, al)
haze(img, W * 0.5, H * 0.42, W * 0.5, 0.10)

paste_alpha(img, os.path.join(IMG, 'logo-mark.png'), 300, W / 2, 245, glow=0.45)
paste_alpha(img, os.path.join(IMG, 'logo-word.png'), 58, W / 2, 452, glow=0.3)
text(img, 'WHERE THE LIGHTS FADE, THE MUSIC TAKES OVER.', 17, W / 2, 528, 0.22, 0.72)
text(img, 'SEOUL  ·  DJ CREW', 14, W / 2, 572, 0.34, 0.42)

# 비네팅 + 그레인
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2)
img *= np.clip(1.14 - d ** 1.9, 0, 1)[..., None]
rng = np.random.default_rng(5)
img += rng.standard_normal((H, W, 1)).astype(np.float32) * 0.016

out = os.path.join(IMG, 'og-image.png')
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out, optimize=True)
print(out, Image.open(out).size, f'{os.path.getsize(out)/1024:.0f} KB')
