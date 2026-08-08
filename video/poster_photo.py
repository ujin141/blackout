"""
풀파티 × 솔로파티 — 실사 사진 버전.

레퍼런스에서 공통으로 나오는 구성을 그대로 따랐다.
    물 사진을 꽉 채우고            → "풀파티"가 0.5초 안에 읽힌다
    아래를 어둡게 눌러 글자 자리    → 사진 위 글자는 눌러야 읽힌다
    두꺼운 흰 글자 + 그림자
    노란 포인트(알약 · CTA 띠)     → 물색 위에서 보색이라 제일 먼저 보인다

⚠ 브랜드 흑백 규칙 예외. 행사 모객용이다.

사진: assets/img/stock/pool-cc0.jpg
    Wikimedia Commons — "A close up of a swimming pool with water" (Markus Spiske)
    CC0 (저작권 포기). 출처 표기 의무 없음. 상업적 사용 가능.

python poster_photo.py  →  out/poster/photo_{feed,story}.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
PHOTO = os.path.join(IMG, 'stock', 'pool-cc0.jpg')
from fonts import KR, KRB

# ── 여기만 고치면 됨 ───────────────────────────────────────
DATE_KR = '일정 공개 예정'          # 예: '8월 23일 토요일'
TIME_KR = '오후 2시 — 밤 10시'
PLACE   = '장소 추후 공지'          # 예: '서울 강남 · OO 루프탑'
PILLS   = ['사전 예약제', '웰컴드링크 1잔', '선착순 마감']
PRICE   = '스탠딩 00,000원'
CTA     = '예약 · 문의는 DM'
HANDLE  = '@blackoutcrew_official'
LINEUP  = 'DEMIC · V · LYNN · AROS · TS'
# ──────────────────────────────────────────────────────────

OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

YELLOW = np.array([1.00, 0.84, 0.10], np.float32)
NAVY   = np.array([0.01, 0.09, 0.26], np.float32)
WHITE  = np.array([1.00, 1.00, 1.00], np.float32)


def tmask(text, path, size, track_em=0.0, stroke=0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    pad = stroke * 2 + 60
    im = Image.new('L', (total + pad * 2, asc + desc + pad * 2), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for c, wc in zip(text, ws):
        d.text((x, pad), c, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0, stroke=0):
    lo, hi = 8, 460
    for _ in range(20):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em, stroke).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def paint(dst, m, cx, cy, color, a=1.0, shadow=0.0, sh_off=(0, 0), sh_blur=7):
    H, W = dst.shape[:2]
    m = m.astype(np.float32) / 255.0
    h, w = m.shape

    def put(mm, col, alpha, ox, oy):
        x0, y0 = int(cx - w / 2 + ox), int(cy - h / 2 + oy)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
        if sx1 <= sx0 or sy1 <= sy0:
            return
        sub = mm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * alpha
        dst[sy0:sy1, sx0:sx1] = dst[sy0:sy1, sx0:sx1] * (1 - sub) + col * sub

    if shadow > 0:
        put(cv2.GaussianBlur(m, (0, 0), sh_blur), NAVY, shadow, sh_off[0], sh_off[1])
    put(m, color, a, 0, 0)


def photo_bg(W, H):
    """CC0 풀 사진을 꽉 채우고 물색으로 보정한다 (원본은 보랏빛이다)."""
    im = Image.open(PHOTO).convert('RGB')
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0 = max(0, (im.width - W) // 2)
    y0 = max(0, (im.height - H) // 2)
    a = np.asarray(im.crop((x0, y0, x0 + W, y0 + H))).astype(np.float32) / 255.0

    # 색조만 돌리면 원본에 남아 있는 색 때문에 엉뚱한 색(분홍 다이빙대)이 튄다.
    # 명암만 남기고 두 색 사이로 다시 칠하는 듀오톤이 통제하기 쉽고 인쇄물처럼 보인다.
    lum = (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114)
    lum = np.clip((lum - 0.5) * 1.25 + 0.50, 0, 1) ** 0.92
    SHADOW = np.array([0.01, 0.16, 0.52], np.float32)      # 깊은 물
    LIGHT = np.array([0.62, 0.96, 1.00], np.float32)       # 수면에 튀는 빛
    duo = SHADOW + (LIGHT - SHADOW) * lum[..., None]
    a = duo * 0.88 + a * 0.12                              # 원본 결을 조금만 남긴다
    return np.ascontiguousarray(np.clip(a, 0, 1))


def shade(dst, y0, y1, a, top=False):
    """글자 자리를 만들기 위해 눌러 준다"""
    H = dst.shape[0]
    g = np.zeros((H, 1, 1), np.float32)
    n = int(y1) - int(y0)
    if n <= 0:
        return
    ramp = np.linspace(0, 1, n, dtype=np.float32) ** 1.25
    g[int(y0):int(y1), 0, 0] = ramp[::-1] if top else ramp
    if not top:
        g[int(y1):, 0, 0] = 1.0
    dst *= (1 - g * a)
    dst += NAVY * (g * a)


def pill(dst, text, cx, cy, U):
    m = tmask(text, KRB, int(26 * U))
    pw, ph = m.shape[1] + int(54 * U), m.shape[0] + int(32 * U)
    L = np.zeros(dst.shape[:2], np.float32)
    cv2.rectangle(L, (int(cx - pw / 2), int(cy - ph / 2)),
                  (int(cx + pw / 2), int(cy + ph / 2)), 1.0, -1, cv2.LINE_AA)
    sh = cv2.GaussianBlur(L, (0, 0), 7)
    dst[:] = dst * (1 - sh[..., None] * 0.35) + NAVY * (sh[..., None] * 0.35)
    dst[:] = dst * (1 - L[..., None]) + YELLOW * L[..., None]
    paint(dst, m, cx, cy, NAVY, 1.0)
    return pw


def build(W, H, story=False):
    U = H / 1350.0
    img = photo_bg(W, H)

    shade(img, 0, H * 0.16, 0.55, top=True)          # 상단
    shade(img, H * 0.30, H * 0.62, 0.62)             # 하단 전체

    # ── 타이틀 ────────────────────────────────────────────
    CY = H * (0.315 if story else 0.335)
    st = max(2, int(8 * U))
    m = tmask('POOL PARTY', KRB, fit('POOL PARTY', KRB, W * 0.88, 0.02, st), 0.02, st)
    paint(img, m, W / 2, CY - 92 * U, WHITE, 1.0, shadow=0.7, sh_off=(0, int(7 * U)), sh_blur=9)
    m = tmask('×', KRB, int(88 * U), 0, st)
    paint(img, m, W / 2, CY, YELLOW, 1.0, shadow=0.6, sh_off=(0, int(5 * U)))
    m = tmask('SOLO PARTY', KRB, fit('SOLO PARTY', KRB, W * 0.88, 0.02, st), 0.02, st)
    paint(img, m, W / 2, CY + 92 * U, WHITE, 1.0, shadow=0.7, sh_off=(0, int(7 * U)), sh_blur=9)

    # ── 문턱 낮추는 한 줄 ─────────────────────────────────
    m = tmask('혼자 와도 됩니다', KRB, int(60 * U))
    paint(img, m, W / 2, H * (0.470 if story else 0.480), YELLOW, 1.0,
          shadow=0.65, sh_off=(0, int(6 * U)))
    m = tmask('어차피 다 혼자 옵니다', KR, int(30 * U))
    paint(img, m, W / 2, H * (0.515 if story else 0.527), WHITE, 0.95,
          shadow=0.5, sh_off=(0, int(3 * U)))

    # ── 날짜 ──────────────────────────────────────────────
    m = tmask(DATE_KR, KRB, min(int(58 * U), fit(DATE_KR, KRB, W * 0.80)))
    paint(img, m, W / 2, H * 0.615, WHITE, 1.0, shadow=0.6, sh_off=(0, int(5 * U)))
    m = tmask(f'{TIME_KR}   ·   {PLACE}', KRB, int(26 * U))
    paint(img, m, W / 2, H * 0.663, WHITE, 0.95, shadow=0.5, sh_off=(0, int(3 * U)))

    # ── 정보 알약 ─────────────────────────────────────────
    py = H * 0.735
    sizes = [tmask(t, KRB, int(26 * U)).shape[1] + int(54 * U) for t in PILLS]
    gap = int(18 * U)
    x = W / 2 - (sum(sizes) + gap * (len(PILLS) - 1)) / 2
    for t, sw in zip(PILLS, sizes):
        pill(img, t, x + sw / 2, py, U)
        x += sw + gap

    # ── 가격 · 라인업 ─────────────────────────────────────
    m = tmask(PRICE, KRB, int(34 * U))
    paint(img, m, W / 2, H * 0.805, WHITE, 1.0, shadow=0.5, sh_off=(0, int(4 * U)))
    m = tmask(LINEUP, KRB, int(fit(LINEUP, KRB, W * 0.82, 0.04)), 0.04)
    paint(img, m, W / 2, H * 0.853, WHITE, 0.95, shadow=0.45, sh_off=(0, int(3 * U)))

    # ── CTA 띠 ────────────────────────────────────────────
    by, bh = H * 0.932, 118 * U
    img[int(by - bh / 2):int(by + bh / 2)] = YELLOW
    m = tmask(CTA, KRB, int(40 * U))
    paint(img, m, W / 2, by - 18 * U, NAVY, 1.0)
    m = tmask(HANDLE, KRB, int(26 * U))
    paint(img, m, W / 2, by + 26 * U, NAVY, 0.85)

    # ── 상단 브랜드 ───────────────────────────────────────
    lg = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    hgt = int(62 * U)
    lg = lg.resize((max(1, int(lg.width * hgt / lg.height)), hgt), Image.LANCZOS)
    al = np.asarray(lg).astype(np.float32)[..., 3]
    paint(img, al, W / 2, H * 0.055, WHITE, 0.95, shadow=0.5, sh_off=(0, int(3 * U)))
    m = tmask('BLACKOUT CREW PRESENTS', KRB, int(19 * U), 0.28)
    paint(img, m, W / 2, H * 0.093, WHITE, 0.8, shadow=0.45, sh_off=(0, int(2 * U)))

    img += np.random.default_rng(4).standard_normal((H, W, 1)).astype(np.float32) * 0.008
    return np.clip(img, 0, 1)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    a = build(W, H, story)
    p = os.path.join(OUT, f'photo_{tag}.png')
    Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)

print('->', OUT)
