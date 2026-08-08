"""
디제잉 풀파티 × 솔로파티 — 포스터.

    위   물              → 풀파티
    아래 연기·조명·디스코볼 → 파티
    카피                 → 솔로파티

파티 느낌은 장식이 아니라 이 넷에서 나온다
    · 색 충돌      물(시안) 위 클럽(마젠타). 한 색으로 가면 잡지가 된다.
    · 기울어진 축   가로줄을 눕히면 정지 사진이 움직인다. 7도면 충분하다.
    · 흐르는 띠     경계에 마퀴를 깔면 소리가 나는 것처럼 읽힌다.
    · 번짐(bloom)   조명이 번져야 클럽이다. 사진을 그냥 쓰면 밋밋하다.

촌스러워지지 않으려고 지키는 것 (전단지처럼 나와서 한 번 갈아엎었다)
    · 글자에 그림자·외곽선을 넣지 않는다. 대비는 배경을 눌러서 만든다.
    · 가운데 정렬하지 않는다. 좌측 기준선 하나로 세운다.
    · 색은 시안·마젠타·흰색 셋뿐. 넷째 색이 들어오는 순간 전단지가 된다.
    · 한글은 볼드 대신 자간을 준 보통 굵기.
    · 타이틀은 가로로 두고 띠만 눕힌다. 다 눕히면 산만해진다.
    · 작은 글자는 폭(V) 기준. 높이(U)로 잡으면 스토리에서 여백을 다 먹는다.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이다.

사진 (전부 CC0 — 표기 의무 없음, 상업적 사용 가능)
    pool-cc0.jpg   수영장 수면
    club-cc0.jpg   클럽. 아래쪽은 관객 얼굴이 다 나온다 —
                   CC0는 저작권만 푼 것이고 초상권은 별개라
                   얼굴이 안 잡히는 위 34%(디스코볼·연기·트러스)만 잘라 쓴다.
                   ZOOM/FOCUS 를 건드리면 얼굴이 딸려 들어오니 주의.

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

ANGLE = 7.0                                          # 띠와 경계가 눕는 각도
INK     = np.array([0.06, 0.01, 0.14], np.float32)   # 가장 어두운 자리 (검정 대신 보라)
WHITE   = np.array([1.00, 1.00, 1.00], np.float32)
CYAN    = np.array([0.24, 0.98, 0.96], np.float32)
MAGENTA = np.array([1.00, 0.26, 0.72], np.float32)


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


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5, zoom=1.0):
    """명암만 남기고 두 색 사이로 다시 칠한다. 색조를 돌리면 원본 색이 남아 엉뚱하게 튄다.
    zoom 을 올리면 더 확대해 잘라낸다 — 사진의 일부만 쓰고 싶을 때."""
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


def bloom(img, thr, sigma, amt, tint):
    """밝은 곳을 번지게 한다. 조명이 번져야 클럽처럼 보인다."""
    lum = img[..., 0] * .299 + img[..., 1] * .587 + img[..., 2] * .114
    g = cv2.GaussianBlur(np.clip(lum - thr, 0, 1) / max(1 - thr, 1e-3), (0, 0), sigma)
    img += g[..., None] * tint * amt


def paint_split(dst, m, x, y, off, a=1.0):
    """색분해 — 마젠타·시안을 어긋나게 깔고 흰 글자를 덮는다.
    클럽 조명 아래 잔상처럼 읽힌다. 어긋남을 키우면 고장 난 것처럼 보이니
    글자 크기와 무관하게 W의 1% 안쪽으로 유지한다."""
    paint(dst, m, x - off, y + off * 0.55, MAGENTA, a * 0.9)
    paint(dst, m, x + off, y - off * 0.55, CYAN, a * 0.9)
    paint(dst, m, x, y, WHITE, a)


def marquee(img, text, cy, bh, bg, fg, V, angle=None):
    """눕혀 까는 흐르는 띠."""
    angle = ANGLE if angle is None else angle
    H, W = img.shape[:2]
    LW = int(W * 2.2)
    m = tmask(text, BRAND, int(21 * V), 0.36)
    th, tw = m.shape
    bh = max(bh, th + int(22 * V))
    strip = np.zeros((bh, LW, 3), np.float32) + bg
    ty = (bh - th) // 2
    x, gap = 0, int(40 * V)
    while x < LW:
        w = min(tw, LW - x)
        sub = (m[:, :w].astype(np.float32) / 255.0)[..., None]
        strip[ty:ty + th, x:x + w] = strip[ty:ty + th, x:x + w] * (1 - sub) + fg * sub
        x += tw + gap
    R = cv2.getRotationMatrix2D((LW / 2, bh / 2), angle, 1.0)
    R[0, 2] += W / 2 - LW / 2
    R[1, 2] += cy - bh / 2
    band = cv2.warpAffine(strip, R, (W, H), flags=cv2.INTER_LINEAR)
    ba = cv2.warpAffine(np.ones((bh, LW), np.float32), R, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    img[:] = img * (1 - ba) + band * ba


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0                          # 작은 글자는 폭 기준
    M = int(W * 0.088)                      # 좌측 기준선. 모든 글자가 여기서 시작한다.
    SEAM = H * (0.44 if story else 0.46)

    pool = duotone(os.path.join(STOCK, 'pool-cc0.jpg'), W, H,
                   np.array([0.00, 0.30, 0.80], np.float32),
                   np.array([0.82, 1.00, 1.00], np.float32),
                   contrast=1.30, keep=0.10, focus=0.32, zoom=1.15)
    # 클럽 사진은 가로로 넓다. 세로 캔버스 전체에 맞추면 가운데 빈 곳만 잘려
    # 보라색 덩어리가 된다 — 실제로 보이는 아래 띠 높이에만 맞춰 자른다.
    # zoom 2.9 · focus 0.16 이 위 34%(디스코볼·연기·트러스) 선이다.
    # 이 값을 낮추면 관객 얼굴이 딸려 들어온다. 초상권 때문에 올리기만 할 것.
    bh = int(H - SEAM + 80 * U)
    band = duotone(os.path.join(STOCK, 'club-cc0.jpg'), W, bh,
                   np.array([0.09, 0.00, 0.20], np.float32),
                   np.array([1.00, 0.34, 0.86], np.float32),
                   contrast=1.34, keep=0.18, focus=0.16, zoom=2.9)
    club = np.concatenate([np.tile(band[:1], (H - bh, 1, 1)), band], 0)

    # 눕힌 경계로 두 장을 붙인다
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    edge = SEAM - (xx - W / 2) * np.tan(np.radians(ANGLE))
    top = np.clip(edge - yy + 0.5, 0, 1)[..., None]
    img = club * (1 - top) + pool * top

    bloom(img, 0.66, 30 * V, 0.85, np.array([0.88, 0.94, 1.00], np.float32))

    # 아래를 눌러 글자 자리를 만든다 — 그림자 대신 이걸로 대비를 낸다
    # 두 단으로 누른다. 한 번에 다 누르면 디스코볼까지 죽어서 파티가 안 보인다 —
    # 타이틀 자리는 사진을 살리고, 표가 앉는 자리만 확실히 죽인다.
    d = (np.clip((yy - SEAM) / (H - SEAM), 0, 1) ** 0.55 * (1 - top[..., 0]) * 0.80)[..., None]
    img = img * (1 - d) + INK * d
    d2 = np.clip((yy - H * 0.645) / (H * 0.075), 0, 1)[..., None] * 0.62
    img = img * (1 - d2) + INK * d2
    t = np.clip(1 - yy / (H * 0.17), 0, 1)[..., None] * 0.42
    img = img * (1 - t) + INK * t
    # 물 쪽도 경계로 갈수록 눌러 준다 — 안 그러면 흰 타이틀이 수면 반짝임에 먹힌다
    p = (np.clip((yy - SEAM * 0.52) / (SEAM * 0.48), 0, 1) ** 1.25 * top[..., 0] * 0.46)[..., None]
    img = img * (1 - p) + INK * p

    # ── 상단 ──────────────────────────────────────────────
    lg = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    hgt = int(46 * V)
    lg = lg.resize((max(1, int(lg.width * hgt / lg.height)), hgt), Image.LANCZOS)
    paint(img, np.asarray(lg).astype(np.float32)[..., 3], M, H * 0.068)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(17 * V), 0.30), M + hgt + int(18 * V), H * 0.068, a=0.9)
    paint(img, tmask('SEOUL', BRAND, int(17 * V), 0.30), W - M, H * 0.068, a=0.6, anchor='r')

    # ── 타이틀 — 좌측 기준선에서 시작해 오른쪽으로 거의 흘러넘친다 ──
    tw = int(W - M * 1.25)
    off = int(6 * V)
    s1 = fit('POOL PARTY', BRAND, tw, 0.02)
    paint_split(img, tmask('POOL PARTY', BRAND, s1, 0.02), M, SEAM - 150 * U, off)
    s2 = fit('SOLO PARTY', BRAND, tw, 0.02)
    paint_split(img, tmask('SOLO PARTY', BRAND, s2, 0.02), M, SEAM + 132 * U, off)

    # ── 마퀴 두 줄. 서로 반대로 눕혀 화면을 잡아 준다 ───────
    # 위쪽은 물만 있는 빈 자리를 메운다. 셋 이상 깔면 산만해진다.
    marquee(img, 'DAY TO NIGHT  ×  SEOUL  ×  ', H * 0.212, int(40 * V), MAGENTA, INK, V, -ANGLE)
    marquee(img, 'POOL PARTY  ×  SOLO PARTY  ×  ', SEAM, int(52 * V), CYAN, INK, V)

    # ── 한 줄 — 이 포스터에서 제일 중요한 문장 ─────────────
    paint(img, tmask(HOOK, KR, int(54 * (U + V) / 2), 0.02), M,
          H * (0.618 if story else 0.634), color=CYAN)

    # ── 정보표 ────────────────────────────────────────────
    y0 = H * (0.690 if story else 0.702)
    step = H * (0.045 if story else 0.048)
    lx = M + int(W * 0.215)                 # 값이 시작하는 열
    for i, (k, v) in enumerate(ROWS):
        y = y0 + step * i
        ry = int(y - step * 0.46)
        img[ry:ry + 1, M:W - M] = img[ry:ry + 1, M:W - M] * 0.7 + CYAN * 0.3
        paint(img, tmask(k, BRAND, int(15 * V), 0.24), M, y, color=CYAN, a=0.75)
        sz = min(int(25 * V), fit(v, KR, W - M - lx))
        paint(img, tmask(v, KR, sz, 0.01), lx, y, a=0.97)
    ry = int(y0 + step * (len(ROWS) - 0.46))
    img[ry:ry + 1, M:W - M] = img[ry:ry + 1, M:W - M] * 0.7 + CYAN * 0.3

    # ── 하단 ──────────────────────────────────────────────
    by = H * 0.955
    paint(img, tmask(HANDLE, BRAND, int(19 * V), 0.16), M, by, a=0.92)
    paint(img, tmask(NOTE, KR, int(21 * V), 0.02), W - M, by, color=MAGENTA, a=0.95, anchor='r')

    img += np.random.default_rng(4).standard_normal((H, W, 1)).astype(np.float32) * 0.010
    return np.clip(img, 0, 1)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    a = build(W, H, story)
    p = os.path.join(OUT, f'split_{tag}.png')
    Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)

print('->', OUT)
