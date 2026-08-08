"""
디제잉 풀파티 × 솔로파티 — 위아래로 나눈 포스터.

컨셉이 셋인데 물 사진만 쓰면 그냥 수영장 행사로 읽힌다.
    위   물        → 풀파티
    아래 DJ 장비    → 디제잉
    경계 ×         → 두 개가 만나는 자리
    카피            → 솔로파티

⚠ 브랜드 흑백 규칙 예외. 행사 모객용이다.

사진 (둘 다 CC0 — 저작권 포기, 표기 의무 없음, 상업적 사용 가능)
    assets/img/stock/pool-cc0.jpg    수영장 수면
    assets/img/stock/mixer-cc0.jpg   Pioneer 믹서 위의 손
    믹서 사진을 고른 이유: DJ 장비가 또렷하고 **얼굴이 안 나온다.**
    저작권이 풀려도 초상권은 별개라, 얼굴이 크게 나오는 사진은 쓰지 않는다.

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
from fonts import KR, KRB

# ── 여기만 고치면 됨 ───────────────────────────────────────
DATE_KR = '일정 공개 예정'          # 예: '8월 23일 토요일'
TIME_KR = '오후 2시 — 밤 10시'
PLACE   = '장소 추후 공지'          # 예: '서울 강남 · OO 루프탑'
PILLS   = ['성비 1:1', '웰컴드링크 1잔', '선착순 마감']
PRICE   = '스탠딩 00,000원'
CTA     = '예약 · 문의는 DM'
HANDLE  = '@blackoutcrew_official'
LINEUP  = 'DEMIC · V · LYNN · AROS · TS'
# ──────────────────────────────────────────────────────────

OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

YELLOW = np.array([1.00, 0.84, 0.10], np.float32)
NAVY   = np.array([0.01, 0.07, 0.22], np.float32)
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


def paint(dst, m, cx, cy, color, a=1.0, shadow=0.0, sh_off=(0, 0), sh_blur=8):
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


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5):
    """사진을 잘라 두 색 사이로 다시 칠한다. 어떤 사진이든 톤이 튀지 않는다."""
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


def pill(dst, text, cx, cy, U):
    m = tmask(text, KRB, int(26 * U))
    pw, ph = m.shape[1] + int(54 * U), m.shape[0] + int(32 * U)
    L = np.zeros(dst.shape[:2], np.float32)
    cv2.rectangle(L, (int(cx - pw / 2), int(cy - ph / 2)),
                  (int(cx + pw / 2), int(cy + ph / 2)), 1.0, -1, cv2.LINE_AA)
    sh = cv2.GaussianBlur(L, (0, 0), 7)
    dst[:] = dst * (1 - sh[..., None] * 0.4) + NAVY * (sh[..., None] * 0.4)
    dst[:] = dst * (1 - L[..., None]) + YELLOW * L[..., None]
    paint(dst, m, cx, cy, NAVY, 1.0)
    return pw


def build(W, H, story=False):
    U = H / 1350.0
    SEAM = int(H * (0.375 if story else 0.400))

    img = np.zeros((H, W, 3), np.float32)
    # 위 — 물. 밝고 시원하게.
    img[:SEAM] = duotone(os.path.join(STOCK, 'pool-cc0.jpg'), W, SEAM,
                         np.array([0.02, 0.20, 0.58], np.float32),
                         np.array([0.68, 0.97, 1.00], np.float32),
                         contrast=1.3, keep=0.10, focus=0.45)
    # 아래 — 디제잉. 어둡게 눌러 글자가 올라갈 자리로.
    img[SEAM:] = duotone(os.path.join(STOCK, 'mixer-cc0.jpg'), W, H - SEAM,
                         np.array([0.01, 0.05, 0.16], np.float32),
                         np.array([0.30, 0.66, 0.98], np.float32),
                         contrast=1.35, keep=0.14, focus=0.55)

    # 아래쪽을 더 눌러 정보가 읽히게
    g = np.zeros((H, 1, 1), np.float32)
    n = H - SEAM
    g[SEAM:, 0, 0] = np.linspace(0.15, 0.88, n, dtype=np.float32) ** 0.9
    img *= (1 - g * 0.92)
    img += NAVY * (g * 0.92)

    # 경계선 — 수면
    img[SEAM - 3:SEAM + 3] = np.clip(img[SEAM - 3:SEAM + 3] * 0.3 + WHITE * 0.7, 0, 1)

    # ── 상단 브랜드 ───────────────────────────────────────
    lg = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    hgt = int(60 * U)
    lg = lg.resize((max(1, int(lg.width * hgt / lg.height)), hgt), Image.LANCZOS)
    paint(img, np.asarray(lg).astype(np.float32)[..., 3], W / 2, H * 0.052,
          WHITE, 0.95, shadow=0.55, sh_off=(0, int(3 * U)))
    m = tmask('BLACKOUT CREW PRESENTS', KRB, int(19 * U), 0.28)
    paint(img, m, W / 2, H * 0.090, WHITE, 0.85, shadow=0.5, sh_off=(0, int(2 * U)))

    # ── 타이틀 — 경계를 물고 앉는다 ───────────────────────
    st = max(2, int(8 * U))
    m = tmask('POOL PARTY', KRB, fit('POOL PARTY', KRB, W * 0.88, 0.02, st), 0.02, st)
    paint(img, m, W / 2, SEAM - 108 * U, WHITE, 1.0, shadow=0.75, sh_off=(0, int(7 * U)), sh_blur=10)
    m = tmask('SOLO PARTY', KRB, fit('SOLO PARTY', KRB, W * 0.88, 0.02, st), 0.02, st)
    paint(img, m, W / 2, SEAM + 108 * U, WHITE, 1.0, shadow=0.75, sh_off=(0, int(7 * U)), sh_blur=10)
    m = tmask('×', KRB, int(92 * U), 0, st)
    paint(img, m, W / 2, SEAM, YELLOW, 1.0, shadow=0.7, sh_off=(0, int(5 * U)))

    # ── 문턱 낮추는 한 줄 ─────────────────────────────────
    m = tmask('혼자 와도 됩니다', KRB, int(58 * U))
    paint(img, m, W / 2, H * 0.548, YELLOW, 1.0, shadow=0.6, sh_off=(0, int(5 * U)))
    m = tmask('어차피 다 혼자 옵니다', KR, int(29 * U))
    paint(img, m, W / 2, H * 0.588, WHITE, 0.92, shadow=0.45, sh_off=(0, int(3 * U)))

    # ── 날짜 ──────────────────────────────────────────────
    m = tmask(DATE_KR, KRB, min(int(56 * U), fit(DATE_KR, KRB, W * 0.80)))
    paint(img, m, W / 2, H * 0.658, WHITE, 1.0, shadow=0.55, sh_off=(0, int(5 * U)))
    m = tmask(f'{TIME_KR}   ·   {PLACE}', KRB, int(25 * U))
    paint(img, m, W / 2, H * 0.702, WHITE, 0.92, shadow=0.45, sh_off=(0, int(3 * U)))

    # ── 정보 알약 ─────────────────────────────────────────
    py = H * 0.772
    sizes = [tmask(t, KRB, int(26 * U)).shape[1] + int(54 * U) for t in PILLS]
    gap = int(18 * U)
    x = W / 2 - (sum(sizes) + gap * (len(PILLS) - 1)) / 2
    for t, sw in zip(PILLS, sizes):
        pill(img, t, x + sw / 2, py, U)
        x += sw + gap

    # ── 가격 · 라인업 ─────────────────────────────────────
    m = tmask(PRICE, KRB, int(33 * U))
    paint(img, m, W / 2, H * 0.838, WHITE, 1.0, shadow=0.45, sh_off=(0, int(4 * U)))
    m = tmask(LINEUP, KRB, int(fit(LINEUP, KRB, W * 0.82, 0.04)), 0.04)
    paint(img, m, W / 2, H * 0.881, WHITE, 0.95, shadow=0.4, sh_off=(0, int(3 * U)))

    # ── CTA 띠 ────────────────────────────────────────────
    by, bh = H * 0.948, 112 * U
    img[int(by - bh / 2):int(by + bh / 2)] = YELLOW
    m = tmask(CTA, KRB, int(38 * U))
    paint(img, m, W / 2, by - 17 * U, NAVY, 1.0)
    m = tmask(HANDLE, KRB, int(25 * U))
    paint(img, m, W / 2, by + 24 * U, NAVY, 0.85)

    img += np.random.default_rng(4).standard_normal((H, W, 1)).astype(np.float32) * 0.008
    return np.clip(img, 0, 1)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    a = build(W, H, story)
    p = os.path.join(OUT, f'split_{tag}.png')
    Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)

print('->', OUT)
