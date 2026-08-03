"""
피드 한 줄(3칸)이 통째로 이어지는 세트.

    │ 멤버 │ 브랜드 │ 브랜드 │   ← 세 칸이 하나의 그림
    │ 멤버 │ 브랜드 │ 브랜드 │
     ↑ 여기가 카드뉴스 1번 슬라이드. 눌러서 열면 기존 카드뉴스가 이어진다.

한 줄을 3240x1350 파노라마로 그린 뒤 1080x1350 세 장으로 자른다.
가운데 칸은 오프닝 영상(릴스)의 커버로 쓸 수 있게 따로 한 장 더 뽑는다.

⚠ 이음새(x=1080, 2160)에는 아무것도 올리지 않는다. 인스타 그리드는 타일 사이가
   벌어져서 경계에 걸친 글자·가는 획은 잘려 사라진다.

python feed_row.py           전체
python feed_row.py demic     한 명만
"""
import os
import sys
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KR, KRB

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T, SAFE_B = 135, 1215
RULE_Y = 1058                    # 세 칸을 관통하는 가로선
SEAM_CLEAR = 90                  # 이음새 좌우로 비워 두는 폭
OUT = os.path.join(HERE, 'out', 'feed_row')
os.makedirs(OUT, exist_ok=True)


# ── 줄 정의 ────────────────────────────────────────────────
ROWS = [
    dict(key='demic', name='DEMIC', cut='members/demic-cutout.png', focus=0.30,
         mid='NIGHT', right='SEOUL', sub='대학 축제부터 호텔 풀파티까지', reel=True),
    dict(key='v', name='V', cut='members/v-cutout.png', focus=0.42,
         mid='HOUSE', right='TECHNO', sub='장르를 가리지 않습니다'),
    dict(key='lynn', name='LYNN', cut='members/lynn-cutout.png', focus=0.36,
         mid='MINIMAL', right='BOUNCE', sub='한 세트에 장르가 여섯 개'),
    dict(key='aros', name='AROS', cut='members/aros-cutout.png', focus=0.34,
         mid='ENERGY', right='HARD', sub='무대 위에서 돌려주는 에너지'),
    dict(key='ts', name='TS', cut='members/ts-cutout.png', focus=0.36,
         mid='DEEP', right='CITY POP', sub='오픈덱에서 시작해'),
]


# ── 도구 ───────────────────────────────────────────────────
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


