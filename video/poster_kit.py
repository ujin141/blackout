"""
포스터 공통 도구.

`poster_split.py`(A안)·`poster_club.py`(B안)는 각자 이 함수들을 복사해 갖고 있습니다.
그때는 두 개뿐이라 괜찮았는데 시안이 다섯으로 늘면서 한 곳만 고쳐도 나머지가
어긋나기 시작해 따로 뺐습니다. C·D·E안은 전부 여기서 가져다 씁니다.

A·B안은 이미 각자 값이 미세하게 조정돼 있어서 건드리지 않았습니다.
새 시안을 만들 때만 이 파일을 쓰세요.
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
STOCK = os.path.join(IMG, 'stock')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

WHITE = np.array([1.0, 1.0, 1.0], np.float32)
BLACK = np.array([0.0, 0.0, 0.0], np.float32)

# 두 사진 모두 CC0. club 은 아래쪽에 관객 얼굴이 다 나오므로
# 얼굴이 없는 위 34%(디스코볼·연기·트러스)만 쓴다 — CLUB_SAFE 를 그대로 쓸 것.
POOL = os.path.join(STOCK, 'pool-cc0.jpg')
CLUB = os.path.join(STOCK, 'club-cc0.jpg')
CLUB_SAFE = dict(focus=0.16, zoom=2.9)      # 값은 올리기만. 낮추면 얼굴이 딸려 들어온다.


def tmask(text, path, size, track_em=0.0):
    """글자를 알파 마스크로. 자간은 em 비율."""
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 140, asc + desc + 120), 0)
    d = ImageDraw.Draw(im)
    x = 70
    for c, wc in zip(text, ws):
        d.text((x, 60), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    """target_w 에 딱 맞는 글자 크기를 이분탐색으로 찾는다."""
    lo, hi = 8, 560
    for _ in range(20):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def paint(dst, m, x, y, color=WHITE, a=1.0, anchor='l', valign='c'):
    """anchor l/r/c · valign t/c. 좌표는 기준점이지 좌상단이 아니다."""
    H, W = dst.shape[:2]
    m = m.astype(np.float32) / 255.0
    h, w = m.shape
    x0 = int(x) if anchor == 'l' else (int(x - w) if anchor == 'r' else int(x - w / 2))
    y0 = int(y) if valign == 't' else int(y - h / 2)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = m[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * a
    dst[sy0:sy1, sx0:sx1] = dst[sy0:sy1, sx0:sx1] * (1 - sub) + color * sub


def add(dst, layer, x0, y0, color, a):
    """빛은 덮지 말고 더한다. 덮으면 배경이 죽는다."""
    H, W = dst.shape[:2]
    h, w = layer.shape
    x0, y0 = int(x0), int(y0)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst[sy0:sy1, sx0:sx1] += layer[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * color * a


def glow(dst, m, x, y, color, a, r, anchor='l', valign='c'):
    """네온 후광. 그림자와 정반대 — 어둡게 까는 게 아니라 빛을 더한다."""
    pad = int(r * 2.4) + 8
    mp = cv2.copyMakeBorder(m.astype(np.float32) / 255.0, pad, pad, pad, pad,
                            cv2.BORDER_CONSTANT, value=0)
    g = cv2.GaussianBlur(mp, (0, 0), r)
    g /= max(g.max(), 1e-6)
    h, w = g.shape
    x0 = x - pad if anchor == 'l' else (x - w + pad if anchor == 'r' else x - w / 2)
    y0 = y - pad if valign == 't' else y - h / 2
    add(dst, g, x0, y0, color, a)


def outline(m, th):
    """속을 비운 테두리만 남긴다. 네온 튜브용."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (th * 2 + 1, th * 2 + 1))
    return np.clip(cv2.dilate(m, k).astype(np.int16) - m.astype(np.int16), 0, 255).astype(np.uint8)


def rule(dst, y, x0, x1, color, a, th=1):
    y, th = int(y), max(1, int(th))
    dst[y:y + th, int(x0):int(x1)] = dst[y:y + th, int(x0):int(x1)] * (1 - a) + color * a


def vrule(dst, x, y0, y1, color, a, th=1):
    x, th = int(x), max(1, int(th))
    dst[int(y0):int(y1), x:x + th] = dst[int(y0):int(y1), x:x + th] * (1 - a) + color * a


def box(dst, x0, y0, x1, y1, color, a=1.0):
    dst[int(y0):int(y1), int(x0):int(x1)] = \
        dst[int(y0):int(y1), int(x0):int(x1)] * (1 - a) + color * a


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5, zoom=1.0):
    """명암만 남기고 두 색 사이로 다시 칠한다.
    색조(HSV)를 돌리면 원본 색이 남아 엉뚱한 색이 튄다 — 반드시 이걸 쓸 것.
    zoom 을 올리면 더 확대해 잘라낸다. 사진의 일부만 쓰고 싶을 때."""
    im = Image.open(path).convert('RGB')
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0 = max(0, (im.width - W) // 2)
    y0 = int(max(0, min(im.height - H, im.height * focus - H * 0.5)))
    a = np.asarray(im.crop((x0, y0, x0 + W, y0 + H))).astype(np.float32) / 255.0
    lum = a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
    lum = np.clip((lum - 0.5) * contrast + 0.5, 0, 1) ** 0.92
    duo = shadow + (light - shadow) * lum[..., None]
    return np.ascontiguousarray(np.clip(duo * (1 - keep) + a * keep, 0, 1))


def bloom(img, thr, sigma, amt, tint=WHITE):
    """밝은 곳을 번지게. 조명이 번져야 클럽처럼 보인다."""
    lum = img[..., 0] * .299 + img[..., 1] * .587 + img[..., 2] * .114
    g = cv2.GaussianBlur(np.clip(lum - thr, 0, 1) / max(1 - thr, 1e-3), (0, 0), sigma)
    img += g[..., None] * tint * amt


def logo(height):
    im = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    return np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3]


def grain(img, amt, seed=3):
    img += np.random.default_rng(seed).standard_normal(img.shape[:2] + (1,)).astype(np.float32) * amt


def save(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)
    return p


SIZES = {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}
