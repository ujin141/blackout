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

# 행사 정보는 event.py 한 곳에서 온다. 여기서 고치지 말 것.
import event as EV
from poster_kit import timetable, partner_strip

HOOK   = ''                                # 한 줄 카피. 비우면 아예 안 그린다
ROWS   = [('DATE',  EV.DATE),
          ('TIME',  EV.TIME),
          ('VENUE', EV.VENUE),
          ('ENTRY', EV.ENTRY)]

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


def add(dst, layer, x0, y0, color, a):
    """빛은 더한다. 덮으면 사진이 죽고, 더하면 사진 위에 빛이 얹힌다."""
    H, W = dst.shape[:2]
    h, w = layer.shape
    x0, y0 = int(x0), int(y0)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst[sy0:sy1, sx0:sx1] += layer[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * color * a


def flare(size, V):
    """수면에 튀는 빛 — 가로로 길게 늘인 아나모픽 섬광.
    별표처럼 사방 대칭으로 그리면 크리스마스 장식이 된다. 가로를 2.6배 길게."""
    s = int(size)
    k = np.zeros((s, s), np.float32)
    c = s // 2
    th = max(1, int(1.6 * V))
    cv2.line(k, (0, c), (s - 1, c), 1.0, th, cv2.LINE_AA)
    cv2.line(k, (c, int(s * 0.30)), (c, int(s * 0.70)), 0.85, th, cv2.LINE_AA)
    yy, xx = np.mgrid[0:s, 0:s].astype(np.float32)
    r = np.sqrt(((xx - c) / (c * 1.0)) ** 2 + ((yy - c) / (c * 0.38)) ** 2)
    k *= np.clip(1 - r, 0, 1) ** 1.5
    k = cv2.GaussianBlur(k, (0, 0), max(0.8, 1.1 * V))
    core = np.clip(1 - np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / (c * 0.16), 0, 1) ** 2
    k = k + core * 0.9
    return k / max(k.max(), 1e-6)


def flares(img, lum, mask, n, V, seed):
    """제일 밝은 점들만 골라 섬광을 얹는다. 아무 데나 뿌리면 지저분해진다."""
    mx = cv2.dilate(lum, np.ones((71, 71), np.uint8))
    peaks = (lum >= mx - 1e-5) & (lum > 0.90) & mask
    ys, xs = np.where(peaks)
    if len(ys) == 0:
        return
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(ys), min(n, len(ys)), replace=False)
    for i in pick:
        s = int(rng.uniform(120, 250) * V)
        k = flare(s, V)
        a = rng.uniform(0.14, 0.30)
        add(img, k, xs[i] - s // 2, ys[i] - s // 2, np.array([0.85, 0.98, 1.00], np.float32), a)


def bokeh(img, y0, y1, n, V, seed):
    """초점 나간 조명 알갱이. 클럽 사진의 빈 어둠을 메운다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    L = np.zeros((H, W, 3), np.float32)
    for _ in range(n):
        x, y = int(rng.integers(0, W)), int(rng.integers(int(y0), int(y1)))
        r = int(rng.uniform(6, 30) * V)
        c = [MAGENTA, CYAN, np.array([1.0, 0.75, 0.95], np.float32)][int(rng.integers(0, 3))]
        a = float(rng.uniform(0.10, 0.30))
        cv2.circle(L, (x, y), r, tuple(float(v * a) for v in c), -1, cv2.LINE_AA)
        cv2.circle(L, (x, y), r, tuple(float(v * a * 0.8) for v in c), max(1, int(2 * V)), cv2.LINE_AA)
    img += cv2.GaussianBlur(L, (0, 0), 2.6 * V)


def glow(dst, m, x, y, color, a, r, anchor='l'):
    """네온 후광. 그림자와 다르다 — 어둡게 까는 게 아니라 빛을 더한다."""
    pad = int(r * 2.4) + 6
    mp = cv2.copyMakeBorder(m.astype(np.float32) / 255.0, pad, pad, pad, pad,
                            cv2.BORDER_CONSTANT, value=0)
    g = cv2.GaussianBlur(mp, (0, 0), r)
    g /= max(g.max(), 1e-6)
    h, w = g.shape
    x0 = x - pad if anchor == 'l' else x - w + pad
    add(dst, g, x0, y - h / 2, color, a)


def paint_split(dst, m, x, y, off, a=1.0):
    """색분해 — 마젠타·시안을 어긋나게 깔고 흰 글자를 덮는다.
    클럽 조명 아래 잔상처럼 읽힌다. 어긋남을 키우면 고장 난 것처럼 보이니
    글자 크기와 무관하게 W의 1% 안쪽으로 유지한다."""
    paint(dst, m, x - off, y + off * 0.55, MAGENTA, a * 0.9)
    paint(dst, m, x + off, y - off * 0.55, CYAN, a * 0.9)
    paint(dst, m, x, y, WHITE, a)


_STRIP = {}


def marquee(img, text, cy, bh, bg, fg, V, angle=None, phase=0.0):
    """눕혀 까는 흐르는 띠. phase 를 주면 글자가 흘러간다 (poster_motion.py 용).

    띠를 매번 새로 조판하면 프레임마다 tmask 가 돌아 느려진다 —
    한 번 만들어 캐시해 두고 np.roll 로만 밀어 준다."""
    angle = ANGLE if angle is None else angle
    H, W = img.shape[:2]
    LW = int(W * 2.2)
    key = (text, bh, V, bytes(bg), bytes(fg), LW)
    if key not in _STRIP:
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
        _STRIP[key] = (strip, tw + gap)
    strip, period = _STRIP[key]
    if phase:
        strip = np.roll(strip, int(phase) % period, axis=1)
    bh = strip.shape[0]
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
    SEAM = H * (0.34 if story else 0.36)

    # 물도 실제로 보이는 위 띠 높이에만 맞춰 자른다. 캔버스 전체에 맞추면
    # 다이빙대 끝만 삼각형처럼 삐져나와 무슨 물체인지 안 읽힌다 —
    # zoom 1.25 · focus 0.62 가 보드가 대각선으로 통째로 들어오는 자리다.
    ph = int(SEAM + 80 * U)
    pband = duotone(os.path.join(STOCK, 'pool-cc0.jpg'), W, ph,
                    np.array([0.00, 0.30, 0.80], np.float32),
                    np.array([0.82, 1.00, 1.00], np.float32),
                    contrast=1.30, keep=0.10, focus=0.62, zoom=1.25)
    pool = np.concatenate([pband, np.tile(pband[-1:], (H - ph, 1, 1))], 0)
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

    bloom(img, 0.74, 28 * V, 0.62, np.array([0.88, 0.94, 1.00], np.float32))

    # 아래를 눌러 글자 자리를 만든다 — 그림자 대신 이걸로 대비를 낸다
    # 두 단으로 누른다. 한 번에 다 누르면 디스코볼까지 죽어서 파티가 안 보인다 —
    # 타이틀 자리는 사진을 살리고, 표가 앉는 자리만 확실히 죽인다.
    d = (np.clip((yy - SEAM) / (H - SEAM), 0, 1) ** 0.55 * (1 - top[..., 0]) * 0.80)[..., None]
    img = img * (1 - d) + INK * d
    d2 = np.clip((yy - H * (0.560 if HOOK else 0.455)) / (H * 0.085), 0, 1)[..., None] * 0.68
    img = img * (1 - d2) + INK * d2
    t = np.clip(1 - yy / (H * 0.17), 0, 1)[..., None] * 0.42
    img = img * (1 - t) + INK * t
    # 물 쪽도 경계로 갈수록 눌러 준다 — 안 그러면 흰 타이틀이 수면 반짝임에 먹힌다
    p = (np.clip((yy - SEAM * 0.44) / (SEAM * 0.56), 0, 1) ** 1.15 * top[..., 0] * 0.62)[..., None]
    img = img * (1 - p) + INK * p

    # ── 빛 알갱이 — 누른 뒤에 더한다. 먼저 얹으면 같이 죽는다 ──
    lum = img[..., 0] * .299 + img[..., 1] * .587 + img[..., 2] * .114
    flares(img, lum, (top[..., 0] > 0.5) & (yy < SEAM * 0.80), 6, V, 11)
    bokeh(img, SEAM, H * 0.665, 34, V, 12)

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
    m1 = tmask('POOL PARTY', BRAND, fit('POOL PARTY', BRAND, tw, 0.02), 0.02)
    glow(img, m1, M, SEAM - 150 * U, CYAN, 0.55, 22 * V)
    paint_split(img, m1, M, SEAM - 150 * U, off)
    m2 = tmask('SOLO PARTY', BRAND, fit('SOLO PARTY', BRAND, tw, 0.02), 0.02)
    glow(img, m2, M, SEAM + 110 * U, MAGENTA, 0.60, 22 * V)
    paint_split(img, m2, M, SEAM + 110 * U, off)

    # ── 마퀴 두 줄. 서로 반대로 눕혀 화면을 잡아 준다 ───────
    # 위쪽은 물만 있는 빈 자리를 메운다. 셋 이상 깔면 산만해진다.
    marquee(img, 'DAY TO NIGHT  ×  SEOUL  ×  ', H * 0.158, int(40 * V), MAGENTA, INK, V, -ANGLE)
    marquee(img, 'POOL PARTY  ×  SOLO PARTY  ×  ', SEAM, int(52 * V), CYAN, INK, V)

    # ── 한 줄 — 이 포스터에서 제일 중요한 문장 ─────────────
    if HOOK:
        mh = tmask(HOOK, KR, int(54 * (U + V) / 2), 0.02)
        hy = H * (0.618 if story else 0.634)
        glow(img, mh, M, hy, CYAN, 0.50, 15 * V)
        paint(img, mh, M, hy, color=CYAN)

    # ── 정보표 ────────────────────────────────────────────
    y0 = H * (0.495 if story else 0.505)
    step = H * (0.040 if story else 0.042)
    lx = M + int(W * 0.215)                 # 값이 시작하는 열
    for i, (k, v) in enumerate(ROWS):
        y = y0 + step * i
        ry = int(y - step * 0.46)
        img[ry:ry + 1, M:W - M] = img[ry:ry + 1, M:W - M] * 0.7 + CYAN * 0.3
        paint(img, tmask(k, BRAND, int(15 * V), 0.24), M, y, color=CYAN, a=0.75)
        sz = min(int(24 * V), fit(v, KR, W - M - lx))
        paint(img, tmask(v, KR, sz, 0.01), lx, y, a=0.97)
    ry = int(y0 + step * (len(ROWS) - 0.46))
    img[ry:ry + 1, M:W - M] = img[ry:ry + 1, M:W - M] * 0.7 + CYAN * 0.3

    # ── 타임테이블 — 여덟 줄을 두 칸으로 접는다 ─────────────
    ty = H * (0.660 if story else 0.672)
    paint(img, tmask('TIME TABLE', BRAND, int(15 * V), 0.24), M, ty, color=CYAN, a=0.75)
    timetable(img, EV.TIMETABLE, M, W - M, ty + H * 0.035, H * 0.036,
              V, CYAN, WHITE, cols=2, ksize=14, vsize=18)

    # ── 협업 브랜드 ───────────────────────────────────────
    # 파일이 없으면 통째로 건너뛴다. 자리를 비워 두면 아래가 뜬 것처럼 보인다.
    ps = EV.partner_paths()
    if ps:
        py = H * (0.860 if story else 0.870)
        ry = int(py - H * 0.034)
        img[ry:ry + 1, M:W - M] = img[ry:ry + 1, M:W - M] * 0.7 + CYAN * 0.3
        paint(img, tmask('PARTNERS', BRAND, int(15 * V), 0.24), M, py, color=CYAN, a=0.75)
        partner_strip(img, ps, lx, W - M, py, H * 0.042, WHITE, a=0.9, align='l')

    # ── 하단 ──────────────────────────────────────────────
    by = H * 0.955
    paint(img, tmask(EV.HANDLE, BRAND, int(19 * V), 0.16), M, by, a=0.92)
    paint(img, tmask(EV.NOTE, KR, int(21 * V), 0.02), W - M, by, color=MAGENTA, a=0.95, anchor='r')

    # ── 여백 디테일 — 인쇄물처럼 보이게 하는 잔손질 ─────────
    # 네 귀퉁이 십자. 세로로 세웠던 옆 글자는 뺐다 — 타임테이블이 들어오면서
    # 오른쪽 값 열을 뚫고 지나갔고, 빽빽한 판에서는 장식이 소음이 된다.
    cm = tmask('+', BRAND, int(19 * V))
    for cx, cy, an in ((M, H * 0.030, 'l'), (W - M, H * 0.030, 'r'),
                       (M, H * 0.982, 'l'), (W - M, H * 0.982, 'r')):
        paint(img, cm, cx, cy, a=0.40, anchor=an)

    img += np.random.default_rng(4).standard_normal((H, W, 1)).astype(np.float32) * 0.010
    return np.clip(img, 0, 1)


# import 만 해도 렌더가 도는 걸 막는다 — poster_motion.py 가 build() 를 가져다 쓴다
if __name__ == '__main__':
    for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
        a = build(W, H, story)
        p = os.path.join(OUT, f'split_{tag}.png')
        Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)

    print('->', OUT)