def blit_photo(dst, name, height, cx, bottom, contrast=1.2, bright=0.98):
    """누끼 사진을 실제 픽셀로 합성"""
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    im = im.resize((w, height), Image.LANCZOS)
    arr = np.asarray(im).astype(np.float32) / 255.0
    rgb, al = arr[..., :3], arr[..., 3:4]
    g = (rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114)[..., None]
    g = np.clip((g - 0.5) * contrast + 0.5, 0, 1) * bright
    g = np.repeat(g, 3, axis=2)
    x0, y0 = int(cx - w / 2), int(bottom - height)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + height)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sa = al[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    sc = g[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    dst[sy0:sy1, sx0:sx1] = dst[sy0:sy1, sx0:sx1] * (1 - sa) + sc * sa


def logo_alpha(name, height):
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    return np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3] / 255.0


def beam(dst, x, spread, angle, a):
    layer = np.zeros((H // 2, W // 2), np.float32)
    L = H
    pts = np.array([[x / 2, -40],
                    [x / 2 - spread / 2 + np.sin(angle) * L, L],
                    [x / 2 + spread / 2 + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= (np.linspace(1, 0, H // 2, dtype=np.float32) ** 1.35)[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 26)
    dst += cv2.resize(layer, (W, H))[..., None] * a


def haze(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H:4, 0:W:4].astype(np.float32)
    g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r, 0, 1) ** 2.2
    dst += cv2.resize(g, (W, H))[..., None] * a


def build(row):
    img = np.zeros((H, W, 3), np.float32)

    # 세 칸을 가로지르는 빛 — 이어짐의 핵심
    for x, sp, an, al in [(150, 150, 0.14, 0.085), (620, 120, -0.05, 0.070),
                          (1080, 160, 0.0, 0.075), (1560, 120, 0.10, 0.070),
                          (2160, 150, 0.0, 0.075), (2620, 120, -0.10, 0.070),
                          (3090, 150, -0.16, 0.085)]:
        beam(img, x, sp, an, al)
    haze(img, W * 0.5, H * 0.36, W * 0.40, 0.055)

    # 바닥
    g = np.zeros((H, 1), np.float32)
    g[int(H * 0.66):, 0] = np.linspace(0, 1, H - int(H * 0.66)) ** 1.7
    img += g[..., None] * 0.05

    # ── 1칸: 멤버 ─────────────────────────────────────────
    blit_photo(img, row['cut'], int(H * 0.80), TW * 0.5, int(H * 0.96))
    # 인물 아래를 눌러 글자 자리를 만든다
    gg = np.zeros((H, 1), np.float32)
    gg[int(H * 0.55):, 0] = np.linspace(0, 1, H - int(H * 0.55)) ** 1.3
    img[:, :TW] *= (1 - gg[..., None] * 0.88)

    # 글자 수가 적은 이름(V, TS)이 과하게 커지지 않게 상한을 둔다
    s = min(fit(row['name'], BRAND, 620, 0.14), 118)
    m = tmask(row['name'], BRAND, s, 0.14)
    blit(img, m, TW * 0.5, 880, 1.0, glow=0.35, glow_r=26)
    m = tmask(row['sub'], KRB, 34)
    blit(img, m, TW * 0.5, 975, 0.62, glow=0.2, glow_r=14)

    # ── 2칸: 가운데 (릴스 커버로도 쓰는 칸) ────────────────
    lock = logo_alpha('logo-mark.png', 420)
    blit(img, lock, TW * 1.5, 560, 1.0, glow=0.45, glow_r=48)
    s = fit(row['mid'], BRAND, 700, 0.16)
    m = tmask(row['mid'], BRAND, s, 0.16)
    blit(img, m, TW * 1.5, 880, 0.92, glow=0.32, glow_r=24)

    # ── 3칸: 오른쪽 ───────────────────────────────────────
    s = fit(row['right'], BRAND, 720, 0.14)
    m = tmask(row['right'], BRAND, s, 0.14)
    blit(img, m, TW * 2.5, 640, 0.95, glow=0.34, glow_r=26)
    m = tmask('BLACKOUT CREW', BRAND, 26, 0.32)
    blit(img, m, TW * 2.5, 880, 0.5)

    # 세 칸을 관통하는 가로선 — 끝에서 끝까지.
    # 안쪽으로 들여 그으면 잘랐을 때 1번 칸은 왼쪽만, 3번 칸은 오른쪽만 비어 보인다.
    img[RULE_Y:RULE_Y + 2, 0:W] += 0.30
    img[RULE_Y + 1:RULE_Y + 2, int(W * 0.34):int(W * 0.66)] += 0.22

    # 가로선 아래 — 각 칸 안에서 끝난다
    m = tmask('@BLACKOUTCREW_OFFICIAL', BRAND, 22, 0.16)
    blit(img, m, TW * 0.5, 1140, 0.6)
    m = tmask('SEOUL · SINCE 2026', BRAND, 22, 0.24)
    blit(img, m, TW * 1.5, 1140, 0.55)
    m = tmask('MUSIC · CONTENT · COMMUNITY', BRAND, 21, 0.18)
    blit(img, m, TW * 2.5, 1140, 0.55)

    # 마감
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((xx - W / 2) / (W * 0.66)) ** 2 + ((yy - H / 2) / (H * 0.86)) ** 2)
    img *= np.clip(1.1 - d ** 2.0, 0, 1)[..., None]
    img += np.random.default_rng(8).standard_normal((H, W, 1)).astype(np.float32) * 0.015
    return np.clip(img, 0, 1)


def render(row):
    full = Image.fromarray((build(row) * 255).astype(np.uint8))
    k = row['key']
    full.save(os.path.join(OUT, f'{k}_full.png'), optimize=True)
    for i in range(3):
        p = os.path.join(OUT, f'{k}_{i + 1}.png')
        full.crop((i * TW, 0, (i + 1) * TW, TH)).save(p, optimize=True)
        print(p, '← 카드뉴스 1번 슬라이드' if i == 0 else
                 ('← 릴스 커버로 지정' if (i == 1 and row.get('reel')) else ''))


if __name__ == '__main__':
    keys = [k.lower() for k in sys.argv[1:]]
    for r in ROWS:
        if not keys or r['key'] in keys:
            render(r)
    print('->', OUT)
