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
from fonts import KR as KRF          # 정보 블록의 한글 값에 쓴다
OUT = os.path.join(HERE, 'out', 'poster')
os.makedirs(OUT, exist_ok=True)

WHITE = np.array([1.0, 1.0, 1.0], np.float32)
BLACK = np.array([0.0, 0.0, 0.0], np.float32)

# 두 사진 모두 CC0. club 은 아래쪽에 관객 얼굴이 다 나오므로
# 얼굴이 없는 위 34%(디스코볼·연기·트러스)만 쓴다 — CLUB_SAFE 를 그대로 쓸 것.
POOL = os.path.join(STOCK, 'pool-cc0.jpg')
CLUB = os.path.join(STOCK, 'club-cc0.jpg')
CLUB_SAFE = dict(focus=0.16, zoom=2.9)      # 값은 올리기만. 낮추면 얼굴이 딸려 들어온다.

# ── 인물 배경 사진 ────────────────────────────────────────
# `pool-model.jpg` · `pool-model-2.jpg` · `pool-model-3.jpg` 를 넣어 두면 골라 쓴다.
# 하나도 없으면 빈 수영장 사진으로 돌아가므로 코드는 항상 돈다.
#
#     python poster_real.py                    1번 사진
#     BLACKOUT_HERO=2 python poster_real.py    2번 사진 → real_h2_story.png
#
# **인물이 주인공인 사진은 가운데에 그래픽이 있는 판과 부딪힌다** —
# 위·아래에만 글자가 있는 판(real · ko · night)에서 쓸 것.
#
# 크롭은 사진마다 다르다. 세로 전신은 그대로, 가로 사진은 확대해서 인물만 잡는다 —
# 가로 사진을 세로 판에 그냥 넣으면 좌우가 잘려 무슨 그림인지 모르게 된다.
# 크롭은 후보를 나란히 놓고 골랐다(눈대중 금지).
#   2번은 **가로 사진**이라 세로 판에서 좌우가 크게 잘린다 — 얼굴·상반신만 잡는다.
#   3번은 세로라 위에 물이 남게 잡아 헤드라인 자리를 비운다.
_MODELS = [('pool-model.jpg',   dict(focus=0.40, zoom=1.00, offx=0.00)),
           ('pool-model-2.jpg', dict(focus=0.42, zoom=2.40, offx=-0.15)),
           ('pool-model-3.jpg', dict(focus=0.30, zoom=1.35, offx=0.00))]

HEROES = [(os.path.join(STOCK, f), c) for f, c in _MODELS
          if os.path.exists(os.path.join(STOCK, f))]

_N = max(1, int(os.environ.get('BLACKOUT_HERO', '1')))
if HEROES:
    HERO, HERO_CROP = HEROES[min(_N, len(HEROES)) - 1]
    HERO_TAG = '' if _N <= 1 else f'_h{_N}'
else:
    HERO, HERO_CROP, HERO_TAG = POOL, dict(focus=0.62, zoom=1.25), ''


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


def tmask_bl(text, path, size, track_em=0.0):
    """마스크와 함께 **윗변에서 베이스라인까지의 거리**를 돌려준다.

    라벨(영문 대문자)과 값(한글)을 같은 y 에 가운데 맞추면 한 줄로 안 읽힙니다 —
    글자마다 위아래로 튀어나온 정도가 달라서 각자 다른 높이에 뜹니다.
    베이스라인을 맞춰야 비로소 한 줄이 됩니다."""
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
    m = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    return m, (60 + asc) - ys.min()


def paint_bl(dst, pair, x, y_base, color=WHITE, a=1.0, anchor='l'):
    """베이스라인 y 에 맞춰 그린다. pair 는 tmask_bl() 의 반환값."""
    m, base = pair
    paint(dst, m, x, y_base - base, color=color, a=a, anchor=anchor, valign='t')


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


