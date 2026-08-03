"""
인스타 피드 열 맞추기용 브랜드 타일 세트 (1080x1350 × 10장).

배치 목표 — 왼쪽 열에 멤버 카드뉴스, 나머지 두 칸은 브랜드 타일.
    │ 멤버 │ 브랜드 │ 브랜드 │
    │ 멤버 │ 브랜드 │ 브랜드 │

올리는 순서: brand_01 → brand_02 → 멤버1 → brand_03 → brand_04 → 멤버2 → ...
(인스타는 최신이 왼쪽 위라, 3개마다 멤버를 올리면 멤버가 같은 열에 쌓인다)

python feed_grid.py  →  out/feed_grid/brand_01.png ~ brand_10.png
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KRB                 # OS별 한글 폰트

W, H = 1080, 1350
SAFE_T, SAFE_B = 135, 1215            # 프로필 그리드에서 잘리지 않는 구간
OUT = os.path.join(HERE, 'out', 'feed_grid')
os.makedirs(OUT, exist_ok=True)


# ── 도구 ───────────────────────────────────────────────────
def tmask(text, path, size, track_em=0.0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 80, asc + desc + 60), 0)
    d = ImageDraw.Draw(im)
    x = 40
    for c, wc in zip(text, ws):
        d.text((x, 30), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    lo, hi = 8, 400
    for _ in range(22):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def blit(dst, m, cx, cy, a=1.0, glow=0.0, glow_r=24):
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


def logo(dst, name, height, cx, cy, a=1.0, glow=0.4, glow_r=40):
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    al = np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3] / 255.0
    blit(dst, al, cx, cy, a, glow=glow, glow_r=glow_r)


def beam(dst, x, spread, angle, a):
    layer = np.zeros((H // 2, W // 2), np.float32)
    L = H
    pts = np.array([[x / 2, -40],
                    [x / 2 - spread / 2 + np.sin(angle) * L, L],
                    [x / 2 + spread / 2 + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= (np.linspace(1, 0, H // 2, dtype=np.float32) ** 1.4)[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 24)
    dst += cv2.resize(layer, (W, H))[..., None] * a


def haze(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r, 0, 1) ** 2.2
    dst += cv2.resize(g, (W, H))[..., None] * a


def caustics(scale=1.0, seed=0):
    yy, xx = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    x, y = xx * 0.011 * scale + seed, yy * 0.011 * scale
    f = (np.sin(x * 1.4 + 1.6 * np.sin(y * 0.42)) +
         np.sin(y * 1.1 + 1.3 * np.sin(x * 0.37)) +
         0.8 * np.sin((x + y) * 0.85))
    lines = np.clip(1 - np.abs(np.sin(f * 1.7)) * 7.5, 0, 1) ** 1.4
    lines = cv2.GaussianBlur(lines, (0, 0), 1.3)
    return cv2.resize(lines, (W, H), interpolation=cv2.INTER_LINEAR)


RULE_Y = 1058          # 다른 피드 자산과 같은 높이. 그래야 옆 칸과 선이 이어진다.


def rule(dst, y, x0, x1, a, th=2):
    dst[y:y + th, int(x0):int(x1)] += a


def line(dst):
    """모든 타일이 공유하는 가로선"""
    dst[RULE_Y:RULE_Y + 2, 0:W] += 0.28
    dst[RULE_Y + 1:RULE_Y + 2, int(W * 0.30):int(W * 0.70)] += 0.20


def base(seed=0, lit=1.0):
    """공통 바탕 — 어둡게. 전 타일이 한 가족으로 보이게 값은 크게 안 바꾼다."""
    img = np.zeros((H, W, 3), np.float32)
    rng = np.random.default_rng(seed)
    for i in range(3):
        beam(img, 180 + i * 360 + rng.integers(-70, 70),
             110 + rng.integers(0, 70), (rng.random() - 0.5) * 0.3,
             (0.055 + rng.random() * 0.03) * lit)
    haze(img, W * 0.5, H * 0.38, W * 0.62, 0.045 * lit)
    g = np.zeros((H, 1), np.float32)
    g[int(H * 0.68):, 0] = np.linspace(0, 1, H - int(H * 0.68)) ** 1.7
    img += g[..., None] * 0.035 * lit
    return img


def finish(img, seed=3):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.70)) ** 2 + ((yy - H / 2) / (H * 0.82)) ** 2)
    img *= np.clip(1.1 - d ** 2.0, 0, 1)[..., None]
    img += np.random.default_rng(seed).standard_normal((H, W, 1)).astype(np.float32) * 0.015
    return np.clip(img, 0, 1)


def save(img, n, seed=3):
    out = finish(img, seed)
    line(out)                      # 비네팅 뒤에 그려야 가장자리까지 살아 있다
    p = os.path.join(OUT, f'brand_{n:02d}.png')
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)


def word_tile(n, word, sub, seed, mark=True):
    """큰 키워드 한 장 — 세트의 기본형"""
    img = base(seed)
    s = fit(word, BRAND, 830, 0.08)
    m = tmask(word, BRAND, s, 0.08)
    blit(img, m, W / 2, 640, 1.0, glow=0.36, glow_r=26)
    m = tmask(sub, BRAND, 22, 0.32)
    blit(img, m, W / 2, 830, 0.45)
    if mark:
        logo(img, 'logo-mark.png', 74, W / 2, SAFE_T + 60, 0.55, glow=0.22, glow_r=16)
    save(img, n, seed)


# ── 10장 ───────────────────────────────────────────────────
# 01 · 02 — 장르 한 쌍
word_tile(1, 'HOUSE', 'SOUND OF THE CREW', 11)
word_tile(2, 'TECHNO', 'SOUND OF THE CREW', 12)

# 03 — 엠블럼
img = base(13)
logo(img, 'logo-mark.png', 520, W / 2, 590, 1.0, glow=0.45, glow_r=48)
m = tmask('SEOUL · SINCE 2026', BRAND, 24, 0.32)
blit(img, m, W / 2, 970, 0.5)
save(img, 3, 13)

# 04 — 슬로건
img = base(14, lit=0.8)
for i, t in enumerate(('WHERE THE', 'LIGHTS FADE,')):
    s = fit(t, BRAND, 760, 0.06)
    m = tmask(t, BRAND, s, 0.06)
    blit(img, m, W / 2, 520 + i * 110, 0.9, glow=0.3, glow_r=22)
for i, t in enumerate(('THE MUSIC', 'TAKES OVER.')):
    s = fit(t, BRAND, 760, 0.06)
    m = tmask(t, BRAND, s, 0.06)
    blit(img, m, W / 2, 760 + i * 110, 0.55, glow=0.2, glow_r=18)
save(img, 4, 14)

# 05 · 06 — 키워드 한 쌍
word_tile(5, 'UNDERGROUND', 'EIGHT WORDS WE KEEP', 15)
word_tile(6, 'NIGHT', 'EIGHT WORDS WE KEEP', 16)

# 07 — 이 칸은 이미지가 아니라 오프닝 영상(릴스)을 올린다.
#      릴스는 그리드에서 커버 프레임으로 보이므로, 커버로 쓸 한 컷만 뽑아 둔다.
def opening_cover(src='blackout_opening3.mp4', t=19.6, n=7):
    path = os.path.join(HERE, 'out', src)
    if not os.path.exists(path):
        print(f'[skip] {src} 없음 — 먼저 opening3.py 로 렌더하세요')
        return
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ok, fr = cap.read()
    cap.release()
    if not ok:
        print('[skip] 프레임을 읽지 못했습니다')
        return
    im = Image.fromarray(fr[..., ::-1])            # BGR -> RGB
    # 1080x1920 세로 영상을 1080x1350 피드 비율로 가운데 잘라낸다
    top = max(0, (im.height - int(im.width * H / W)) // 2)
    im = im.crop((0, top, im.width, top + int(im.width * H / W))).resize((W, H), Image.LANCZOS)
    p = os.path.join(OUT, f'brand_{n:02d}_cover.png')
    im.save(p, optimize=True)
    print(p, '(릴스 커버로 지정할 이미지)')


opening_cover()

# 08 — 키워드
word_tile(8, 'MINIMAL', 'EIGHT WORDS WE KEEP', 18)

# 09 — 세 단어
img = base(19)
for i, t in enumerate(('ENERGY', 'UNITY', 'FUTURE')):
    s = fit(t, BRAND, 620, 0.14)
    m = tmask(t, BRAND, s, 0.14)
    blit(img, m, W / 2, 480 + i * 170, 0.95 - i * 0.16, glow=0.3, glow_r=22)
m = tmask('@BLACKOUTCREW_OFFICIAL', BRAND, 22, 0.16)
blit(img, m, W / 2, 1050, 0.5)
save(img, 9, 19)

# 10 — 모집 (한글)
img = base(20)
logo(img, 'logo-lockup.png', 300, W / 2, 470, 1.0, glow=0.4, glow_r=40)
m = tmask('창립 멤버 모집 중', KRB, 56)
blit(img, m, W / 2, 780, 1.0, glow=0.35, glow_r=22)
for i, t in enumerate(('DJ · PRODUCER', 'VISUAL · PHOTO', 'VIDEO · CONTENT')):
    m = tmask(t, BRAND, 22, 0.24)
    blit(img, m, W / 2, 880 + i * 48, 0.5)
m = tmask('DM', BRAND, 26, 0.3)
blit(img, m, W / 2, 1130, 0.7, glow=0.25, glow_r=14)
save(img, 10, 20)

print('->', OUT)
