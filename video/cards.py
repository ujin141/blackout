"""
인스타 카드뉴스 (1080x1350). DJ 1명당 5장.
python cards.py  →  out/cards/aros_1..5.png, lynn_1..5.png
"""
import os
import glob
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, 'assets', 'img')
BRAND = os.path.join(HERE, 'assets', 'Michroma-Regular.ttf')
from fonts import KR, KRB          # OS별 한글 폰트 (video/fonts.py)

W, H = 1080, 1350
OUT = os.path.join(HERE, 'out', 'cards')
os.makedirs(OUT, exist_ok=True)

MARGIN = 90
HANDLE = '@blackoutcrew_official'
SLOGAN = 'WHERE THE LIGHTS FADE, THE MUSIC TAKES OVER.'


# ── 기본 도구 ──────────────────────────────────────────────
def load_alpha(name, height):
    im = Image.open(os.path.join(IMG, name)).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    im = im.resize((w, height), Image.LANCZOS)
    return np.asarray(im).astype(np.float32)[..., 3] / 255.0


def blit_photo(dst, name, height, cx, bottom, contrast=1.15, bright=1.0):
    """누끼 사진을 실제 픽셀로 합성 (알파만 쓰는 blit과 다름)"""
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
    sub_a = al[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    sub_c = g[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    dst[sy0:sy1, sx0:sx1] = dst[sy0:sy1, sx0:sx1] * (1 - sub_a) + sub_c * sub_a


def blit(dst, m, cx, cy, a=1.0, glow=0.0, glow_r=24, anchor='c'):
    if abs(a) < 0.003:
        return
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
        x0 = int(cx) if anchor == 'l' else int(cx - w / 2)
        y0 = int(cy - h / 2)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        dst[sy0:sy1, sx0:sx1] += lm[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * (a * la)


def tmask(text, path, size, track_em=0.0):
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 60, asc + desc + 40), 0)
    d = ImageDraw.Draw(im)
    x = 30
    for c, wc in zip(text, ws):
        d.text((x, 20), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    if not len(xs):
        return np.zeros((1, 1), np.uint8)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    lo, hi = 8, 300
    for _ in range(20):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def beam(dst, x, angle, spread, a):
    if a <= 0.004:
        return
    layer = np.zeros((H // 2, W // 2), np.float32)
    L = H
    pts = np.array([[x / 2, -30], [x / 2 - spread / 2 + np.sin(angle) * L, L],
                    [x / 2 + spread / 2 + np.sin(angle) * L, L]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    layer *= (np.linspace(1, 0, H // 2, dtype=np.float32) ** 1.4)[:, None]
    layer = cv2.GaussianBlur(layer, (0, 0), 20)
    dst += cv2.resize(layer, (W, H))[..., None] * a


def haze(dst, x, y, r, a):
    yy, xx = np.mgrid[0:H:3, 0:W:3].astype(np.float32)
    g = np.clip(1 - np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r, 0, 1) ** 2.2
    dst += cv2.resize(g, (W, H))[..., None] * a


def floor(dst, a, top=0.62):
    g = np.zeros((H, 1), np.float32)
    y0 = int(H * top)
    g[y0:, 0] = np.linspace(0, 1, H - y0) ** 1.6
    dst += g[..., None] * a


_VIG = None


RULE_Y = 1058          # 피드의 모든 1080x1350 자산이 공유하는 가로선 높이.
                       # feed.py · feed2.py · feed_row.py · feed_grid.py 와 같은 값이어야
                       # 그리드에서 옆 칸과 선이 이어진다. 건드리지 말 것.


def finish(img, vig=1.0):
    global _VIG
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt(((xx - W / 2) / (W * 0.78)) ** 2 + ((yy - H / 2) / (H * 0.78)) ** 2)
        _VIG = np.clip(1.12 - d ** 1.9, 0, 1)[..., None]
    img = img * ((1 - vig) + vig * _VIG)
    rng = np.random.default_rng(9)
    img = img + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.018
    # 선은 비네팅 뒤에 그린다. 앞에 그리면 가장자리가 어두워져서
    # 옆 칸과 붙였을 때 이어지지 않고 끊긴 점선처럼 보인다.
    img[RULE_Y:RULE_Y + 2, 0:W] += 0.30
    img[RULE_Y + 1:RULE_Y + 2, int(W * 0.30):int(W * 0.70)] += 0.18
    return np.clip(img, 0, 1)


def stage_bg(seed=0):
    """무대 조명 배경"""
    img = np.zeros((H, W, 3), np.float32)
    rng = np.random.default_rng(seed)
    for i in range(4):
        beam(img, W * (0.12 + i * 0.25) + rng.integers(-70, 70),
             (rng.random() - 0.5) * 0.4, 90 + i * 14, 0.10 + rng.random() * 0.07)
    haze(img, W * 0.5, H * 0.4, W * 0.85, 0.05)
    floor(img, 0.10)
    return img


def brandmark(img, y=MARGIN + 10):
    """좌상단 로고 + 우상단 핸들"""
    mk = load_alpha('logo-mark.png', 74)
    blit(img, mk, MARGIN, y, 0.95, glow=0.3, glow_r=14, anchor='l')
    wd = load_alpha('logo-blackout.png', 15)
    blit(img, wd, MARGIN + 66, y + 2, 0.9, glow=0.2, glow_r=8, anchor='l')
    h = tmask(HANDLE, BRAND, 17, 0.1)
    blit(img, h, W - MARGIN - h.shape[1], y, 0.5)


def footer(img, text=SLOGAN):
    m = tmask(text, BRAND, 15, 0.2)
    blit(img, m, W / 2, H - MARGIN + 6, 0.4)


def lines(img, rows, y0, font, size, gap, a=1.0, glow=0.35, track=0.0, align='c'):
    y = y0
    for r in rows:
        m = tmask(r, font, size, track)
        if align == 'l':
            blit(img, m, MARGIN, y, a, glow=glow, glow_r=18, anchor='l')
        else:
            blit(img, m, W / 2, y, a, glow=glow, glow_r=18)
        y += gap
    return y


def photo_card(path, focus=0.42, dark=0.62):
    """풀블리드 흑백 사진"""
    im = Image.open(path).convert('L')
    tw, th = W, H
    s = max(tw / im.width, th / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x0 = max(0, (im.width - tw) // 2)
    y0 = int(max(0, min(im.height - th, im.height * focus - th * 0.42)))
    im = im.crop((x0, y0, x0 + tw, y0 + th))
    a = np.asarray(im).astype(np.float32) / 255.0
    a = np.clip((a - 0.5) * 1.28 + 0.5, 0, 1) ** 1.18 * dark
    img = np.repeat(a[..., None], 3, axis=2)
    g = np.zeros((H, 1), np.float32)
    g[int(H * 0.42):, 0] = np.linspace(0, 1, H - int(H * 0.42)) ** 1.5
    img *= (1 - g[..., None] * 0.86)          # 하단 어둡게 (글자 자리)
    return img


# ── 카드 정의 ──────────────────────────────────────────────
def make(dj):
    name = dj['name']
    out = []

    # 1) 훅
    if dj.get('hook_bg') == 'stage':
        img = stage_bg(7)
        haze(img, W / 2, 420, W * 0.7, 0.06)
        img = np.clip(img, 0, 1)
        blit_photo(img, dj['cutout'], int(H * 0.82), W / 2, int(H * 0.86))
        g = np.zeros((H, 1), np.float32)
        g[int(H * 0.45):, 0] = np.linspace(0, 1, H - int(H * 0.45)) ** 1.5
        img *= (1 - g[..., None] * 0.9)
    else:
        img = photo_card(dj['photo'], dj['focus'])
    brandmark(img)
    y = H - MARGIN - 150
    for i, ln in enumerate(dj['hook']):
        m = tmask(ln, KRB, 58)
        blit(img, m, MARGIN, y + i * 80, 1.0, glow=0.3, glow_r=16, anchor='l')
    m = tmask('SWIPE', BRAND, 16, 0.35)
    blit(img, m, W - MARGIN - m.shape[1], H - MARGIN + 6, 0.55)
    out.append(finish(img, 0.55))

    # 2) 이름
    img = stage_bg(1)
    haze(img, W / 2, 420, W * 0.6, 0.07)
    img = np.clip(img, 0, 1)
    blit_photo(img, dj['cutout'], 850, W / 2, 950)
    brandmark(img)
    sz = fit(name, BRAND, W - MARGIN * 2 - 120, 0.08)
    m = tmask(name, BRAND, min(sz, 150), 0.08)
    blit(img, m, W / 2, 1075, 1.0, glow=0.5, glow_r=30)
    m = tmask(dj['role'], BRAND, 20, 0.4)
    blit(img, m, W / 2, 1160, 0.75)
    footer(img)
    out.append(finish(img))

    # 3~4) 정보 두 장
    for si, seed in ((dj['s3'], 2), (dj['s4'], 3)):
        img = stage_bg(seed)
        brandmark(img)
        m = tmask(si['label'], BRAND, 22, 0.42)
        blit(img, m, W / 2, 330, 0.55)
        rows = si['rows']
        cap = 72 if len(rows) <= 4 else 56
        sz = min(cap, fit(max(rows, key=len), KRB, W - MARGIN * 2 - 60))
        gap = int(sz * 1.6)
        y = int(H / 2 - (len(rows) - 1) * gap / 2) - 40
        for r in rows:
            m = tmask(r, KRB, sz)
            blit(img, m, W / 2, y, 1.0, glow=0.34, glow_r=20)
            y += gap
        if si.get('note'):
            m = tmask(si['note'], KR, 28)
            blit(img, m, W / 2, y + 30, 0.6)
        footer(img)
        out.append(finish(img))

    # 5) CTA
    img = stage_bg(4)
    haze(img, W / 2, 520, W * 0.7, 0.08)
    lock = load_alpha('logo-lockup.png', 520)
    blit(img, lock, W / 2, 520, 1.0, glow=0.45, glow_r=40)
    m = tmask('창립 멤버 모집 중', KRB, 52)
    blit(img, m, W / 2, 930, 1.0, glow=0.35, glow_r=20)
    m = tmask('DJ · PRODUCER · VISUAL · PHOTO · VIDEO', BRAND, 19, 0.22)
    blit(img, m, W / 2, 1010, 0.6)
    m = tmask(HANDLE, BRAND, 30, 0.12)
    blit(img, m, W / 2, 1130, 0.95, glow=0.3, glow_r=16)
    m = tmask('DM 주세요', KR, 26)
    blit(img, m, W / 2, 1190, 0.55)
    footer(img)
    out.append(finish(img))

    for i, im in enumerate(out, 1):
        p = os.path.join(OUT, f'{dj["key"]}_{i}.png')
        Image.fromarray((im * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)


AROS = dict(
    key='aros', name='AROS', role='DJ',
    photo=glob.glob(os.path.join(ROOT, 'AROS', '*_02.jpg'))[0],
    cutout='members/aros-cutout.png', focus=0.34,
    hook=['중학생 때 들은 노래 한 곡이', '이 사람을 부스에 앉혔다'],
    s3=dict(label='PLAYS', rows=['EDM', '바운스', '하우스', '하드']),
    s4=dict(label='PLAYED AT', rows=['상하이 클럽 MAX', '클럽 234', '성남 국빈관 나이트클럽']),
)

LYNN = dict(
    key='lynn', name='LYNN', role='DJ',
    photo=glob.glob(os.path.join(ROOT, 'Lynn', '*.jpg'))[0],
    cutout='members/lynn-cutout.png', focus=0.36,
    hook=['한 세트에', '장르가 여섯 개 있다'],
    s3=dict(label='PLAYS', rows=['EDM', '테크하우스', '하우스', '미니멀', '미니멀 바운스', '힙합']),
    s4=dict(label='RANGE', rows=['EDM부터 힙합까지', '플로어 보고 고른다']),
)

V = dict(
    key='v', name='V', role='DJ',
    photo=glob.glob(os.path.join(ROOT, 'V', '*.jpg'))[0],
    cutout='members/v-cutout.png', focus=0.42,
    hook=['장르를 가리지 않습니다', '음악의 길로 안내합니다'],
    s3=dict(label='PLAYS', rows=['힙합', '테크노', '하우스']),
    s4=dict(label='PLAYED AT', rows=['홍대 다다르다', '세인트 더 스위트 양양', '구디 별밤', '루미아르 청담'],
            note='현 홍대 다다르다 파트타임'),
)

TS = dict(
    key='ts', name='TS', role='DJ / DESIGNER',
    photo=glob.glob(os.path.join(ROOT, 'TS', '*.jpg'))[0],
    cutout='members/ts-cutout.png', focus=0.36,
    hook=['오픈덱에서 시작해', '무대를 늘려가는 중'],
    s3=dict(label='PLAYS', rows=['EDM', '딥 하우스', '개러지 하우스', 'K-POP', '시티팝']),
    s4=dict(label='PLAYED AT', rows=['업장 오픈덱', 'DJ 학원 수강생 파티', '학원 워크샵', '가평 빠지'],
            note='크루 디자인도 맡고 있습니다'),
)

if __name__ == '__main__':
    import sys
    who = dict(aros=AROS, lynn=LYNN, v=V, ts=TS)
    keys = sys.argv[1:] or ['aros', 'lynn', 'v', 'ts']
    for k in keys:
        make(who[k])