def duotone(path, W, H, shadow, light, contrast=1.25, keep=0.10, focus=0.5, zoom=1.0,
            offx=0.0):
    """명암만 남기고 두 색 사이로 다시 칠한다.
    색조(HSV)를 돌리면 원본 색이 남아 엉뚱한 색이 튄다 — 반드시 이걸 쓸 것.
    zoom 을 올리면 더 확대해 잘라낸다. 사진의 일부만 쓰고 싶을 때."""
    im = Image.open(path).convert('RGB')
    s = max(W / im.width, H / im.height) * zoom
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    # offx 는 가로 크롭 위치. 0 이 가운데, +면 오른쪽을 본다(=피사체가 왼쪽으로 간다).
    # 인물 사진에서 사람이 화면 가운데 오면 앞의 글자와 정면으로 부딪혀서 필요하다.
    x0 = int(np.clip((im.width - W) * (0.5 + offx), 0, max(0, im.width - W)))
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
              cols=2, ksize=15, vsize=19, a=1.0, program=(), prog_color=None):
    """타임테이블. 여덟 줄을 한 줄씩 쌓으면 포스터 절반을 먹어서 두 칸으로 접는다.

    시간은 오른쪽 끝을 맞춰야 세로로 읽힌다 — 왼쪽만 맞추면 자릿수가 달라
    들쭉날쭉해 보인다. 여기서는 24시간제라 자릿수가 같아 왼쪽 정렬로 충분하다."""
    per = (len(rows) + cols - 1) // cols
    cw = (x1 - x0) / cols
    for i, (s, e, name) in enumerate(rows):
        cx = x0 + cw * (i // per)
        y = y0 + step * (i % per)
        # 시간과 이름을 각각 가운데 맞추면 크기가 달라 한 줄로 안 읽힌다 —
        # 베이스라인을 맞춘다. 표에서 이 한 끗이 제일 크게 보인다.
        kb = tmask_bl(f'{s}–{e}', BRAND, int(ksize * V), 0.10)
        vb = tmask_bl(name, BRAND, int(vsize * V), 0.08)
        yb = y + vb[0].shape[0] * 0.5
        paint_bl(img, kb, cx, yb, color=key_color, a=a * 0.8)
        # 프로그램(솔로파티)은 DJ 가 아니다. 같은 색이면 DJ 이름으로 읽힌다.
        c = (prog_color if (name in program and prog_color is not None) else val_color)
        paint_bl(img, vb, cx + cw * 0.46, yb, color=c, a=a)


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


def info_block(img, x, y, width, V, key_color, val_color, head_color=None,
               head=34, key=15, val=21, step=None, kw=0.17, rules=True, a=1.0):
    """행사 정보 네 줄. **형식은 `event.INFO` 가 정한다** — 여기서 순서를 바꾸지 않는다.

    첫 줄(날짜)은 라벨이 없고 크게, 나머지는 라벨 + 값 두 열입니다.
    라벨과 값은 크기가 달라서 가운데를 맞추면 한 줄로 안 읽힙니다 —
    **베이스라인을 맞춥니다**(표에서 이 한 끗이 제일 크게 보입니다).

    돌려주는 값은 블록의 아래 y. 다음 요소를 여기서 이어 내리면
    사이즈가 달라져도 발치가 안 겹칩니다."""
    import event as _EV
    head_color = head_color if head_color is not None else val_color
    step = step if step is not None else 46 * V
    yb = y
    for i, (k, v) in enumerate(_EV.INFO):
        if not k:                                     # 날짜 줄 — 라벨 없이 크게
            paint_bl(img, tmask_bl(v, BRAND, int(head * V), 0.16), x, yb,
                     color=head_color, a=a)
            yb += step * 1.28
            if rules:
                rule(img, yb - step * 0.62, x, x + width, val_color, 0.22 * a,
                     max(1, int(2 * V)))
            continue
        paint_bl(img, tmask_bl(k, BRAND, int(key * V), 0.24), x, yb,
                 color=key_color, a=0.95 * a)
        paint_bl(img, tmask_bl(v, KRF, int(val * V), 0.01), x + width * kw, yb,
                 color=val_color, a=a)
        if rules and i < len(_EV.INFO) - 1:
            rule(img, yb + step * 0.28, x, x + width, val_color, 0.10 * a,
                 max(1, int(1 * V)))
        yb += step
    return yb


def grain(img, amt, seed=3):
    img += np.random.default_rng(seed).standard_normal(img.shape[:2] + (1,)).astype(np.float32) * amt


def save(img, name):
    # 사진을 바꿔 뽑으면 이름이 갈려야 덮어쓰지 않는다.
    # 여기 한 곳만 고치면 판 전체가 따라온다.
    p = os.path.join(OUT, f'{name}{HERO_TAG}.png')
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(p)
    return p


SIZES = {'feed': (1080, 1350, False), 'story': (1080, 1920, True)}
