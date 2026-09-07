"""
**파티모아 인스타 피드 3장.** 브랜드 보라 위에 폰 목업. 격자에서 이어진다.

    python shots_cdp.py       먼저. 화면을 새로 찍는다
    python feed_partymoa.py   →  out/partymoa/P1.jpg P2.jpg P3.jpg · _격자.jpg

## 세 장을 잇는 것

파티모아 심볼(열린 원 + 점 여덟 개 + 노란 점)을 세 칸 폭으로 크게 깔고
셋으로 자른다. 한 장씩 보면 점 몇 개가 보이는 무늬고, 붙이면 심볼이다.
폰 목업은 같은 바닥선에 선다. 아래 흰 선 하나가 세 장을 지난다.

## 한 장씩도 완결

칸마다 제목 두 줄과 폰 한 대. 홈 → 파티 상세 → 예매. 앱을 처음 보는
사람이 세 장을 순서대로 넘기면 예매까지 한 번 가 본 셈이 된다.

## 색

브랜드 보라 #5B2BE8, 아래로 갈수록 #4416C8. 글자는 흰색, 강조는 노랑
#FFE24D 한 곳. 폰 테두리는 검정. 그 외 색은 화면 캡처 안에만 있다.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from fonts import KR, KRB

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, 'assets', 'shots_moon')
OUT = os.path.join(HERE, 'out', 'partymoa')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
COLS = 3
RW = W * COLS
M = 84

BRAND = (0x5B, 0x2B, 0xE8)
DEEP = (0x44, 0x16, 0xC8)
ACCENT = (0xFF, 0xE2, 0x4D)
WHITE = (255, 255, 255)

# 심볼 좌표. 100 칸 안. profile_partymoa.py 와 같다
DOTS = [(63.20, 63.25), (51.32, 72.66), (36.53, 71.19), (26.60, 59.63),
        (26.60, 40.37), (36.53, 28.81), (51.32, 27.34), (63.20, 36.75)]
ACC = (85.00, 50.00)

TILES = [
    ('home', ['파티 예매 앱', '파티모아'], 'App Store 출시'),
    ('party', ['누가 트는지', '몇 자리 남았는지'], '라인업 · 잔여석 · 남녀 자리'),
    ('book', ['예매 1분', '입금 24시간'], '티켓도 쿠폰도 폰 안에'),
]


def font(p, s):
    return ImageFont.truetype(p, s)


def background():
    """세 칸짜리 보라 바탕. 아래로 깊어지고, 심볼이 크게 깔린다."""
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.float32(BRAND) / 255
    low = np.float32(DEEP) / 255
    a = top * (1 - yy ** 1.4) + low * (yy ** 1.4)
    a = np.repeat(a, RW, axis=1)
    # 왼쪽 위가 조금 밝다. 판판한 단색은 인쇄물처럼 죽는다
    xx = np.linspace(0, 1, RW, dtype=np.float32)[None, :, None]
    a += 0.06 * np.exp(-(((xx - 0.18) / 0.45) ** 2) - ((yy - 0.1) / 0.5) ** 2)
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')

    # 심볼. 세 칸 폭 거의 다 쓴다. 흰 점은 아주 옅게, 노란 점만 살린다
    lay = Image.new('RGBA', (RW, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    S = RW / 63.0                             # 26.6~85 칸이 세 칸을 거의 채운다
    ox = (RW - (ACC[0] - 26.6) * S) / 2 - 26.6 * S
    oy = H * 0.50 - 50 * S
    r = 2.8 * S
    for x, y in DOTS:
        cx, cy = ox + x * S, oy + y * S
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE + (22,))
    cx, cy = ox + ACC[0] * S, oy + ACC[1] * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT + (120,))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    pil.alpha_composite(lay)

    # 세 장을 지나는 선. 폰 바닥선보다 위, 제목 아래
    d = ImageDraw.Draw(pil)
    ly = int(H * 0.86)
    d.line([(M, ly), (RW - M, ly)], fill=WHITE + (110,), width=2)
    return pil


def phone(shot, width):
    """검정 테두리 폰. 화면은 둥글게 잘라 넣는다."""
    im = Image.open(shot).convert('RGB')
    sw = width - 2 * 22
    sh = int(im.height * sw / im.width)
    im = im.resize((sw, sh), Image.LANCZOS)
    ph = sh + 2 * 22
    body = Image.new('RGBA', (width, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([0, 0, width - 1, ph - 1], 74, fill=(11, 10, 20, 255))
    d.rounded_rectangle([3, 3, width - 4, ph - 4], 72, outline=(60, 56, 84, 255), width=2)
    mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw - 1, sh - 1], 56, fill=255)
    body.paste(im, (22, 22), mask)
    # 노치
    d.rounded_rectangle([width / 2 - 78, 30, width / 2 + 78, 30 + 30], 15, fill=(11, 10, 20, 255))
    return body


def shadow(size, blur, alpha):
    w, h = size
    pad = blur * 3
    lay = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle([pad, pad, pad + w, pad + h], 74,
                                          fill=(20, 8, 60, alpha))
    return lay.filter(ImageFilter.GaussianBlur(blur)), pad


def tile(sheet, i, shot, lines, sub):
    t = sheet.crop((i * W, 0, (i + 1) * W, H))
    d = ImageDraw.Draw(t)

    # 위: 심볼 작게 + 워드마크. 첫 칸만 — 격자에서 셋에 다 있으면 시끄럽다
    if i == 0:
        f = font(KRB, 34)
        S = 0.42
        ox, oy = M, 104
        for x, y in DOTS:
            cx, cy = ox + x * S, oy + y * S
            d.ellipse([cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2], fill=WHITE)
        cx, cy = ox + ACC[0] * S, oy + ACC[1] * S
        d.ellipse([cx - 2.6, cy - 2.6, cx + 2.6, cy + 2.6], fill=ACCENT)
        d.text((ox + 48, oy + 4), '파티모아', font=f, fill=WHITE)
    # 순번은 셋 다
    fn = font(KR, 24)
    d.text((W - M - d.textlength(f'0{i + 1} / 03', font=fn), 112), f'0{i + 1} / 03',
           font=fn, fill=WHITE + (170,))

    # 제목 두 줄. 폭에 맞춘 한 크기를 셋이 같이 쓴다
    fh = font(KRB, HEAD_SIZE)
    y = 230
    for line in lines:
        d.text((M, y), line, font=fh, fill=WHITE)
        y += HEAD_SIZE + 12
    fs = font(KR, 32)
    d.text((M, y + 14), sub, font=fs, fill=ACCENT)

    # 폰. 바닥선 아래로 잘린다. 셋이 같은 높이에 선다
    pw = 540
    body = phone(shot, pw)
    px, py = (W - pw) // 2, 560
    sh, pad = shadow(body.size, 40, 140)
    t.alpha_composite(sh, (px - pad, py - pad + 30))
    t.alpha_composite(body, (px, py))

    # 아래 선 밑 글자
    fb = font(KR, 22)
    ly = int(H * 0.86)
    d = ImageDraw.Draw(t)
    d.text((M, ly + 22), 'partymoa.com', font=fb, fill=WHITE + (200,))
    r = 'App Store'
    d.text((W - M - d.textlength(r, font=fb), ly + 22), r, font=fb, fill=WHITE + (200,))
    return t.convert('RGB')


def _head_size():
    longest = max((l for _, ls, _ in TILES for l in ls), key=len)
    for sz in range(120, 50, -2):
        if font(KRB, sz).getlength(longest) <= W - M * 2:
            return sz
    return 50


HEAD_SIZE = _head_size()


def main():
    sheet = background()
    tiles = []
    for i, (shot, lines, sub) in enumerate(TILES):
        im = tile(sheet, i, os.path.join(SHOTS, f'{shot}.png'), lines, sub)
        im.save(os.path.join(OUT, f'P{i + 1}.jpg'), quality=94)
        tiles.append(im)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_격자.jpg'), quality=92)
    print('완료:', OUT)


if __name__ == '__main__':
    main()
