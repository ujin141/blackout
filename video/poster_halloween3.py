"""
**BLACKOUT HALLOWEEN · 10.31 SAT — 사진판.** 피드 세 장(이어짐) + 스토리.

    python poster_halloween3.py   →  out/halloween/HW1.jpg HW2.jpg HW3.jpg · _할로윈격자.jpg · HW_스토리.jpg

## 왜 사진인가

그림(실루엣 · 클립아트)으로 그린 파티는 **가고 싶지 않다** — 싸 보이고, 거기 누가 있는지 모른다.
오고 싶게 만드는 건 **진짜 장면**이다. 딥하우즈 촬영본(9.21)에서 세 컷을 쓴다.

    HW1   믹서 위의 손     분장하고 오면 술 한 잔 서비스 (스티커)
    HW2   디제이 얼굴      COSTUME PARTY
    HW3   바에 모인 사람들  장소 · 라인업 곧 공개

할로윈 색으로 갈아입힌다 — 그림자는 보라, 빛은 주황. 원래 색을 반쯤 남겨 사진이 산다.

## 셋을 잇는 것

    HALLOWEEN   아홉 자를 아홉 칸에 (HAL / LOW / EEN). 주황 채움 · 검정 테 · 보라 그림자
    아래 띠      검정 띠가 세 장 바닥을 지난다. 날짜 · 코스튬 · 장소
    박쥐         몇 마리가 첫 장에서 셋째 장으로 날아간다

올리는 순서 HW3 → HW2 → HW1.
"""
import glob
import os
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fonts import KRB, KRD
from poster_halloween import OUT, bat_points
from poster_kit import bloom, grain
from poster_moon import LOGO, tracked, tracked_w

COND = 'C:/Windows/Fonts/bahnschrift.ttf'
SRC_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')
CACHE = os.path.join(OUT, '_src')
os.makedirs(CACHE, exist_ok=True)

ORANGE = (255, 122, 26)
ORANGE_HI = (255, 190, 90)
PURPLE = (92, 30, 150)
INK = (250, 246, 240)
BLACK = (8, 6, 10)

WORD = 'HALLOWEEN'
DATE = '10.31 SAT'


def cond(size, w='Bold Condensed'):
    f = ImageFont.truetype(COND, size)
    f.set_variation_by_name(w)
    return f


def kr(size, bold=True):
    return ImageFont.truetype(KRD if bold else KRB, size)


# ── 사진 ──────────────────────────────────────────────
def frame(n, t):
    """촬영본 한 장, 원본 해상도(세로 2160×3840) → 1080×1920."""
    p = os.path.join(CACHE, f'{n}_{t:.1f}.png')
    if not os.path.exists(p):
        f = glob.glob(os.path.join(SRC_DIR, 'drive-download-*', f'ta_{n}.MP4'))[0]
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.2f}', '-i', f, '-frames:v', '1',
                        '-vf', 'scale=1080:1920', p], check=True)
    return np.asarray(Image.open(p).convert('RGB'), np.float32) / 255.0


def grade(a, lift=1.45, keep=0.50):
    """할로윈 색. 그림자 보라 · 빛 주황. 원래 색을 keep 만큼 남긴다."""
    a = np.clip(a * lift, 0, 1)
    lum = a @ np.float32([0.299, 0.587, 0.114])
    l = np.clip(lum, 0, 1)[..., None] ** 0.85
    sh = np.float32([0.10, 0.02, 0.20])
    mid = np.float32([0.62, 0.14, 0.34])
    hi = np.float32([1.0, 0.62, 0.22])
    duo = np.where(l < 0.5, sh + (mid - sh) * (l / 0.5), mid + (hi - mid) * ((l - 0.5) / 0.5))
    out = a * keep + duo * (1 - keep)
    out = np.clip((out - 0.03) * 1.12, 0, 1)
    return out


def crop(a, y0, h):
    return a[y0:y0 + h]


# ── 글자 ──────────────────────────────────────────────
def text3d(text, f, stroke=8, shadow=(12, 12)):
    """주황 채움(위 밝게) · 검정 테 · 보라 그림자. 파티 포스터 제목."""
    probe = ImageDraw.Draw(Image.new('L', (8, 8)))
    x0, y0, x1, y1 = probe.textbbox((0, 0), text, font=f, stroke_width=stroke)
    w, h = x1 - x0 + shadow[0] + 8, y1 - y0 + shadow[1] + 8
    def mask(sw, off=(0, 0)):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).text((-x0 + 4 + off[0], -y0 + 4 + off[1]), text, font=f, fill=255,
                               stroke_width=sw, stroke_fill=255)
        return np.asarray(m, np.float32) / 255.0
    fill = mask(0)
    edge = mask(stroke)
    shad = mask(stroke, shadow)
    out = np.zeros((h, w, 4), np.float32)
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
    top, bot = np.float32(ORANGE_HI) / 255, np.float32(ORANGE) / 255
    grad = top * (1 - yy[..., None]) + bot * yy[..., None]
    # 윗면 반사 한 줄
    grad += np.exp(-((yy - 0.30) / 0.05) ** 2)[..., None] * 0.18
    out[..., :3] = np.float32(PURPLE) / 255 * shad[..., None]
    out[..., 3] = shad
    out[..., :3] = out[..., :3] * (1 - edge[..., None]) + np.float32(BLACK) / 255 * edge[..., None]
    out[..., 3] = np.maximum(out[..., 3], edge)
    out[..., :3] = out[..., :3] * (1 - fill[..., None]) + np.clip(grad, 0, 1) * fill[..., None]
    return out


