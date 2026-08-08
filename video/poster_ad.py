"""
풀파티 × 솔로파티 — 판매용 포스터.

poster_solo.py 는 티저(컨셉만 보여주고 궁금하게 만드는 것)다.
이건 실제로 결제까지 끌고 가는 버전이라 정보 밀도를 올린다.

레퍼런스에서 공통으로 나오는 위계를 그대로 따랐다.
    1 행사명        가장 크게
    2 날짜 · 장소   두 번째로 크게. 못 찾으면 안 온다
    3 특징          성비 · 포함 혜택 · 정원. 솔로파티는 이게 결정 요인이다
    4 가격          숨기면 신뢰가 떨어진다
    5 CTA           뭘 해야 하는지 한 문장으로. 예약 창구를 명확히

티저와 달리 "예쁜 여백"보다 "빠짐없는 정보"가 우선이다.

python poster_ad.py  →  out/poster/ad_{feed,story}_{light,dark}.png
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
DATE_EN = 'COMING SOON'                 # 예: 'SAT 08.23'
DATE_KR = '일정 공개 예정'                # 예: '8월 23일 토요일'
TIME_KR = '시간 추후 공지'                # 예: '오후 2시 — 밤 10시'
PLACE   = '장소 추후 공지'                # 예: '서울 강남 · OO 루프탑'
HOOK    = '혼자 와도 됩니다'
FACTS   = [('성비', '1 : 1'),
           ('포함', '웰컴 드링크'),
           ('정원', '선착순')]
PRICE   = [('스탠딩', '가격 협의 중'),
           ('테이블', 'DM 문의')]
CTA     = '예약은 인스타 DM'
CTA_SUB = '@BLACKOUTCREW_OFFICIAL'
LINEUP  = ['DEMIC', 'V', 'LYNN', 'AROS', 'TS']
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


def ink(dst, m, cx, cy, a=1.0, soft=0.0, soft_r=18, left=None):
    H, W = dst.shape[:2]
    m = m.astype(np.float32)
    if m.max() > 1.5:
        m /= 255.0
    if left is not None:
        cx = left + m.shape[1] / 2
    layers = [(m, 1.0)]
    if soft > 0:
        pad = int(soft_r * 1.6) + 4
        mp = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
        layers.insert(0, (cv2.GaussianBlur(mp, (0, 0), soft_r * 0.55), soft))
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


def caustics(dst, a):
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    x, y = xx * 0.010, yy * 0.010
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37)) +
         0.8 * np.sin((x + y) * 0.85))
    lines = np.clip(1 - np.abs(np.sin(f * 1.7)) * 6.5, 0, 1) ** 1.3
    lines = cv2.GaussianBlur(lines, (0, 0), 1.1)
    dst += cv2.resize(lines, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def sunlight(dst, cx, cy, r, a):
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:3, 0:W:3].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    dst -= cv2.resize(np.clip(1 - d, 0, 1) ** 1.8, (W, H),
                      interpolation=cv2.INTER_LINEAR)[..., None] * a


def two_circles(dst, cx, cy, r, gap, th, a_line, a_fill):
    H, W = dst.shape[:2]
    L = np.zeros((H // 2, W // 2), np.float32)
    c1 = (int((cx - gap / 2) / 2), int(cy / 2))
    c2 = (int((cx + gap / 2) / 2), int(cy / 2))
    rr = int(r / 2)
    if a_fill > 0:
        A = np.zeros((H // 2, W // 2), np.float32)
        B = np.zeros((H // 2, W // 2), np.float32)
        cv2.circle(A, c1, rr, 1.0, -1, cv2.LINE_AA)
        cv2.circle(B, c2, rr, 1.0, -1, cv2.LINE_AA)
        L += (A * B) * (a_fill / max(a_line, 1e-6))
    cv2.circle(L, c1, rr, 1.0, th, cv2.LINE_AA)
    cv2.circle(L, c2, rr, 1.0, th, cv2.LINE_AA)
    dst += cv2.resize(cv2.GaussianBlur(L, (0, 0), 0.8), (W, H),
                      interpolation=cv2.INTER_LINEAR)[..., None] * a_line


def hline(dst, y, x0, x1, a, th=2):
    dst[int(y):int(y) + th, int(x0):int(x1)] += a


def box(dst, x0, y0, x1, y1, a, th=3):
    """CTA 테두리 — 여기가 끝점이라는 신호"""
    cv2.rectangle(dst, (int(x0), int(y0)), (int(x1), int(y1)), (a, a, a), th, cv2.LINE_AA)


def build(W, H, story=False):
    U = H / 1350.0
    M = W * 0.09                                  # 좌우 여백
    img = np.zeros((H, W, 3), np.float32)

    caustics(img, 0.085)
    sunlight(img, W * 0.74, H * 0.08, W * 0.80, 0.15)
    sunlight(img, W * 0.18, H * 0.26, W * 0.50, 0.06)

    # ── 1) 행사명 — 가장 크게 ─────────────────────────────
    CY = H * (0.245 if story else 0.265)
    two_circles(img, W / 2, CY, r=W * 0.255, gap=W * 0.25,
                th=max(2, int(3 * U)), a_line=0.45, a_fill=0.045)

    top = H * (0.055 if story else 0.048)
    ink(img, logo_alpha('logo-mark.png', int(58 * U)), W / 2, top, 0.8, soft=0.15, soft_r=12)
    m = tmask('BLACKOUT CREW PRESENTS', BRAND, int(17 * U), 0.34)
    ink(img, m, W / 2, top + 54 * U, 0.5)

    tw = W * 0.66
    m = tmask('POOL PARTY', BRAND, fit('POOL PARTY', BRAND, tw, 0.05), 0.05)
    ink(img, m, W / 2, CY - 92 * U, 1.0, soft=0.10, soft_r=15)
    m = tmask('×', BRAND, fit('×', BRAND, 74 * U))
    ink(img, m, W / 2, CY, 1.0, soft=0.12, soft_r=16)
    m = tmask('SOLO PARTY', BRAND, fit('SOLO PARTY', BRAND, tw, 0.05), 0.05)
    ink(img, m, W / 2, CY + 92 * U, 1.0, soft=0.10, soft_r=15)

    m = tmask(HOOK, KRB, int(46 * U))
    ink(img, m, W / 2, CY + 186 * U, 0.92, soft=0.08, soft_r=14)

    # ── 2) 날짜 · 장소 — 두 번째로 크게 ───────────────────
    # 세로 위치는 전부 H 비율로 잡는다. 오프셋을 누적하면 칸이 서로 먹는다.
    hline(img, H * 0.415, M, W - M, 0.30, max(1, int(2 * U)))
    m = tmask(DATE_EN, BRAND, fit(DATE_EN, BRAND, W * 0.58, 0.13), 0.13)
    ink(img, m, W / 2, H * 0.452, 1.0, soft=0.10, soft_r=16)
    m = tmask(f'{DATE_KR}  ·  {TIME_KR}', KRB, int(25 * U))
    ink(img, m, W / 2, H * 0.492, 0.7)
    m = tmask(PLACE, KRB, int(25 * U))
    ink(img, m, W / 2, H * 0.522, 0.7)
    hline(img, H * 0.552, M, W - M, 0.30, max(1, int(2 * U)))

    # ── 3) 특징 — 솔로파티는 이게 결정 요인 ───────────────
    fy = H * 0.605
    step = (W - M * 2) / len(FACTS)
    for i, (k, v) in enumerate(FACTS):
        cx = M + step * (i + 0.5)
        m = tmask(k, KRB, int(20 * U), 0.12)
        ink(img, m, cx, fy, 0.5)
        # 칸 폭을 넘지 않게 줄인다
        sz = min(int(27 * U), fit(v, KRB, step * 0.80))
        m = tmask(v, KRB, sz)
        ink(img, m, cx, fy + 44 * U, 0.9)
        if i:
            img[int(fy - 22 * U):int(fy + 62 * U),
                int(M + step * i):int(M + step * i) + 1] += 0.22

    # ── 4) 가격 ───────────────────────────────────────────
    px0, px1 = M + W * 0.05, W - M - W * 0.05
    for i, (k, v) in enumerate(PRICE):
        y = H * (0.705 + i * 0.038)
        m = tmask(k, KRB, int(25 * U), 0.1)
        ink(img, m, 0, y, 0.55, left=px0)
        mm = tmask(v, KRB, int(25 * U))
        ink(img, mm, 0, y, 0.92, left=px1 - mm.shape[1])
        img[int(y + 26 * U):int(y + 26 * U) + 1, int(px0):int(px1)] += 0.14

    # ── 5) 라인업 ─────────────────────────────────────────
    m = tmask('LINE UP', BRAND, int(16 * U), 0.4)
    ink(img, m, W / 2, H * 0.800, 0.42)
    txt = '  ·  '.join(LINEUP)
    m = tmask(txt, BRAND, fit(txt, BRAND, W * 0.76, 0.09), 0.09)
    ink(img, m, W / 2, H * 0.836, 0.88)

    # ── 6) CTA — 여기가 끝점이다 ──────────────────────────
    by = H * 0.925
    bh = 104 * U
    box(img, M, by - bh / 2, W - M, by + bh / 2, 0.55, max(2, int(3 * U)))
    m = tmask(CTA, KRB, int(36 * U))
    ink(img, m, W / 2, by - 15 * U, 0.98, soft=0.08, soft_r=12)
    m = tmask(CTA_SUB, BRAND, int(17 * U), 0.16)
    ink(img, m, W / 2, by + 26 * U, 0.6)

    return np.clip(img, 0, 1.6)


def save(a, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    k = build(W, H, story)
    rng = np.random.default_rng(6)
    save(1.0 - k + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.009, f'ad_{tag}_light')
    save(np.clip(k * 1.18, 0, 1) + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.011,
         f'ad_{tag}_dark')

print('->', OUT)
