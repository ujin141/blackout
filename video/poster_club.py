"""
풀파티 × 솔로파티 — 클럽 파티 시안 (B안).

`poster_split.py`(A안)와 같은 행사, 완전히 다른 판입니다.
두 개를 나란히 놓고 고르라고 만든 것이라 **일부러 겹치는 장치를 안 씁니다.**

            A안 (split)              B안 (club, 이 파일)
    구조     사진 두 장 · 7도 기울임    사진 한 장 · 엄격한 직각 격자
    타이포   가로 두 줄               세로로 쌓은 네 줄, 양끝 맞춤
    색       시안 × 마젠타            검정 × 형광 레드
    질감     물빛 섬광 · 보케          스캔라인 · 스트로브 바
    정보     라벨/값 한 줄 표          라벨 위 · 값 아래 카드형 격자

촌스러워지지 않으려고 지키는 것 (A안과 동일 — 이건 판이 달라도 안 바뀐다)
    · 글자에 그림자·외곽선을 넣지 않는다. 대비는 배경을 눌러서 만든다.
    · 색은 셋까지. 여기서는 검정·레드·흰색.
    · 한글은 볼드 대신 자간을 준 보통 굵기.
    · 작은 글자는 폭(V) 기준. 높이(U)로 잡으면 스토리에서 여백을 다 먹는다.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이다.

사진 club-cc0.jpg (CC0 — 표기 의무 없음, 상업적 사용 가능)
    아래쪽은 관객 얼굴이 다 나온다. CC0는 저작권만 푼 것이고 초상권은 별개라
    얼굴이 안 잡히는 위 34%(디스코볼·연기·트러스)만 잘라 쓴다.
    ZOOM/FOCUS 는 올리기만 할 것 — 낮추면 얼굴이 딸려 들어온다.

python poster_club.py  →  out/poster/club_{feed,story}.png
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
# (낱말, 폭 비율, 정렬, 색)  ·  None 은 구분선 자리
STACK  = [('POOL',  1.00, 'l', 'w'),
          ('PARTY', 0.58, 'r', 'r'),
          None,
          ('SOLO',  1.00, 'l', 'w'),
          ('PARTY', 0.58, 'r', 'r')]
# 행사 정보는 event.py 한 곳에서 온다. 여기서 고치지 말 것.
import event as EV
from poster_kit import timetable, partner_strip

CELLS  = [('DATE', EV.DATE), ('TIME', EV.TIME)]
WIDE   = ('ENTRY', EV.ENTRY)
HANDLE = EV.HANDLE
NOTE   = EV.NOTE
# ──────────────────────────────────────────────────────────

OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

INK   = np.array([0.03, 0.01, 0.02], np.float32)     # 완전한 검정은 인쇄물처럼 죽는다
WHITE = np.array([1.00, 1.00, 1.00], np.float32)
RED   = np.array([1.00, 0.16, 0.20], np.float32)


def tmask(text, path, size, track_em=0.0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 120, asc + desc + 100), 0)
    d = ImageDraw.Draw(im)
    x = 60
    for c, wc in zip(text, ws):
        d.text((x, 50), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    lo, hi = 8, 520
    for _ in range(20):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def paint(dst, m, x, y, color=WHITE, a=1.0, anchor='l', valign='c'):
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


def rule(dst, y, x0, x1, color, a, th=1):
    y = int(y)
    dst[y:y + th, int(x0):int(x1)] = dst[y:y + th, int(x0):int(x1)] * (1 - a) + color * a


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5, zoom=1.0):
    """명암만 남기고 두 색 사이로 다시 칠한다. 색조를 돌리면 원본 색이 남아 엉뚱하게 튄다."""
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


def strobe(img, V, seed):
    """가로로 지나가는 빛 띠. 조명이 한 번 터진 순간처럼 읽힌다.
    A안의 기울인 마퀴와 겹치지 않게, 여기서는 수평만 쓴다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    L = np.zeros((H, 1), np.float32)
    for _ in range(7):
        y = int(rng.uniform(0.04, 0.96) * H)
        h = int(rng.uniform(2, 26) * V)
        L[y:y + h, 0] = rng.uniform(0.05, 0.16)
    L = cv2.GaussianBlur(L, (1, 0), 6 * V)
    img += L[..., None] * np.array([1.0, 0.86, 0.86], np.float32)


