"""
풀파티 × 솔로파티 포스터 — 컨셉을 그림으로 말한다.

검정 일색으로 가면 언더그라운드 클럽 포스터가 된다.
이 행사는 낮에 물에서 놀고, 혼자 온 사람끼리 만나는 자리다.
그래서 밝게 간다. 브랜드 흑백은 지키되 톤을 뒤집는다.

컨셉 장치
    겹치는 두 개의 원   혼자 온 사람 둘이 만나는 지점. × 가 정확히 그 교점에 놓인다
    물결(코스틱)        수면
    강한 햇빛           낮

"혼자 와도 됩니다" 한 줄이 이 포스터의 핵심이다.
솔로파티에서 사람들이 가장 무서워하는 건 혼자 가는 것이다.

python poster_solo.py  →  out/poster/solo_{feed,story}_{light,dark}.png
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
DATE_EN  = 'COMING SOON'            # 예: 'SAT 08.23'
DATE_KR  = '일정 공개 예정'           # 예: '8월 23일 토요일 · 오후 2시'
INFO     = 'VENUE TBA'              # 예: 'SEOUL · 강남'
HOOK     = '혼자 와도 됩니다'          # 이 줄이 제일 중요하다
SUB      = '어차피 다 혼자 옵니다'
LINEUP   = ['DEMIC', 'V', 'LYNN', 'AROS', 'TS']
NOTE_KR  = '예약 · 문의는 DM'
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


def ink(dst, m, cx, cy, a=1.0, soft=0.0, soft_r=20):
    """잉크를 얹는다 (값이 클수록 진하다). 마지막에 1-ink 로 뒤집어 흰 종이가 된다."""
    H, W = dst.shape[:2]
    m = m.astype(np.float32)
    if m.max() > 1.5:
        m /= 255.0
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


def caustics(dst, a, scale=1.0):
    """수면 물결 — 종이 위 옅은 회색 결"""
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    x, y = xx * 0.010 * scale, yy * 0.010 * scale
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37)) +
         0.8 * np.sin((x + y) * 0.85))
    lines = np.clip(1 - np.abs(np.sin(f * 1.7)) * 6.5, 0, 1) ** 1.3
    lines = cv2.GaussianBlur(lines, (0, 0), 1.1)
    dst += cv2.resize(lines, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def sunlight(dst, cx, cy, r, a):
    """햇빛 — 잉크를 걷어내 밝게 만든다"""
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:3, 0:W:3].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = np.clip(1 - d, 0, 1) ** 1.8
    dst -= cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a


def two_circles(dst, cx, cy, r, gap, th, a_line, a_fill):
    """겹치는 두 원 — 혼자 온 사람 둘이 만나는 지점"""
    H, W = dst.shape[:2]
    L = np.zeros((H // 2, W // 2), np.float32)
    c1 = (int((cx - gap / 2) / 2), int(cy / 2))
    c2 = (int((cx + gap / 2) / 2), int(cy / 2))
    rr = int(r / 2)
    if a_fill > 0:                                  # 겹치는 부분만 옅게 채운다
        A = np.zeros((H // 2, W // 2), np.float32)
        B = np.zeros((H // 2, W // 2), np.float32)
        cv2.circle(A, c1, rr, 1.0, -1, cv2.LINE_AA)
        cv2.circle(B, c2, rr, 1.0, -1, cv2.LINE_AA)
        L += (A * B) * (a_fill / max(a_line, 1e-6))
    cv2.circle(L, c1, rr, 1.0, th, cv2.LINE_AA)
    cv2.circle(L, c2, rr, 1.0, th, cv2.LINE_AA)
    L = cv2.GaussianBlur(L, (0, 0), 0.8)
    dst += cv2.resize(L, (W, H), interpolation=cv2.INTER_LINEAR)[..., None] * a_line


def build(W, H, story=False):
    U = H / 1350.0
    img = np.zeros((H, W, 3), np.float32)          # 잉크 양

    # 종이 결 — 물결
    caustics(img, 0.10, 1.0)

    # 햇빛 두 개 — 위쪽에서 들어온다
    sunlight(img, W * 0.72, H * 0.10, W * 0.85, 0.16)
    sunlight(img, W * 0.20, H * 0.30, W * 0.55, 0.07)

    # 컨셉 장치 — 겹치는 두 원.
    # 화면 안에 두 원이 통째로 들어와야 "둘이 겹친다"가 읽힌다.
    # 크게 키우면 하나의 큰 렌즈처럼 보여서 컨셉이 죽는다.
    CY = H * (0.34 if story else 0.36)
    R, GAP = W * 0.285, W * 0.28
    two_circles(img, W / 2, CY, r=R, gap=GAP,
                th=max(2, int(3 * U)), a_line=0.50, a_fill=0.05)

    # ── 상단 ──────────────────────────────────────────────
    top = H * (0.085 if story else 0.068)
    ink(img, logo_alpha('logo-mark.png', int(66 * U)), W / 2, top, 0.85, soft=0.15, soft_r=14)
    m = tmask('BLACKOUT CREW PRESENTS', BRAND, int(18 * U), 0.34)
    ink(img, m, W / 2, top + 60 * U, 0.5)

    # ── 타이틀 — × 가 두 원의 교점에 놓인다 ────────────────
    tw = W * 0.64                                   # 원보다 좁게. 원이 글자를 감싸 보이게.
    m = tmask('POOL PARTY', BRAND, fit('POOL PARTY', BRAND, tw, 0.05), 0.05)
    ink(img, m, W / 2, CY - 108 * U, 1.0, soft=0.10, soft_r=16)
    m = tmask('×', BRAND, fit('×', BRAND, 86 * U))
    ink(img, m, W / 2, CY, 1.0, soft=0.12, soft_r=18)
    m = tmask('SOLO PARTY', BRAND, fit('SOLO PARTY', BRAND, tw, 0.05), 0.05)
    ink(img, m, W / 2, CY + 108 * U, 1.0, soft=0.10, soft_r=16)

    # ── 호감 — 이 포스터에서 제일 중요한 줄 ────────────────
    hy = H * (0.63 if story else 0.665)
    m = tmask(HOOK, KRB, int(58 * U))
    ink(img, m, W / 2, hy, 0.95, soft=0.10, soft_r=16)
    m = tmask(SUB, KR, int(28 * U))
    ink(img, m, W / 2, hy + 58 * U, 0.5)

    # ── 날짜 ──────────────────────────────────────────────
    ry = int(hy + 108 * U)
    img[ry:ry + max(1, int(2 * U)), int(W * 0.38):int(W * 0.62)] += 0.32
    dy = hy + 168 * U
    m = tmask(DATE_EN, BRAND, fit(DATE_EN, BRAND, W * 0.52, 0.14), 0.14)
    ink(img, m, W / 2, dy, 0.95, soft=0.10, soft_r=16)
    m = tmask(DATE_KR, KRB, int(27 * U))
    ink(img, m, W / 2, dy + 52 * U, 0.58)
    m = tmask(INFO, BRAND, int(20 * U), 0.26)
    ink(img, m, W / 2, dy + 96 * U, 0.48)

    # ── 라인업 ────────────────────────────────────────────
    ly = H * (0.885 if story else 0.912)
    txt = '  ·  '.join(LINEUP)
    m = tmask(txt, BRAND, fit(txt, BRAND, W * 0.80, 0.10), 0.10)
    ink(img, m, W / 2, ly, 0.85)

    # ── 하단 ──────────────────────────────────────────────
    m = tmask('@BLACKOUTCREW_OFFICIAL', BRAND, int(20 * U), 0.16)
    ink(img, m, W / 2, H * (0.940 if story else 0.965), 0.7)
    if story:
        m = tmask(NOTE_KR, KR, int(22 * U))
        ink(img, m, W / 2, H * 0.965, 0.45)

    return np.clip(img, 0, 1.6)


def save(a, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    k = build(W, H, story)
    paper = 1.0 - k                                   # 흰 종이에 검은 잉크
    paper += np.random.default_rng(5).standard_normal((H, W, 1)).astype(np.float32) * 0.010
    save(paper, f'solo_{tag}_light')

    night = np.clip(k * 1.15, 0, 1)                   # 같은 판을 밤 버전으로
    night += np.random.default_rng(5).standard_normal((H, W, 1)).astype(np.float32) * 0.012
    save(night, f'solo_{tag}_dark')

print('->', OUT)
