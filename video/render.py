"""
BLACKOUT — 숏폼 티저 렌더러 (1080x1920 / 30fps)
타이포 + 모션그래픽만. 사람 사진 없음.
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, 'assets', 'img')

W, H = 1080, 1920
FPS = 30
BPM = 128.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
DUR = BAR * 15
NF = int(round(DUR * FPS))

BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KR, KRB          # OS별 한글 폰트 (video/fonts.py)

# 숏폼 UI 세이프존
SAFE_TOP, SAFE_BOT = 300, 1560


def T(bar, beat=0.0):
    return (bar - 1) * BAR + beat * BEAT


# ── 이징 ───────────────────────────────────────────────────
def clamp01(x):
    return max(0.0, min(1.0, x))


def out_expo(x):
    x = clamp01(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def out_cubic(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def in_cubic(x):
    x = clamp01(x)
    return x ** 3


def out_back(x, s=1.7):
    x = clamp01(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def pulse(x, k=6.0):
    """0→1→0"""
    x = clamp01(x)
    return (np.sin(np.pi * x) ** k) if k != 1 else np.sin(np.pi * x)


# ── 텍스트 마스크 ──────────────────────────────────────────
_font_cache = {}
_mask_cache = {}


def font(path, size):
    k = (path, size)
    if k not in _font_cache:
        _font_cache[k] = ImageFont.truetype(path, size)
    return _font_cache[k]


def _draw_tracked(text, f, tracking):
    """자간 적용해 타이트한 마스크(uint8) 생성"""
    pad = 40
    widths = []
    for ch in text:
        widths.append(f.getlength(ch))
    total = sum(widths) + tracking * max(len(text) - 1, 0)
    asc, desc = f.getmetrics()
    im = Image.new('L', (int(total) + pad * 2, asc + desc + pad * 2), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for ch, wch in zip(text, widths):
        d.text((x, pad), ch, font=f, fill=255)
        x += wch + tracking
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    if len(xs) == 0:
        return np.zeros((1, 1), np.uint8)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def text_mask(text, path, target_w=None, size=None, track_em=0.08):
    """target_w(px)에 맞춰 크기를 자동으로 찾음"""
    key = (text, path, target_w, size, round(track_em, 4))
    if key in _mask_cache:
        return _mask_cache[key]
    if size is None:
        lo, hi = 8, 460
        for _ in range(22):
            mid = (lo + hi) / 2
            f = font(path, int(mid))
            m = _draw_tracked(text, f, int(mid * track_em))
            if m.shape[1] > target_w:
                hi = mid
            else:
                lo = mid
        size = int(lo)
    f = font(path, int(size))
    m = _draw_tracked(text, f, int(size * track_em))
    _mask_cache[key] = m
    return m


# ── 이미지 소스 ────────────────────────────────────────────
def load_alpha(name, height=None):
    im = Image.open(os.path.join(ASSETS, name)).convert('RGBA')
    if height:
        w = max(1, int(im.width * height / im.height))
        im = im.resize((w, height), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255.0
    return a[..., 3], a[..., :3]


MARK_A, _ = load_alpha('logo-mark.png', 900)
WORD_A, _ = load_alpha('logo-word.png', 150)


# ── 합성 ───────────────────────────────────────────────────
def blit(dst, mask, cx, cy, alpha=1.0, glow=0.0, glow_r=25, color=(1, 1, 1),
         scale=1.0, rot=0.0, blur=0.0):
    """mask(uint8/float) 를 화면 중심좌표(cx,cy)에 가산 합성"""
    if abs(alpha) <= 0.002:          # 음수 alpha = 반전 컷에서 글자 파내기
        return
    m = mask.astype(np.float32)
    if m.max() > 1.5:
        m = m / 255.0
    if scale != 1.0:
        h, w = m.shape
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        if nw > 6000 or nh > 6000:
            return
        m = cv2.resize(m, (nw, nh), interpolation=cv2.INTER_LINEAR)
    if rot:
        h, w = m.shape
        d = int((h ** 2 + w ** 2) ** 0.5)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0)
        M[0, 2] += (d - w) / 2
        M[1, 2] += (d - h) / 2
        m = cv2.warpAffine(m, M, (d, d))
    if blur > 0:
        k = int(blur) * 2 + 1
        m = cv2.GaussianBlur(m, (k, k), 0)

    h, w = m.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    layers = [(m, 1.0)]
    if glow > 0:
        # 마스크 바깥으로 번질 자리를 미리 확보하지 않으면 글로우가 사각형으로 잘린다
        pad = int(glow_r * 1.6) + 4
        mp = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        k = int(glow_r) * 2 + 1
        layers.insert(0, (cv2.GaussianBlur(mp, (k, k), 0), glow))

    for lm, la in layers:
        lh, lw = lm.shape
        lx0, ly0 = int(cx - lw / 2), int(cy - lh / 2)
        sx0, sy0 = max(0, lx0), max(0, ly0)
        sx1, sy1 = min(W, lx0 + lw), min(H, ly0 + lh)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        sub = lm[sy0 - ly0:sy1 - ly0, sx0 - lx0:sx1 - lx0] * (alpha * la)
        for c in range(3):
            if color[c]:
                dst[sy0:sy1, sx0:sx1, c] += sub * color[c]


def beam(dst, x, y0, angle, spread, length, a):
    """상단에서 내려오는 빛 기둥"""
    if a <= 0.002:
        return
    pts = np.array([[x, y0],
                    [x - spread + np.sin(angle) * length, y0 + length],
                    [x + spread + np.sin(angle) * length, y0 + length]], np.int32)
    layer = np.zeros((H, W), np.float32)
    cv2.fillPoly(layer, [pts], 1.0)
    grad = np.linspace(1.0, 0.0, H, dtype=np.float32)[:, None] ** 1.6
    layer *= np.roll(grad, int(y0), axis=0)
    layer = cv2.GaussianBlur(layer, (61, 61), 0)
    dst += layer[..., None] * a


def haze(dst, x, y, r, a):
    if a <= 0.002:
        return
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
    g = np.clip(1 - d, 0, 1) ** 2.2
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    dst += g[..., None] * a


# 사전 계산
_vig = None
_grain = None


def vignette():
    global _vig
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.72)) ** 2)
        _vig = np.clip(1.15 - d ** 1.9, 0, 1)[..., None]
    return _vig


def grain(i):
    global _grain
    if _grain is None:
        rng = np.random.default_rng(3)
        _grain = [(rng.standard_normal((H // 2, W // 2)).astype(np.float32)) for _ in range(8)]
    g = _grain[i % 8]
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]


def chroma(img, px):
    if px < 0.4:
        return img
    p = int(px)
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], p, axis=1)
    out[..., 2] = np.roll(img[..., 2], -p, axis=1)
    return out


def shake(img, ax, ay, rot=0.0):
    if abs(ax) < 0.3 and abs(ay) < 0.3 and abs(rot) < 0.02:
        return img
    M = cv2.getRotationMatrix2D((W / 2, H / 2), rot, 1.0)
    M[0, 2] += ax
    M[1, 2] += ay
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)


def zoom(img, s, cx=W / 2, cy=H / 2):
    if abs(s - 1.0) < 0.002:
        return img
    M = cv2.getRotationMatrix2D((cx, cy), 0, s)
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