def paste(pil, arr, x, y):
    pil.alpha_composite(Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), 'RGBA'), (int(x), int(y)))


def sticker(lines, r, rot=-12):
    """세일 스티커처럼 톱니 원. 주황 바탕 검정 글."""
    S = int(r * 2.4)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    n = 30
    pts = []
    for i in range(n * 2):
        a = np.pi * i / n
        rr = r if i % 2 == 0 else r * 0.90
        pts.append((c + np.cos(a) * rr, c + np.sin(a) * rr))
    d.polygon([(x + 8, y + 10) for x, y in pts], fill=(10, 6, 12, 180))
    d.polygon(pts, fill=ORANGE + (255,))
    d.ellipse([c - r * 0.80, c - r * 0.80, c + r * 0.80, c + r * 0.80], outline=BLACK + (255,), width=4)
    sizes = [int(r * 0.24), int(r * 0.40), int(r * 0.24)]
    hs = []
    for t, s in zip(lines, sizes):
        f = kr(s)
        hs.append((t, f, d.textbbox((0, 0), t, font=f)))
    total = sum(b[3] - b[1] for _, _, b in hs) + r * 0.05 * (len(hs) - 1)
    y = c - total / 2
    for t, f, b in hs:
        d.text((c - (b[2] - b[0]) / 2 - b[0], y - b[1]), t, font=f, fill=BLACK + (255,))
        y += b[3] - b[1] + r * 0.05
    return im.rotate(-rot, resample=Image.BICUBIC, expand=True)


def tape(text, f, rot=3, pad=(34, 16), bg=PURPLE, fg=INK):
    probe = ImageDraw.Draw(Image.new('L', (8, 8)))
    b = probe.textbbox((0, 0), text, font=f)
    w, h = b[2] - b[0] + pad[0] * 2, b[3] - b[1] + pad[1] * 2
    im = Image.new('RGBA', (w, h), bg + (245,))
    ImageDraw.Draw(im).text((pad[0] - b[0], pad[1] - b[1]), text, font=f, fill=fg + (255,))
    return im.rotate(rot, resample=Image.BICUBIC, expand=True)


def bats(d, spots):
    for x, y, s, rot in spots:
        d.polygon(bat_points(x, y, s, rot, 1.0), fill=BLACK + (255,))


def logo_img(w):
    lg = Image.open(LOGO).convert('RGBA')
    return lg.resize((w, max(1, round(lg.height * w / lg.width))), Image.LANCZOS)


def shade(a, y0, y1, k):
    """아래를 검정으로 내려 글과 띠가 선다."""
    H = a.shape[0]
    yy = np.arange(H, dtype=np.float32)
    ramp = np.clip((yy - y0) / max(1, y1 - y0), 0, 1) ** 1.3
    a *= (1 - ramp * k)[:, None, None]
    return a


# ══════════════════════════════════════════════════════════
#  피드 세 장
# ══════════════════════════════════════════════════════════

SHOTS = [(1426, 20.0, 300), (1417, 15.0, 160), (1434, 8.0, 330)]     # (컷, 초, 세로 자를 위치)


