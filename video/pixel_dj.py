"""
**AFTER MOON · 디제이 픽셀아트 셋.** 한 칸에 한 사람, 세 칸이 한 판.

    python pixel_dj.py   →  out/moon/PX1.jpg PX2.jpg PX3.jpg · _픽셀격자.jpg

## 픽셀로 그리는 법

1080×1350 을 6으로 나눈 180×225 칸에 그린다. 세 칸이면 540×225 한 판.
그 위에 글자·사람·달·바닥을 전부 픽셀 단위로 놓고, 마지막에 6배로
**nearest** 로 키운다. 안티앨리어싱은 어디에도 없다 — 글자도 fontmode '1'.

## 이어지는 것

    바닥      체커 플로어가 세 칸 아래를 지난다. 원근으로 좁아진다
    달        가운데 칸 위에 큰 픽셀 달. 디더링으로 그림자. 양옆 칸에 빛 조각
    별        1px 별이 온 판에
    띠        맨 아래 조건 한 줄이 세 칸을 이어 흐른다

## 색은 사람에게만

판은 검정·남색·은색·흰색 네 단계. 누끼만 색이 있다 — 그것도 8색으로 줄인다.
BHO · LII 는 누끼가 없어 없다. 셋이 한 판이고 라인업 다섯은 띠에 다 적는다.

## 올리는 순서

PX3 → PX2 → PX1. 격자는 새 글이 왼쪽 위.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fonts import KR, KRB
from poster_crew import crop_head
from poster_lineup import LINEUP
from poster_moon import BRAND_FONT, OUT

S = 6                                  # 픽셀 한 칸 = 6px
PW, PH = 180, 225                      # 칸 (픽셀)
COLS = 3
RW = PW * COLS
DJS = ['LYNN', 'AROS', 'TS']           # 누끼 있는 셋, 트는 순서

BLACK = (10, 10, 14)
NAVY = (22, 24, 40)
NAVY2 = (34, 36, 58)
GRAY = (110, 114, 128)
SILVER = (188, 192, 204)
WHITE = (244, 245, 248)


def font(p, s):
    return ImageFont.truetype(p, s)


def slot(name):
    for i, (n, a, b) in enumerate(LINEUP):
        if n == name:
            return i + 1, a, b
    return 0, '', ''


def sky(d):
    """위는 검정, 아래로 남색. 띠 넷으로 끊는다 — 그라데이션도 픽셀답게."""
    bands = [(0, 60, BLACK), (60, 110, (14, 15, 22)), (110, 150, NAVY), (150, 225, NAVY2)]
    for y0, y1, c in bands:
        d.rectangle([0, y0, RW, y1], fill=c)
    rng = np.random.default_rng(926)
    for _ in range(140):
        x, y = int(rng.integers(0, RW)), int(rng.integers(0, 140))
        c = WHITE if rng.random() < 0.25 else SILVER if rng.random() < 0.5 else GRAY
        d.point((x, y), fill=c)
        if rng.random() < 0.08:                        # 큰 별은 십자
            d.point([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], fill=GRAY)


def moon(d, cx, cy, r):
    """디더링 달. 왼쪽 위가 밝고 오른쪽 아래로 체커가 짙어진다."""
    for y in range(-r, r + 1):
        for x in range(-r, r + 1):
            if x * x + y * y > r * r:
                continue
            k = (x + y) / (2.0 * r)                    # -1 ~ 1, 오른쪽 아래가 크다
            if k < -0.25:
                c = WHITE
            elif k < 0.15:
                c = WHITE if (x + y) % 2 == 0 else SILVER
            elif k < 0.5:
                c = SILVER if (x + y) % 2 == 0 else GRAY
            else:
                c = GRAY
            d.point((cx + x, cy + y), fill=c)
    # 크레이터 셋
    for ox, oy, rr in ((-r // 3, -r // 4, 3), (r // 5, r // 6, 4), (-r // 6, r // 3, 2)):
        for y in range(-rr, rr + 1):
            for x in range(-rr, rr + 1):
                if x * x + y * y <= rr * rr:
                    d.point((cx + ox + x, cy + oy + y), fill=GRAY)
    # 빛줄기. 달에서 옆 칸으로 가는 점선
    for k, ang in enumerate((-35, -15, 15, 35, 160, 185, 200)):
        a = np.deg2rad(ang)
        for t in range(r + 6, r + 90, 3):
            x, y = int(cx + np.cos(a) * t), int(cy + np.sin(a) * t)
            if 0 <= x < RW and 0 <= y < PH and (t // 3 + k) % 2 == 0:
                d.point((x, y), fill=GRAY if t < r + 50 else NAVY2)


def floor(d, y0=168, y1=190):
    """체커 댄스플로어. 위로 갈수록 칸이 좁아진다 — 원근."""
    rows = [(y0, 3), (y0 + 3, 4), (y0 + 7, 5), (y0 + 12, 6), (y0 + 18, 7)]
    for ry, h in rows:
        cell = h * 2
        for x in range(0, RW, cell):
            k = (x // cell + ry) % 2
            d.rectangle([x, ry, x + cell - 1, ry + h - 1], fill=NAVY2 if k else (28, 30, 48))
    d.line([(0, y0 - 1), (RW, y0 - 1)], fill=GRAY)


def pixel_person(name, w, h):
    """누끼를 픽셀로. 작게 줄인 뒤 8색으로. 알파는 딱 자른다."""
    fig = crop_head(name, w * 2, h * 2)              # 2배로 받아 줄이면 점이 덜 튄다
    rgb = (np.clip(fig[..., :3], 0, 1) * 255).astype(np.uint8)
    a = (fig[..., 3] > 0.5).astype(np.uint8) * 255
    im = Image.fromarray(rgb).resize((w, h), Image.BOX)
    al = Image.fromarray(a).resize((w, h), Image.NEAREST)
    q = im.quantize(colors=8, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).convert('RGB')
    # 살짝 대비. 8색으로 줄이면 뭉개지니 밝은 건 더 밝게
    arr = np.asarray(q, np.float32)
    arr = np.clip((arr - 128) * 1.15 + 128, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr).convert('RGBA')
    out.putalpha(al)
    return out


def outline(d, im, x, y):
    """실루엣 테두리 1px 은색. 검정 판에서 사람을 뗀다."""
    a = np.asarray(im.getchannel('A')) > 0
    h, w = a.shape
    pad = np.pad(a, 1)
    edge = pad[1:-1, 1:-1] & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    for yy, xx in zip(*np.where(edge)):
        d.point((x + xx, y + yy), fill=SILVER)


def text1(d, xy, s, path, size, fill, anchor='la'):
    """안티앨리어싱 없이. 픽셀 글자."""
    d.fontmode = '1'
    d.text(xy, s, font=font(path, size), fill=fill, anchor=anchor)


def tile(d, img, c, name):
    x0 = c * PW
    n, a, b = slot(name)
    # 머리글
    text1(d, (x0 + 8, 8), 'BLACKOUT', BRAND_FONT, 8, SILVER)
    text1(d, (x0 + PW - 8, 8), f'{c + 1:02d}/03', BRAND_FONT, 7, GRAY, 'ra')
    text1(d, (x0 + PW // 2, 22), 'AFTER MOON · 09.26', BRAND_FONT, 6, GRAY, 'ma')
    # 사람. 바닥 위에 선다. 이름이 어깨를 덮는다
    fw, fh = 118, 122
    fig = pixel_person(name, fw, fh)
    fx, fy = x0 + (PW - fw) // 2, 48
    outline(d, fig, fx, fy)
    img.alpha_composite(fig, (fx, fy))
    d = ImageDraw.Draw(img)
    # 이름. 그림자 1px 검정 → 은색
    ny = 142
    text1(d, (x0 + PW // 2 + 1, ny + 1), name, BRAND_FONT, 22, BLACK, 'ma')
    text1(d, (x0 + PW // 2, ny), name, BRAND_FONT, 22, WHITE, 'ma')
    text1(d, (x0 + PW // 2 + 1, ny + 27), f'{n:02d}  {a} - {b}', BRAND_FONT, 7, BLACK, 'ma')
    text1(d, (x0 + PW // 2, ny + 26), f'{n:02d}  {a} - {b}', BRAND_FONT, 7, SILVER, 'ma')
    return d


def band(d):
    """맨 아래 띠. 세 칸을 이어 흐르는 두 줄. 한글은 9px 는 돼야 읽힌다."""
    y = 194
    d.line([(6, y), (RW - 6, y)], fill=GRAY)
    names = '  ·  '.join(n for n, _, _ in LINEUP)
    text1(d, (RW // 2, y + 4), names, BRAND_FONT, 8, SILVER, 'ma')
    text1(d, (RW // 2, y + 16), '9.26 토 22:00-02:10  압구정 딥하우즈  9,900원  1차 30명  예매 PARTYMOA', KRB, 9, GRAY, 'ma')


def main():
    img = Image.new('RGBA', (RW, PH), BLACK + (255,))
    d = ImageDraw.Draw(img)
    d.fontmode = '1'
    sky(d)
    moon(d, RW // 2, 52, 34)
    floor(d)
    for c, name in enumerate(DJS):
        d = tile(d, img, c, name)
    band(d)

    big = img.convert('RGB').resize((RW * S, PH * S), Image.NEAREST)
    tiles = []
    for c in range(COLS):
        t = big.crop((c * PW * S, 0, (c + 1) * PW * S, PH * S))
        t.save(os.path.join(OUT, f'PX{c + 1}.jpg'), quality=94)
        tiles.append(t)
    g = Image.new('RGB', (PW * S * 3 + 16, PH * S), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (PW * S + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.NEAREST).save(
        os.path.join(OUT, '_픽셀격자.jpg'), quality=92)
    print('완료: PX1~PX3')


if __name__ == '__main__':
    main()
