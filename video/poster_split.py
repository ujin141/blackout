"""
디제잉 풀파티 × 솔로파티 — 포스터.

    위   물        → 풀파티
    아래 DJ 장비    → 디제잉
    카피            → 솔로파티

촌스러워지지 않으려고 지키는 것 (처음 만든 게 전단지처럼 나와서 다시 짬)
    · 글자에 그림자·외곽선을 넣지 않는다. 대신 사진을 눌러 대비를 만든다.
    · 가운데 정렬하지 않는다. 좌측 기준선 하나로 세운다.
    · 색은 사진과 흰색만. 노란 알약·노란 띠를 넣는 순간 전단지가 된다.
    · 한글은 볼드 대신 자간을 준 보통 굵기.
    · 정보는 라벨 + 값의 표로. 문장으로 늘어놓지 않는다.

⚠ 브랜드 흑백 규칙 예외(사진 컬러). 행사 모객용이다.

사진 (둘 다 CC0 — 표기 의무 없음, 상업적 사용 가능)
    pool-cc0.jpg   수영장 수면
    mixer-cc0.jpg  Pioneer 믹서 위의 손. 얼굴이 안 나와서 초상권 문제가 없다.

python poster_split.py  →  out/poster/split_{feed,story}.png
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
from fonts import KR, KRB

# ── 여기만 고치면 됨 ───────────────────────────────────────
HOOK   = '혼자 와도 됩니다'
ROWS   = [('DATE',    '일정 공개 예정'),           # 예: '8월 23일 토요일'
          ('TIME',    '오후 2시 — 밤 10시'),
          ('VENUE',   '장소 추후 공지'),           # 예: '서울 강남'
          ('LINE UP', 'DEMIC · V · LYNN · AROS · TS'),
          ('ENTRY',   '스탠딩 00,000원 · 성비 1:1 · 웰컴드링크 1잔')]
HANDLE = '@BLACKOUTCREW_OFFICIAL'
NOTE   = '예약 · 문의는 DM'
# ──────────────────────────────────────────────────────────

OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

NAVY  = np.array([0.01, 0.05, 0.15], np.float32)
WHITE = np.array([1.00, 1.00, 1.00], np.float32)


def tmask(text, path, size, track_em=0.0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 100, asc + desc + 80), 0)
    d = ImageDraw.Draw(im)
    x = 50
    for c, wc in zip(text, ws):
        d.text((x, 40), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    lo, hi = 8, 460
    for _ in range(20):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def paint(dst, m, x, y, color=WHITE, a=1.0, anchor='l'):
    """anchor: l=왼쪽 기준, r=오른쪽 기준, c=가운데"""
    H, W = dst.shape[:2]
    m = m.astype(np.float32) / 255.0
    h, w = m.shape
    x0 = int(x) if anchor == 'l' else (int(x - w) if anchor == 'r' else int(x - w / 2))
    y0 = int(y - h / 2)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = m[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * a
    dst[sy0:sy1, sx0:sx1] = dst[sy0:sy1, sx0:sx1] * (1 - sub) + color * sub


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5):
    im = Image.open(path).convert('RGB')
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0 = max(0, (im.width - W) // 2)
    y0 = int(max(0, min(im.height - H, im.height * focus - H * 0.5)))
    a = np.asarray(im.crop((x0, y0, x0 + W, y0 + H))).astype(np.float32) / 255.0
    lum = a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114
    lum = np.clip((lum - 0.5) * contrast + 0.5, 0, 1) ** 0.92
    duo = shadow + (light - shadow) * lum[..., None]
    return np.ascontiguousarray(np.clip(duo * (1 - keep) + a * keep, 0, 1))


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0      # 작은 글자는 폭 기준. 높이로 잡으면 스토리에서 여백을 다 먹는다.
    M = int(W * 0.088)                      # 좌측 기준선. 모든 글자가 여기서 시작한다.
    SEAM = int(H * (0.44 if story else 0.46))

    img = np.zeros((H, W, 3), np.float32)
    img[:SEAM] = duotone(os.path.join(STOCK, 'pool-cc0.jpg'), W, SEAM,
                         np.array([0.02, 0.20, 0.55], np.float32),
                         np.array([0.72, 0.97, 1.00], np.float32),
                         contrast=1.28, keep=0.12, focus=0.42)
    img[SEAM:] = duotone(os.path.join(STOCK, 'mixer-cc0.jpg'), W, H - SEAM,
                         np.array([0.01, 0.04, 0.12], np.float32),
                         np.array([0.26, 0.62, 0.96], np.float32),
                         contrast=1.32, keep=0.14, focus=0.58)

    # 아래를 눌러 글자 자리를 만든다 — 그림자 대신 이걸로 대비를 낸다
    g = np.zeros((H, 1, 1), np.float32)
    n = H - SEAM
    g[SEAM:, 0, 0] = np.linspace(0.30, 0.93, n, dtype=np.float32) ** 0.85
    img = img * (1 - g * 0.95) + NAVY * (g * 0.95)
    # 물 쪽도 위아래만 살짝
    t = np.zeros((H, 1, 1), np.float32)
    t[:int(H * 0.20), 0, 0] = np.linspace(0.5, 0, int(H * 0.20), dtype=np.float32)
    img = img * (1 - t * 0.5) + NAVY * (t * 0.5)

    # 경계 — 얇은 흰 선 하나
    img[SEAM:SEAM + max(1, int(2 * U))] = WHITE * 0.9 + img[SEAM:SEAM + max(1, int(2 * U))] * 0.1

    # ── 상단 ──────────────────────────────────────────────
    lg = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    hgt = int(46 * V)
    lg = lg.resize((max(1, int(lg.width * hgt / lg.height)), hgt), Image.LANCZOS)
    paint(img, np.asarray(lg).astype(np.float32)[..., 3], M, H * 0.068)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(17 * V), 0.30), M + hgt + int(18 * V), H * 0.068, a=0.9)
    paint(img, tmask('SEOUL', BRAND, int(17 * V), 0.30), W - M, H * 0.068, a=0.55, anchor='r')

    # ── 타이틀 — 좌측 기준선에서 시작, 경계를 물고 앉는다 ──
    tw = W - M * 2
    s1 = fit('POOL PARTY', BRAND, tw, 0.02)
    paint(img, tmask('POOL PARTY', BRAND, s1, 0.02), M, SEAM - 118 * U)
    s2 = fit('SOLO PARTY', BRAND, tw, 0.02)
    paint(img, tmask('SOLO PARTY', BRAND, s2, 0.02), M, SEAM + 118 * U)
    # × 는 오른쪽 끝에 작게. 가운데에 크게 박으면 촌스러워진다.
    paint(img, tmask('×', BRAND, int(52 * V)), W - M, SEAM + 4 * U, a=0.9, anchor='r')

    # ── 한 줄 ─────────────────────────────────────────────
    paint(img, tmask(HOOK, KR, int(52 * (U + V) / 2), 0.02), M, H * (0.612 if story else 0.628))

    # ── 정보표 ────────────────────────────────────────────
    y0 = H * (0.686 if story else 0.698)
    step = H * (0.045 if story else 0.048)
    lx = M + int(W * 0.215)                 # 값이 시작하는 열
    for i, (k, v) in enumerate(ROWS):
        y = y0 + step * i
        img[int(y - step * 0.46):int(y - step * 0.46) + 1, M:W - M] += 0.16
        paint(img, tmask(k, BRAND, int(15 * V), 0.24), M, y, a=0.5)
        sz = min(int(25 * V), fit(v, KR, W - M - lx))
        paint(img, tmask(v, KR, sz, 0.01), lx, y, a=0.95)
    img[int(y0 + step * (len(ROWS) - 0.46)):int(y0 + step * (len(ROWS) - 0.46)) + 1, M:W - M] += 0.16

    # ── 하단 ──────────────────────────────────────────────
    by = H * 0.955
    paint(img, tmask(HANDLE, BRAND, int(19 * V), 0.16), M, by, a=0.9)
    paint(img, tmask(NOTE, KR, int(21 * V), 0.02), W - M, by, a=0.6, anchor='r')

    img += np.random.default_rng(4).standard_normal((H, W, 1)).astype(np.float32) * 0.008
    return np.clip(img, 0, 1)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    a = build(W, H, story)
    p = os.path.join(OUT, f'split_{tag}.png')
    Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)

print('->', OUT)