def scanlines(img, V):
    """가는 가로줄. 인쇄물·모니터 질감이라 사진의 매끈함이 죽는다."""
    H = img.shape[0]
    g = np.ones((H, 1, 1), np.float32)
    step = max(3, int(4 * V))
    g[::step] = 0.90
    img *= g


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0                          # 작은 글자는 폭 기준
    M = int(W * 0.078)

    # 얼굴이 안 나오는 위쪽만. 값은 올리기만 할 것.
    img = duotone(os.path.join(STOCK, 'club-cc0.jpg'), W, H,
                  np.array([0.05, 0.00, 0.02], np.float32),
                  np.array([1.00, 0.24, 0.18], np.float32),
                  contrast=1.42, keep=0.12, focus=0.16, zoom=2.9)

    strobe(img, V, 7)
    scanlines(img, V)

    # 가운데를 비우고 위아래를 눌러 글자 자리를 만든다
    yy = np.mgrid[0:H, 0:1][0].astype(np.float32)
    v = np.clip(np.abs(yy / H - 0.42) / 0.52, 0, 1) ** 1.35
    img = img * (1 - v[..., None] * 0.78) + INK * (v[..., None] * 0.78)
    xx = np.mgrid[0:1, 0:W][1].astype(np.float32)
    hv = (np.clip((np.abs(xx / W - 0.5) - 0.22) / 0.28, 0, 1) ** 1.4 * 0.55)
    img = img * (1 - hv[..., None]) + INK * hv[..., None]
    img = img * 0.80 + INK * 0.20                       # 전체를 한 번 더 눌러 밤으로

    # ── 격자 — A안의 기울임과 정반대. 전부 직각으로 잡는다 ──
    fx0, fx1 = M, W - M
    ty, by = H * 0.052, H * 0.976
    rule(img, ty, fx0, fx1, RED, 0.55, max(1, int(2 * V)))
    rule(img, by, fx0, fx1, RED, 0.55, max(1, int(2 * V)))

    # ── 상단 ──────────────────────────────────────────────
    lg = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    hgt = int(42 * V)
    lg = lg.resize((max(1, int(lg.width * hgt / lg.height)), hgt), Image.LANCZOS)
    hy = ty + 44 * V
    paint(img, np.asarray(lg).astype(np.float32)[..., 3], M, hy)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(16 * V), 0.30), M + hgt + int(16 * V), hy, a=0.92)
    paint(img, tmask('SEOUL', BRAND, int(16 * V), 0.30), W - M, hy, color=RED, a=0.9, anchor='r')

    # ── 쌓아 올린 타이포 ──────────────────────────────────
    # 큰 낱말은 전폭 왼쪽, 작은 낱말은 60% 폭 오른쪽.
    # 전부 같은 폭으로 맞추면 네 줄이 다 커져서 세로가 넘치고,
    # 넘치지 않게 줄이면 오른쪽 여백이 남는다. 크기를 갈라 두 문제를 같이 푼다.
    band0, band1 = H * 0.130, H * 0.545
    colw = fx1 - fx0
    lead, divh = int(20 * U), int(104 * U)
    for _ in range(4):                                  # 칸에 맞을 때까지 폭을 줄인다
        rows, total = [], 0
        for it in STACK:
            if it is None:
                rows.append(None)
                total += divh
                continue
            wd, ratio, align, col = it
            m = tmask(wd, BRAND, fit(wd, BRAND, int(colw * ratio), 0.02), 0.02)
            rows.append((m, align, col))
            total += m.shape[0]
        total += lead * (len(STACK) - 1)
        if total <= band1 - band0:
            break
        colw = int(colw * (band1 - band0) / total)

    y = (band0 + band1) / 2 - total / 2
    for r in rows:
        if r is None:                                   # 구분선 + 큰 ×
            cy = y + divh / 2
            rule(img, cy, fx0, fx0 + colw - int(148 * V), WHITE, 0.45, max(1, int(2 * V)))
            paint(img, tmask('×', BRAND, int(112 * V)), fx0 + colw, cy, color=RED, anchor='r')
            y += divh + lead
            continue
        m, align, col = r
        x = fx0 if align == 'l' else fx0 + colw
        paint(img, m, x, y, color=(RED if col == 'r' else WHITE), anchor=align, valign='t')
        y += m.shape[0] + lead

    # ── 정보 — 라벨 위, 값 아래. A안의 한 줄 표와 다르게 간다 ──
    cw = (fx1 - fx0) / 2
    for i, (k, val) in enumerate([*CELLS, ('VENUE', EV.VENUE), WIDE]):
        cx = fx0 + cw * (i % 2)
        ry = H * 0.575 + H * 0.066 * (i // 2)
        rule(img, ry - 26 * U, cx, cx + cw - int(24 * V), WHITE, 0.18)
        paint(img, tmask(k, BRAND, int(13 * V), 0.26), cx, ry, color=RED, a=0.95)
        sz = min(int(24 * V), fit(val, KR, cw - int(30 * V)))
        paint(img, tmask(val, KR, sz, 0.01), cx, ry + 34 * U, a=0.97)

    # ── 타임테이블 ────────────────────────────────────────
    ty = H * 0.700
    rule(img, ty - 26 * U, fx0, fx1, WHITE, 0.18)
    paint(img, tmask('TIME TABLE', BRAND, int(13 * V), 0.26), fx0, ty, color=RED, a=0.95)
    # 시간은 흰색으로. 배경이 붉은 판이라 붉은 글자를 쓰면 같은 색끼리 겹쳐
    # 안 읽힌다 — 강조색은 구역 라벨에만 남긴다.
    timetable(img, EV.TIMETABLE, fx0, fx1, ty + H * 0.035, H * 0.030, V,
              WHITE, WHITE, cols=2, ksize=13, vsize=17, a=0.95)

    ps = EV.partner_paths()
    if ps:
        py = H * (0.872 if story else 0.878)
        rule(img, py - 44 * U, fx0, fx1, WHITE, 0.18)
        paint(img, tmask('PARTNERS', BRAND, int(13 * V), 0.26), fx0, py - 18 * U, color=RED, a=0.95)
        partner_strip(img, ps, fx0, fx1, py + 30 * U, H * 0.034, WHITE, a=0.9, align='l')

    # ── 하단 ──────────────────────────────────────────────
    fy = by - 30 * V
    paint(img, tmask(HANDLE, BRAND, int(17 * V), 0.16), M, fy, a=0.92)
    paint(img, tmask(NOTE, KR, int(19 * V), 0.02), W - M, fy, color=RED, a=0.95, anchor='r')

    img += np.random.default_rng(9).standard_normal((H, W, 1)).astype(np.float32) * 0.013
    return np.clip(img, 0, 1)


# import 만 해도 렌더가 도는 걸 막는다 — poster_motion.py 가 build() 를 가져다 쓴다
if __name__ == '__main__':
    for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
        a = build(W, H, story)
        p = os.path.join(OUT, f'club_{tag}.png')
        Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)

    print('->', OUT)