def feed():
    W, H = 1080, 1350
    RW = W * 3
    M = 80
    sheet = np.zeros((H, RW, 3), np.float32)
    for c, (n, t, y0) in enumerate(SHOTS):
        lift = 1.9 if n == 1434 else 1.45
        sheet[:, c * W:(c + 1) * W] = grade(crop(frame(n, t), y0, H), lift=lift)
    sheet = shade(sheet, 620, H, 0.78)
    # 위도 살짝. 머리글이 선다
    yy = np.arange(H, dtype=np.float32)
    sheet *= (1 - 0.45 * np.clip(1 - yy / 260, 0, 1))[:, None, None]

    pil = Image.fromarray((np.clip(sheet, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    bats(d, [(620, 170, 46, -0.2), (760, 250, 30, 0.1), (1500, 150, 26, 0.15), (2250, 200, 40, -0.1),
             (2420, 130, 24, 0.2), (2900, 260, 34, 0.05)])

    fe = cond(26, 'SemiLight Condensed')
    lg = logo_img(int(W * 0.17))
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, 96), 'BLACKOUT CREW PRESENTS', fe, 0.40, INK + (220,))
        pil.alpha_composite(lg, (x0 + W - M - lg.width, 88))

    # HW1 스티커
    st = sticker(['분장하고 오면', '술 한 잔', '서비스'], 190, -10)
    pil.alpha_composite(st, (W - st.width - 30, 190))
    # HW2 테이프
    tp = tape('COSTUME PARTY', cond(84), -3)
    pil.alpha_composite(tp, (W + (W - tp.width) // 2, 520))
    # HW3 테이프
    tp3 = tape('장소 · 라인업 곧 공개', kr(44), 3, bg=(18, 12, 22), fg=INK)
    pil.alpha_composite(tp3, (2 * W + W - tp3.width - 60, 240))

    # HALLOWEEN
    slot = RW / len(WORD)
    f = cond(40)
    for s in range(520, 60, -4):
        f = cond(s)
        if max(d.textlength(ch, font=f) for ch in WORD) <= slot * 0.78:
            break
    ly = 760
    for i, ch in enumerate(WORD):
        m = text3d(ch, f, stroke=9, shadow=(14, 14))
        paste(pil, m, slot * i + (slot - m.shape[1]) / 2, ly)
    lh = m.shape[0]
    d = ImageDraw.Draw(pil, 'RGBA')

    # 아래 띠
    by = H - 150
    d.rectangle([0, by, RW, H], fill=BLACK + (235,))
    d.rectangle([0, by, RW, by + 6], fill=ORANGE + (255,))
    fd = cond(88)
    tracked(d, (M, by + 30), DATE, fd, 0.04, INK + (255,))
    fk = kr(40)
    t2 = '할로윈 당일 밤 · 코스튬 파티'
    d.text((W + (W - d.textlength(t2, font=fk)) / 2, by + 46), t2, font=fk, fill=INK + (255,))
    t3 = 'BLACKOUT HALLOWEEN'
    f3 = cond(60)
    tracked(d, (2 * W + W - M - tracked_w(t3, f3, 0.04), by + 42), t3, f3, 0.04, ORANGE + (255,))

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.70, W * 0.010, 0.25)
    grain(out, 0.012)
    big = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    tiles = []
    for c in range(3):
        t = big.crop((c * W, 0, (c + 1) * W, H))
        t.save(os.path.join(OUT, f'HW{c + 1}.jpg'), quality=94)
        tiles.append(t)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(os.path.join(OUT, '_할로윈격자.jpg'), quality=92)
    print('피드 완료')


# ══════════════════════════════════════════════════════════
#  스토리
# ══════════════════════════════════════════════════════════

def story():
    W, H = 1080, 1920
    M = 80
    TOP = 250
    a = grade(frame(1417, 15.0), lift=1.45)
    a = shade(a, 900, 1700, 0.85)
    yy = np.arange(H, dtype=np.float32)
    a *= (1 - 0.55 * np.clip(1 - (yy - 150) / 300, 0, 1))[:, None, None]
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil, 'RGBA')
    bats(d, [(150, 420, 44, -0.2), (90, 540, 26, 0.1), (880, 380, 36, 0.15)])

    fe = cond(30, 'SemiLight Condensed')
    tracked(d, (M, TOP + 6), 'BLACKOUT CREW PRESENTS', fe, 0.40, INK + (220,))
    lg = logo_img(int(W * 0.19))
    pil.alpha_composite(lg, (W - M - lg.width, TOP))

    st = sticker(['분장하고 오면', '술 한 잔', '서비스'], 170, -10)
    pil.alpha_composite(st, (W - st.width - 10, 330))

    f = cond(40)
    for s in range(400, 60, -4):
        f = cond(s)
        if d.textlength(WORD, font=f) <= W - M * 2 - 30:
            break
    m = text3d(WORD, f, stroke=9, shadow=(14, 14))
    ly = 1040
    paste(pil, m, (W - m.shape[1]) / 2, ly)
    d = ImageDraw.Draw(pil, 'RGBA')
    tp = tape('COSTUME PARTY', cond(76), -3)
    pil.alpha_composite(tp, ((W - tp.width) // 2, ly - tp.height + 20))
    y = ly + m.shape[0] + 30
    fd = cond(130)
    tracked(d, ((W - tracked_w(DATE, fd, 0.04)) / 2, y), DATE, fd, 0.04, INK + (255,))
    y += 150
    fk = kr(44)
    t = '할로윈 당일 밤'
    d.text(((W - d.textlength(t, font=fk)) / 2, y), t, font=fk, fill=INK + (255,))
    y += 70
    tp3 = tape('장소 · 라인업 곧 공개', kr(38), 0, bg=(18, 12, 22), fg=INK)
    pil.alpha_composite(tp3, ((W - tp3.width) // 2, int(y)))
    assert y + tp3.height < 1640, y

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.70, W * 0.010, 0.25)
    grain(out, 0.012)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'HW_스토리.jpg'), quality=94)
    print('스토리 완료')


if __name__ == '__main__':
    feed()
    story()
