"""
행사 포스터 — 화려하되 요소는 적게.

화려함은 '방사선 + 동심원' 한 덩어리로만 낸다. 나머지는 전부 비운다.
요소를 늘려서 화려하게 만들면 금방 촌스러워지고, 작은 화면에서 뭉개진다.
피드에서 멈추게 만드는 건 장식 개수가 아니라 대비다.

    dark   검정 바탕 — 기존 피드와 같은 결
    light  흑백 반전 — 어두운 피드에서 혼자 하얗게 튄다

python poster_event.py  →  out/poster/event_{feed,story}_{dark,light}.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KR, KRB

# ── 여기만 고치면 됨 ───────────────────────────────────────
TITLE1  = 'POOL PARTY'
TITLE2  = 'SOLO PARTY'
DATE_EN = 'COMING SOON'             # 예: 'SAT 08.23'
DATE_KR = '일정 공개 예정'            # 예: '8월 23일 토요일'
INFO    = 'VENUE TBA'               # 예: 'SEOUL · 강남 · 14:00 – 22:00'
LINEUP  = ['DEMIC', 'V', 'LYNN', 'AROS', 'TS']
NOTE_KR = '예약 · 문의는 DM'
# ──────────────────────────────────────────────────────────

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
    lo, hi = 8, 460
    for _ in range(22):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def blit(dst, m, cx, cy, a=1.0, glow=0.0, glow_r=24):
    H, W = dst.shape[:2]
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


def rays(dst, cx, cy, n=72, a=0.20, r0=0.06, r1=1.25):
    """방사선 — 이 포스터의 유일한 장식. 굵기를 번갈아 줘서 밀도를 만든다."""
    H, W = dst.shape[:2]
    L = np.zeros((H // 2, W // 2), np.float32)
    R = max(H, W) * r1 / 2
    for i in range(n):
        ang = i * 2 * np.pi / n
        th = 3 if i % 3 == 0 else 1
        x0 = cx / 2 + np.cos(ang) * (R * r0)
        y0 = cy / 2 + np.sin(ang) * (R * r0)
        x1 = cx / 2 + np.cos(ang) * R
        y1 = cy / 2 + np.sin(ang) * R
        cv2.line(L, (int(x0), int(y0)), (int(x1), int(y1)), 1.0, th, cv2.LINE_AA)
    # 바깥으로 갈수록 흐리게
    yy, xx = np.mgrid[0:H // 2, 0:W // 2].astype(np.float32)
    d = np.sqrt((xx - cx / 2) ** 2 + (yy - cy / 2) ** 2) / R
    L *= np.clip(1.15 - d, 0, 1) ** 1.5
    L = cv2.GaussianBlur(L, (0, 0), 1.2)
    dst += cv2.resize(L, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def rings(dst, cx, cy, radii, a=0.5, th=3):
    H, W = dst.shape[:2]
    L = np.zeros((H // 2, W // 2), np.float32)
    for r, w in radii:
        cv2.circle(L, (int(cx / 2), int(cy / 2)), int(r / 2), 1.0, w, cv2.LINE_AA)
    L = cv2.GaussianBlur(L, (0, 0), 0.9)
    dst += cv2.resize(L, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def disc(dst, cx, cy, r, a=1.0, soft=0.35):
    """가운데를 눌러 글자가 읽히게 만드는 원판"""
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = np.clip((1 - d) / soft, 0, 1)
    dst *= (1 - cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a)


def caustics(dst, a, y0=0.62):
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    x, y = xx * 0.011, yy * 0.011
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37)) +
         0.8 * np.sin((x + y) * 0.85))
    lines = np.clip(1 - np.abs(np.sin(f * 1.7)) * 7.5, 0, 1) ** 1.4
    lines = cv2.GaussianBlur(lines, (0, 0), 1.2)
    lines = cv2.resize(lines, (W, H), interpolation=cv2.INTER_LINEAR)
    grad = np.clip((np.arange(H, dtype=np.float32) - H * y0) / (H * (1 - y0)), 0, 1) ** 1.2
    dst += (lines * grad[:, None])[..., None] * a


def build(W, H, story=False):
    img = np.zeros((H, W, 3), np.float32)
    CX, CY = W / 2, H * (0.40 if story else 0.42)
    U = H / 1350.0                      # 세로 기준 배율

    # ── 화려함은 여기 하나로 ───────────────────────────────
    rays(img, CX, CY, n=84, a=0.17)
    rings(img, CX, CY, [(W * 1.02, 3), (W * 0.80, 2), (W * 0.58, 2)], a=0.30)
    caustics(img, 0.16, 0.60)
    disc(img, CX, CY, W * 0.50, a=0.86, soft=0.55)      # 가운데를 눌러 글자 자리 확보

    # ── 상단 ──────────────────────────────────────────────
    top = H * (0.13 if story else 0.10)
    blit(img, logo_alpha('logo-mark.png', int(78 * U)), CX, top, 0.95, glow=0.3, glow_r=20)
    m = tmask('BLACKOUT CREW PRESENTS', BRAND, int(20 * U), 0.34)
    blit(img, m, CX, top + 74 * U, 0.55)

    # ── 타이틀 ────────────────────────────────────────────
    tw = W * 0.80
    s1 = fit(TITLE1, BRAND, tw, 0.05)
    m = tmask(TITLE1, BRAND, s1, 0.05)
    blit(img, m, CX, CY - 118 * U, 1.0, glow=0.45, glow_r=34)

    s = fit('×', BRAND, 92 * U)
    m = tmask('×', BRAND, s)
    blit(img, m, CX, CY, 0.95, glow=0.5, glow_r=36)

    s2 = fit(TITLE2, BRAND, tw, 0.05)
    m = tmask(TITLE2, BRAND, s2, 0.05)
    blit(img, m, CX, CY + 118 * U, 1.0, glow=0.45, glow_r=34)

    # ── 날짜 ──────────────────────────────────────────────
    dy = CY + 300 * U
    m = tmask(DATE_EN, BRAND, int(fit(DATE_EN, BRAND, W * 0.62, 0.14)), 0.14)
    blit(img, m, CX, dy, 1.0, glow=0.38, glow_r=26)
    m = tmask(DATE_KR, KRB, int(32 * U))
    blit(img, m, CX, dy + 62 * U, 0.72)
    m = tmask(INFO, BRAND, int(23 * U), 0.26)
    blit(img, m, CX, dy + 118 * U, 0.55)

    # ── 라인업 ────────────────────────────────────────────
    ly = H * (0.80 if story else 0.83)
    m = tmask('LINE UP', BRAND, int(18 * U), 0.4)
    blit(img, m, CX, ly - 52 * U, 0.45)
    txt = '  ·  '.join(LINEUP)
    m = tmask(txt, BRAND, int(fit(txt, BRAND, W * 0.86, 0.10)), 0.10)
    blit(img, m, CX, ly, 0.95, glow=0.3, glow_r=20)

    # ── 하단 ──────────────────────────────────────────────
    by = H * (0.90 if story else 0.93)
    m = tmask('@BLACKOUTCREW_OFFICIAL', BRAND, int(22 * U), 0.16)
    blit(img, m, CX, by, 0.8, glow=0.24, glow_r=14)
    m = tmask(NOTE_KR, KR, int(24 * U))
    blit(img, m, CX, by + 48 * U, 0.5)

    # ── 마감 ──────────────────────────────────────────────
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.78)) ** 2 + ((yy - H / 2) / (H * 0.84)) ** 2)
    img *= np.clip(1.12 - d ** 2.0, 0, 1)[..., None]
    img += np.random.default_rng(12).standard_normal((H, W, 1)).astype(np.float32) * 0.014
    return np.clip(img, 0, 1)


def save(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((img * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    dark = build(W, H, story)
    save(dark, f'event_{tag}_dark')
    # 반전 — 어두운 피드에서 혼자 하얗게 튄다
    light = 1.0 - dark
    light = np.clip((light - 0.5) * 1.06 + 0.5, 0, 1)      # 반전 후 대비 보정
    save(light, f'event_{tag}_light')

print('->', OUT)
