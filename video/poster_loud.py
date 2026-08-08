"""
풀파티 × 솔로파티 — 직설 버전.

⚠ 브랜드 흑백 규칙을 일부러 깬 포스터다. (사용자가 명시적으로 요청)
   흑백으로는 "풀파티"가 즉각적으로 안 읽힌다. 물색과 햇빛이 곧 정보다.
   크루 브랜드 포스터는 poster_solo.py / poster_ad.py 를 쓸 것.

한 번에 읽히게 만드는 장치
    물색 그라데이션 + 물결   → 물이 있는 자리
    강한 햇빛              → 낮
    겹친 튜브 두 개         → 풀파티이면서, 혼자 온 둘이 만난다는 뜻
    두꺼운 글자 + 외곽선     → 작은 화면에서도 안 뭉갠다
    노란 띠 CTA            → 시선이 마지막에 닿는 곳

python poster_loud.py  →  out/poster/loud_{feed,story}.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
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

CYAN   = np.array([0.20, 0.80, 0.94], np.float32)
DEEP   = np.array([0.02, 0.16, 0.52], np.float32)
SUN    = np.array([1.00, 0.93, 0.48], np.float32)
YELLOW = np.array([1.00, 0.84, 0.10], np.float32)
NAVY   = np.array([0.02, 0.11, 0.30], np.float32)
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
        d.text((x, pad), c, font=f, fill=255,
               stroke_width=stroke, stroke_fill=255)
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


def paint(dst, m, cx, cy, color, a=1.0, shadow=0.0, sh_off=(0, 0)):
    """마스크를 색으로 칠한다"""
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
        put(cv2.GaussianBlur(m, (0, 0), 6), NAVY, shadow, sh_off[0], sh_off[1])
    put(m, color, a, 0, 0)


def water(W, H):
    """물색 그라데이션 — 위는 얕고 밝게, 아래는 깊고 진하게"""
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None] ** 1.15
    return CYAN * (1 - t) + DEEP * t


def caustics(dst, a):
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    x, y = xx * 0.0105, yy * 0.0105
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37)) +
         0.8 * np.sin((x + y) * 0.85))
    lines = np.clip(1 - np.abs(np.sin(f * 1.7)) * 6.0, 0, 1) ** 1.2
    lines = cv2.GaussianBlur(lines, (0, 0), 1.1)
    lines = cv2.resize(lines, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    dst += lines * a * WHITE


def sun(dst, cx, cy, r, a):
    H, W = dst.shape[:2]
    yy, xx = np.mgrid[0:H:3, 0:W:3].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    g = cv2.resize(np.clip(1 - d, 0, 1) ** 2.0, (W, H),
                   interpolation=cv2.INTER_LINEAR)[..., None]
    dst += g * a * SUN


def tube(dst, cx, cy, r, th, color, a=1.0):
    """튜브 — 풀파티라는 신호. 두껍게 그려야 튜브로 보인다."""
    H, W = dst.shape[:2]
    L = np.zeros((H, W), np.float32)
    cv2.circle(L, (int(cx), int(cy)), int(r), 1.0, int(th), cv2.LINE_AA)
    sh = cv2.GaussianBlur(L, (0, 0), 9)
    dst[:] = dst * (1 - sh[..., None] * 0.35 * a) + NAVY * (sh[..., None] * 0.35 * a)
    dst[:] = dst * (1 - L[..., None] * a) + color * (L[..., None] * a)
    # 안쪽에 얇은 하이라이트 — 부풀어 보이게
    Hl = np.zeros((H, W), np.float32)
    cv2.circle(Hl, (int(cx), int(cy)), int(r - th * 0.28), 1.0, max(1, int(th * 0.16)), cv2.LINE_AA)
    dst[:] = dst * (1 - Hl[..., None] * 0.45 * a) + WHITE * (Hl[..., None] * 0.45 * a)


def pill(dst, text, cx, cy, U, fill=YELLOW, fg=NAVY):
    m = tmask(text, KRB, int(27 * U))
    w, h = m.shape[1], m.shape[0]
    pw, ph = w + int(56 * U), h + int(34 * U)
    L = np.zeros(dst.shape[:2], np.float32)
    cv2.rectangle(L, (int(cx - pw / 2), int(cy - ph / 2)),
                  (int(cx + pw / 2), int(cy + ph / 2)), 1.0, -1, cv2.LINE_AA)
    sh = cv2.GaussianBlur(L, (0, 0), 7)
    dst[:] = dst * (1 - sh[..., None] * 0.30) + NAVY * (sh[..., None] * 0.30)
    dst[:] = dst * (1 - L[..., None]) + fill * L[..., None]
    paint(dst, m, cx, cy, fg, 1.0)
    return pw


def build(W, H, story=False):
    U = H / 1350.0
    img = water(W, H).repeat(W, axis=1) if False else np.repeat(water(W, H), W, axis=1)
    img = np.ascontiguousarray(img)

    sun(img, W * 0.80, -H * 0.02, W * 1.05, 0.55)
    caustics(img, 0.30)

    # ── 튜브 두 개 — 풀파티 + 둘이 만난다 ──────────────────
    CY = H * (0.285 if story else 0.300)
    R = W * 0.235
    tube(img, W / 2 - W * 0.145, CY, R, 34 * U, WHITE, 1.0)
    tube(img, W / 2 + W * 0.145, CY, R, 34 * U, YELLOW, 1.0)

    # ── 타이틀 ────────────────────────────────────────────
    st = max(2, int(9 * U))
    m = tmask('POOL PARTY', KRB, fit('POOL PARTY', KRB, W * 0.86, 0.02, st), 0.02, st)
    paint(img, m, W / 2, CY - 96 * U, WHITE, 1.0, shadow=0.55, sh_off=(0, int(7 * U)))
    m = tmask('SOLO PARTY', KRB, fit('SOLO PARTY', KRB, W * 0.86, 0.02, st), 0.02, st)
    paint(img, m, W / 2, CY + 96 * U, YELLOW, 1.0, shadow=0.55, sh_off=(0, int(7 * U)))
    m = tmask('×', KRB, int(96 * U), 0, st)
    paint(img, m, W / 2, CY, WHITE, 1.0, shadow=0.5, sh_off=(0, int(5 * U)))

    # ── 혼자 와도 된다 — 문턱 낮추기 ──────────────────────
    m = tmask('혼자 와도 됩니다', KRB, int(58 * U))
    paint(img, m, W / 2, H * 0.500, YELLOW, 1.0, shadow=0.6, sh_off=(0, int(6 * U)))
    m = tmask('어차피 다 혼자 옵니다', KR, int(30 * U))
    paint(img, m, W / 2, H * 0.545, WHITE, 0.95, shadow=0.4, sh_off=(0, int(3 * U)))

    # ── 날짜 ──────────────────────────────────────────────
    # 날짜는 폭에 맞추되 상한을 둔다. 짧은 문구가 들어오면 제목보다 커져 버린다.
    m = tmask(DATE_KR, KRB, min(int(58 * U), fit(DATE_KR, KRB, W * 0.80)))
    paint(img, m, W / 2, H * 0.628, WHITE, 1.0, shadow=0.55, sh_off=(0, int(5 * U)))
    m = tmask(f'{TIME_KR}   ·   {PLACE}', KRB, int(26 * U))
    paint(img, m, W / 2, H * 0.676, WHITE, 0.95, shadow=0.4, sh_off=(0, int(3 * U)))

    # ── 정보 알약 ─────────────────────────────────────────
    py = H * 0.748
    sizes = [tmask(t, KRB, int(27 * U)).shape[1] + int(56 * U) for t in PILLS]
    gap = int(20 * U)
    total = sum(sizes) + gap * (len(PILLS) - 1)
    x = W / 2 - total / 2
    for t, sw in zip(PILLS, sizes):
        pill(img, t, x + sw / 2, py, U)
        x += sw + gap

    # ── 가격 · 라인업 ─────────────────────────────────────
    m = tmask(PRICE, KRB, int(34 * U))
    paint(img, m, W / 2, H * 0.814, WHITE, 1.0, shadow=0.5, sh_off=(0, int(4 * U)))
    m = tmask(LINEUP, KRB, int(fit(LINEUP, KRB, W * 0.82, 0.04)), 0.04)
    paint(img, m, W / 2, H * 0.860, WHITE, 0.95, shadow=0.4, sh_off=(0, int(3 * U)))

    # ── CTA 띠 ────────────────────────────────────────────
    by = H * 0.930
    bh = 120 * U
    img[int(by - bh / 2):int(by + bh / 2)] = YELLOW
    m = tmask(CTA, KRB, int(40 * U))
    paint(img, m, W / 2, by - 18 * U, NAVY, 1.0)
    m = tmask(HANDLE, KRB, int(26 * U))
    paint(img, m, W / 2, by + 26 * U, NAVY, 0.85)

    img += np.random.default_rng(4).standard_normal((H, W, 1)).astype(np.float32) * 0.010
    return np.clip(img, 0, 1)


for tag, (W, H, story) in {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}.items():
    a = build(W, H, story)
    p = os.path.join(OUT, f'loud_{tag}.png')
    Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)

print('->', OUT)
