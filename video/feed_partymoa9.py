"""
**파티모아 피드 9장.** 3×3 격자가 한 판이다. 훅과 CTA 를 끝까지 민다.

    python feed_partymoa9.py   →  out/partymoa/G1~G9.jpg · _격자9.jpg

## 3×3 이 왜 한 판인가

프로필 첫 화면이 딱 세 줄이다. 아홉 장을 한 번에 채우면 들어온 사람이
스크롤 없이 보는 게 전부 우리 판이다. 심볼을 아홉 칸 폭·높이로 깔아서
셋씩 세 줄이 하나로 붙는다.

## 줄마다 할 일이 다르다

    1줄  앱이 뭔지     폰 세 대. 홈 → 상세 → 예매
    2줄  왜 오는지     혼자 가도 되나 · 남녀 15:15 · 웰컴샷 쿠폰
    3줄  지금 하라     9,900원 · 1차 30명 · QR

3줄은 전부 CTA 판이 붙는다. 노란 판에 검정 글씨 — 이 판에서 노랑은
여기만 쓴다. 눈이 거기로 간다.

## 숫자는 앱에 있는 것만

45명 중 45명 혼자는 홈의 '지금까지' 칸 숫자다. 지어내지 않는다.

## 올리는 순서

격자는 새 글이 왼쪽 위다. G9 → G1 순으로 올려야 G1 이 왼쪽 위에 온다.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from feed_partymoa import (ACC, ACCENT, BRAND, DEEP, DOTS, M, SHOTS, WHITE,
                           font, phone, shadow)
from fonts import KR, KRB
from qr import build as qr_build

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'partymoa')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
COLS, ROWS = 3, 3
RW, RH = W * COLS, H * ROWS
PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'

# (종류, 제목 줄들, 부제, CTA)
TILES = [
    ('phone:home', ['파티 예매 앱', '파티모아'], 'App Store 출시', None),
    ('phone:party', ['누가 트는지', '몇 자리 남았는지'], '라인업 · 잔여석 · 남녀 자리', None),
    ('phone:book', ['예매 1분', '입금 24시간'], '티켓도 쿠폰도 폰 안에', None),

    ('type', ['혼자 가도', '되나요'], '지난 파티 45명 중 45명이 혼자 왔어요', '파티 보기 → 프로필 링크'),
    ('type', ['남녀', '15 : 15'], '성비 맞춰 받아요. 한쪽 차면 그쪽 마감', '남은 자리 보기 → 프로필 링크'),
    ('type', ['웰컴샷', '쿠폰'], '예매하면 티켓에 붙어요. 바에서 보여주면 끝', '예매하면 자동 발급'),

    ('type', ['9,900원'], 'AFTER MOON · 9.26 토 · 압구정 딥하우즈', '예매하기 → 프로필 링크'),
    ('type', ['1차 30명'], '차면 2차. 먼저 잡는 쪽이 먼저', '남은 자리 보기 → 프로필 링크'),
    ('qr', ['지금 예매'], 'QR 찍으면 바로 예매 화면', 'App Store · 파티모아'),
]


def background():
    yy = np.linspace(0, 1, RH, dtype=np.float32)[:, None, None]
    top = np.float32(BRAND) / 255
    low = np.float32(DEEP) / 255
    a = top * (1 - yy ** 1.6) + low * (yy ** 1.6)
    a = np.repeat(a, RW, axis=1)
    xx = np.linspace(0, 1, RW, dtype=np.float32)[None, :, None]
    a += 0.06 * np.exp(-(((xx - 0.18) / 0.45) ** 2) - ((yy - 0.06) / 0.4) ** 2)
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')

    # 심볼. 아홉 칸에 걸친다. 원이 2줄을 지나고 노란 점은 오른쪽 가운데
    lay = Image.new('RGBA', (RW, RH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    S = RW / 63.0
    ox = (RW - (ACC[0] - 26.6) * S) / 2 - 26.6 * S
    oy = RH * 0.50 - 50 * S
    r = 2.8 * S
    for x, y in DOTS:
        cx, cy = ox + x * S, oy + y * S
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE + (22,))
    cx, cy = ox + ACC[0] * S, oy + ACC[1] * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT + (120,))
    lay = lay.filter(ImageFilter.GaussianBlur(1.2))
    pil.alpha_composite(lay)

    d = ImageDraw.Draw(pil)
    for row in range(ROWS):
        ly = row * H + int(H * 0.86)
        d.line([(M, ly), (RW - M, ly)], fill=WHITE + (110,), width=2)
    return pil


def cta_plate(d, text, y):
    """노란 판. 이 판에서 노랑은 여기만 쓴다."""
    f = font(KRB, 34)
    tw = d.textlength(text, font=f)
    pw, ph = int(tw + 72), 92
    x = M
    d.rounded_rectangle([x, y, x + pw, y + ph], 22, fill=ACCENT)
    d.text((x + 36, y + (ph - 34) / 2 - 4), text, font=f, fill=(20, 12, 60))
    return ph


def head(d, lines, sub, size, y):
    fh = font(KRB, size)
    for line in lines:
        d.text((M, y), line, font=fh, fill=WHITE)
        y += size + 12
    fs = font(KR, 32)
    d.text((M, y + 14), sub, font=fs, fill=ACCENT)
    return y + 14 + 32


def tile(sheet, i, kind, lines, sub, cta):
    col, row = i % COLS, i // COLS
    t = sheet.crop((col * W, row * H, (col + 1) * W, (row + 1) * H))
    d = ImageDraw.Draw(t)

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
    fn = font(KR, 24)
    num = f'{i + 1:02d} / 09'
    d.text((W - M - d.textlength(num, font=fn), 112), num, font=fn, fill=WHITE + (170,))

    ly = int(H * 0.86)

    if kind.startswith('phone:'):
        head(d, lines, sub, HEAD_PHONE, 230)
        pw = 540
        body = phone(os.path.join(SHOTS, kind.split(':')[1] + '.png'), pw)
        px, py = (W - pw) // 2, 560
        sh, pad = shadow(body.size, 40, 140)
        t.alpha_composite(sh, (px - pad, py - pad + 30))
        t.alpha_composite(body, (px, py))
        d = ImageDraw.Draw(t)

    elif kind == 'type':
        # 큰 글자는 칸 가운데쯤. 위 여백이 훅을 띄운다
        y0 = 360 if len(lines) == 2 else 470
        yb = head(d, lines, sub, HEAD_TYPE, y0)
        if cta:
            cta_plate(d, cta, ly - 92 - 48)

    else:  # qr
        yb = head(d, lines, sub, HEAD_TYPE, 300)
        q = qr_build(PARTY_URL, 300, [0.08, 0.04, 0.24], [1.0, 1.0, 1.0],
                     badge=False, error='m')
        qs = 320
        q = q.resize((qs, qs), Image.NEAREST)
        box = Image.new('RGBA', (qs + 48, qs + 48), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([0, 0, qs + 47, qs + 47], 28, fill=WHITE)
        box.paste(q, (24, 24))
        qx, qy = M, yb + 60
        t.alpha_composite(box, (qx, qy))
        d = ImageDraw.Draw(t)
        f = font(KR, 26)
        d.text((qx + qs + 48 + 28, qy + 24), '카메라로 찍으면', font=f, fill=WHITE + (220,))
        d.text((qx + qs + 48 + 28, qy + 24 + 40), 'AFTER MOON 예매', font=f, fill=WHITE + (220,))
        d.text((qx + qs + 48 + 28, qy + 24 + 80), '화면이 열려요', font=f, fill=WHITE + (220,))
        if cta:
            cta_plate(d, cta, ly - 92 - 48)

    fb = font(KR, 22)
    d.text((M, ly + 22), 'partymoa.com', font=fb, fill=WHITE + (200,))
    r = 'App Store'
    d.text((W - M - d.textlength(r, font=fb), ly + 22), r, font=fb, fill=WHITE + (200,))
    return t.convert('RGB')


def _size(kinds, cap):
    longest = max((l for k, ls, _, _ in TILES if k.startswith(kinds) for l in ls), key=len)
    for sz in range(cap, 50, -2):
        if font(KRB, sz).getlength(longest) <= W - M * 2:
            return sz
    return 50


HEAD_PHONE = _size('phone', 120)
HEAD_TYPE = _size(('type', 'qr'), 210)


def main():
    sheet = background()
    tiles = []
    for i, (kind, lines, sub, cta) in enumerate(TILES):
        im = tile(sheet, i, kind, lines, sub, cta)
        im.save(os.path.join(OUT, f'G{i + 1}.jpg'), quality=94)
        tiles.append(im)
    g = Image.new('RGB', (W * 3 + 16, H * 3 + 16), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, ((i % 3) * (W + 8), (i // 3) * (H + 8)))
    g.resize((g.width // 4, g.height // 4), Image.LANCZOS).save(
        os.path.join(OUT, '_격자9.jpg'), quality=92)
    print('완료:', OUT)


if __name__ == '__main__':
    main()
