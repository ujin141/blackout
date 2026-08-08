"""
포스터 공통 도구.

`poster_split.py`(A안)·`poster_club.py`(B안)는 각자 이 함수들을 복사해 갖고 있습니다.
그때는 두 개뿐이라 괜찮았는데 시안이 다섯으로 늘면서 한 곳만 고쳐도 나머지가
어긋나기 시작해 따로 뺐습니다. C·D·E안은 전부 여기서 가져다 씁니다.

A·B안은 이미 각자 값이 미세하게 조정돼 있어서 건드리지 않았습니다.
새 시안을 만들 때만 이 파일을 쓰세요.
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
OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

WHITE = np.array([1.0, 1.0, 1.0], np.float32)
BLACK = np.array([0.0, 0.0, 0.0], np.float32)

# 두 사진 모두 CC0. club 은 아래쪽에 관객 얼굴이 다 나오므로
# 얼굴이 없는 위 34%(디스코볼·연기·트러스)만 쓴다 — CLUB_SAFE 를 그대로 쓸 것.
POOL = os.path.join(STOCK, 'pool-cc0.jpg')
CLUB = os.path.join(STOCK, 'club-cc0.jpg')
CLUB_SAFE = dict(focus=0.16, zoom=2.9)      # 값은 올리기만. 낮추면 얼굴이 딸려 들어온다.


def tmask(text, path, size, track_em=0.0):
    """글자를 알파 마스크로. 자간은 em 비율."""
    f = ImageFont.truetype(path, size)
    tr = int(size * track_em)
    ws = [f.getlength(c) for c in text]
    total = int(sum(ws) + tr * max(len(text) - 1, 0))
    asc, desc = f.getmetrics()
    im = Image.new('L', (total + 140, asc + desc + 120), 0)
    d = ImageDraw.Draw(im)
    x = 70
    for c, wc in zip(text, ws):
        d.text((x, 60), c, font=f, fill=255)
        x += wc + tr
    a = np.asarray(im)
    ys, xs = np.where(a > 0)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()


def fit(text, path, target_w, track_em=0.0):
    """target_w 에 딱 맞는 글자 크기를 이분탐색으로 찾는다."""
    lo, hi = 8, 560
    for _ in range(20):
        mid = (lo + hi) / 2
        if tmask(text, path, int(mid), track_em).shape[1] > target_w:
            hi = mid
        else:
            lo = mid
    return int(lo)


def paint(dst, m, x, y, color=WHITE, a=1.0, anchor='l', valign='c'):
    """anchor l/r/c · valign t/c. 좌표는 기준점이지 좌상단이 아니다."""
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


def add(dst, layer, x0, y0, color, a):
    """빛은 덮지 말고 더한다. 덮으면 배경이 죽는다."""
    H, W = dst.shape[:2]
    h, w = layer.shape
    x0, y0 = int(x0), int(y0)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst[sy0:sy1, sx0:sx1] += layer[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None] * color * a


def glow(dst, m, x, y, color, a, r, anchor='l', valign='c'):
    """네온 후광. 그림자와 정반대 — 어둡게 까는 게 아니라 빛을 더한다."""
    pad = int(r * 2.4) + 8
    mp = cv2.copyMakeBorder(m.astype(np.float32) / 255.0, pad, pad, pad, pad,
                            cv2.BORDER_CONSTANT, value=0)
    g = cv2.GaussianBlur(mp, (0, 0), r)
    g /= max(g.max(), 1e-6)
    h, w = g.shape
    x0 = x - pad if anchor == 'l' else (x - w + pad if anchor == 'r' else x - w / 2)
    y0 = y - pad if valign == 't' else y - h / 2
    add(dst, g, x0, y0, color, a)


def outline(m, th):
    """속을 비운 테두리만 남긴다. 네온 튜브용."""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (th * 2 + 1, th * 2 + 1))
    return np.clip(cv2.dilate(m, k).astype(np.int16) - m.astype(np.int16), 0, 255).astype(np.uint8)


def rule(dst, y, x0, x1, color, a, th=1):
    y, th = int(y), max(1, int(th))
    dst[y:y + th, int(x0):int(x1)] = dst[y:y + th, int(x0):int(x1)] * (1 - a) + color * a


def vrule(dst, x, y0, y1, color, a, th=1):
    x, th = int(x), max(1, int(th))
    dst[int(y0):int(y1), x:x + th] = dst[int(y0):int(y1), x:x + th] * (1 - a) + color * a


def box(dst, x0, y0, x1, y1, color, a=1.0):
    dst[int(y0):int(y1), int(x0):int(x1)] = \
        dst[int(y0):int(y1), int(x0):int(x1)] * (1 - a) + color * a


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5, zoom=1.0):
    """명암만 남기고 두 색 사이로 다시 칠한다.
    색조(HSV)를 돌리면 원본 색이 남아 엉뚱한 색이 튄다 — 반드시 이걸 쓸 것.
    zoom 을 올리면 더 확대해 잘라낸다. 사진의 일부만 쓰고 싶을 때."""
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


def bloom(img, thr, sigma, amt, tint=WHITE):
    """밝은 곳을 번지게. 조명이 번져야 클럽처럼 보인다."""
    lum = img[..., 0] * .299 + img[..., 1] * .587 + img[..., 2] * .114
    g = cv2.GaussianBlur(np.clip(lum - thr, 0, 1) / max(1 - thr, 1e-3), (0, 0), sigma)
    img += g[..., None] * tint * amt


def logo(height):
    im = Image.open(os.path.join(IMG, 'logo-mark.png')).convert('RGBA')
    w = max(1, int(im.width * height / im.height))
    return np.asarray(im.resize((w, height), Image.LANCZOS)).astype(np.float32)[..., 3]


def timetable(img, rows, x0, x1, y0, step, V, key_color, val_color,
              cols=2, ksize=15, vsize=19, a=1.0):
    """타임테이블. 여덟 줄을 한 줄씩 쌓으면 포스터 절반을 먹어서 두 칸으로 접는다.

    시간은 오른쪽 끝을 맞춰야 세로로 읽힌다 — 왼쪽만 맞추면 자릿수가 달라
    들쭉날쭉해 보인다. 여기서는 24시간제라 자릿수가 같아 왼쪽 정렬로 충분하다."""
    per = (len(rows) + cols - 1) // cols
    cw = (x1 - x0) / cols
    for i, (s, e, name) in enumerate(rows):
        cx = x0 + cw * (i // per)
        y = y0 + step * (i % per)
        paint(img, tmask(f'{s}–{e}', BRAND, int(ksize * V), 0.10), cx, y, color=key_color, a=a * 0.8)
        paint(img, tmask(name, BRAND, int(vsize * V), 0.08), cx + cw * 0.46, y, color=val_color, a=a)


def partner_strip(img, paths, x0, x1, cy, h_max, color, a=0.9, gap_ratio=0.055,
                  align='l', names=(), name_font=None):
    """협업 브랜드 로고 줄.

    **높이를 맞추면 크기가 안 맞아 보입니다.** 로고마다 획이 굵고 가는 정도가 달라서,
    같은 높이로 놓으면 굵은 쪽이 훨씬 커 보입니다. 여기서는 **잉크 양(알파 합)** 을
    맞춥니다 — 눈이 느끼는 무게가 그거라서요. 그런 다음 높이 상한만 따로 겁니다.

    로고 색도 하나로 통일합니다. 흰색·금색이 섞이면 협찬 딱지처럼 보입니다.

    **정렬을 포스터와 맞춰야 합니다.** 포스터가 전부 좌측 기준선에 세워져 있는데
    로고만 가운데로 놓으면 따로 붙인 것처럼 겉돕니다 — `align='l'` 로 값 열에
    맞춰 세우고, 위에 라벨과 괘선을 두면 정보표의 한 줄로 읽힙니다."""
    if not paths and not names:
        return
    marks = []
    for p in paths:
        im = Image.open(p).convert('RGBA')
        arr = np.asarray(im).astype(np.float32)
        # 검정 바탕에 얹힌 로고가 대부분이라 알파가 없으면 밝기를 알파로 쓴다.
        # **알파의 최솟값으로 판단하면 안 된다** — 배경이 불투명한 PNG 라도
        # 가장자리 안티에일리어싱 한 픽셀 때문에 최솟값이 250 밑으로 떨어져,
        # 배경까지 알파 255 로 칠해진 흰 사각형이 나온다.
        # 실제로 뚫린 픽셀이 5% 넘게 있을 때만 알파를 믿는다.
        al = arr[..., 3]
        if (al < 16).mean() < 0.05:
            al = arr[..., :3].max(2)
        # 문턱을 낮게 잡으면 배경 글로우와 바닥 반사까지 경계 상자에 들어와
        # 로고가 실제보다 훨씬 커 보인다. 24 는 눈에 보이는 획만 남는 선.
        ys, xs = np.where(al > 24)
        if len(ys) == 0:
            continue
        # 은색·금색 로고는 중간 밝기가 넓게 깔려 있어 그대로 쓰면 뭉개진다.
        # 아래위를 잘라 대비를 세워야 작은 크기에서도 형태가 남는다.
        al = np.clip((al[ys.min():ys.max() + 1, xs.min():xs.max() + 1] - 40) / 130.0, 0, 1)
        marks.append(al)
    if not marks:
        return

    ink = np.array([m.sum() for m in marks], np.float32)
    target = float(np.median(ink))
    scale = np.sqrt(target / np.maximum(ink, 1e-6))
    # 높이 상한 — 세로로 긴 로고가 줄을 뚫고 나가지 않게
    for i, m in enumerate(marks):
        scale[i] = min(scale[i], h_max / m.shape[0])
    sizes = [(max(1, int(m.shape[1] * s)), max(1, int(m.shape[0] * s)))
             for m, s in zip(marks, scale)]

    # 이름만 넣는 브랜드 — 잉크 양으로 맞추면 글자는 로고보다 획이 적어
    # 터무니없이 커진다. 실제로 놓인 로고 높이를 기준으로 크기를 잡는다.
    if names and name_font:
        base = float(np.median([h for _, h in sizes])) if sizes else h_max
        for nm in names:
            m = tmask(nm, name_font, max(8, int(base * 0.46)), 0.02)
            marks.append(m.astype(np.float32) / 255.0)
            sizes.append((m.shape[1], m.shape[0]))

    gap = int((x1 - x0) * gap_ratio)
    total = sum(w for w, _ in sizes) + gap * (len(sizes) - 1)
    if total > x1 - x0:                                   # 줄을 넘치면 통째로 줄인다
        k = (x1 - x0) / total
        sizes = [(max(1, int(w * k)), max(1, int(h * k))) for w, h in sizes]
        gap = int(gap * k)
        total = sum(w for w, _ in sizes) + gap * (len(sizes) - 1)

    x = x0 if align == 'l' else (x1 - total if align == 'r'
                                 else x0 + ((x1 - x0) - total) / 2)
    for m, (w, h) in zip(marks, sizes):
        r = cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)
        paint(img, (r * 255).astype(np.uint8), x, cy, color=color, a=a)
        x += w + gap


def grain(img, amt, seed=3):
    img += np.random.default_rng(seed).standard_normal(img.shape[:2] + (1,)).astype(np.float32) * amt


def save(img, name):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)
    return p


SIZES = {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}
