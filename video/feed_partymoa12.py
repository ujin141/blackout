"""
**올린 아홉 장 위에 세 장 더.** 맨 윗줄이 된다.

    python feed_partymoa12.py   →  out/partymoa/V1~V3.jpg · _격자_위셋.jpg

## 지금 격자

    맨 위    U6 9,900원   U5 1차 30명   U4 지금 예매 QR
    가운데   U3 혼자      U2 15:15      U1 웰컴샷
    맨 아래  P1 앱        P2 상세       P3 예매

새 세 장이 그 위에 올라간다. 격자는 새 글이 왼쪽 위라 V1 → V3 순으로
올려야 V3 이 왼쪽 위에 온다.

## 이 줄의 장치는 티켓

아랫줄들은 심볼(원)이 이어 준다. 원은 가운데 줄까지만 올라오니 맨 윗줄은
제 장치가 필요하다. 하얀 티켓 한 장을 세 칸에 걸쳐 놓는다. 칸 경계마다
절취선 홈을 파서, 격자에서 보면 찢어 나눈 한 장의 티켓이다. 한 장씩 봐도
"티켓" 이라 읽힌다 — 이 앱이 파는 게 그거다.

티켓에 적는 건 파티의 확정 사실뿐이다. 날짜·시간·장소·값·웰컴샷.

## 세 장이 하는 말

    V3 (왼쪽)   언제        9.26 토 22:00
    V2 (가운데) 어디·누가   압구정 딥하우즈 · 라인업 다섯
    V1 (오른쪽) 뭐가 좋나   티켓이 폰 안에. 입금 확인 알림, 입장은 예매번호

노랑은 CTA 판에만. 아랫줄들과 같은 규칙이다.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from feed_partymoa import ACC, ACCENT, BRAND, DEEP, DOTS, M, WHITE, font
from feed_partymoa9 import HEAD_TYPE, cta_plate, head
from fonts import KR, KRB

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'partymoa')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
COLS = 3
RW = W * COLS
INK = (20, 12, 60)        # 티켓 위 글자. CTA 판 글자와 같은 색

# (파일, 제목, 부제, CTA) — 오른쪽부터 올린다
TOP = [
    ('V1', ['티켓은', '폰 안에'], '입금 확인되면 알림. 입장은 예매번호로', 'App Store · 파티모아'),
    ('V2', ['압구정', '딥하우즈'], 'TECH HOUSE · BASS HOUSE · TECHNO', '라인업 보기 → 프로필 링크'),
    ('V3', ['9.26 토', '22:00'], '추석 연휴 마지막 토요일 · 02:10 까지', '예매하기 → 프로필 링크'),
]
SLOT = {'V1': 2, 'V2': 1, 'V3': 0}

# 티켓 띠. 로고 아래, 제목 위
TY0, TY1 = 214, 372
NOTCH = 30


def background_row():
    """U 줄과 같은 그라데이션 한 줄."""
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    top = np.float32(BRAND) / 255
    low = np.float32(DEEP) / 255
    row = top * (1 - yy ** 1.4) + low * (yy ** 1.4)
    row = np.repeat(row, RW, axis=1)
    xx = np.linspace(0, 1, RW, dtype=np.float32)[None, :, None]
    row += 0.06 * np.exp(-(((xx - 0.18) / 0.45) ** 2) - ((yy - 0.1) / 0.5) ** 2)
    pil = Image.fromarray((np.clip(row, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    ly = int(H * 0.86)
    d.line([(M, ly), (RW - M, ly)], fill=WHITE + (110,), width=2)
    return pil


def ticket(sheet):
    """세 칸에 걸친 티켓 한 장. 칸 경계에 절취선 홈."""
    lay = Image.new('RGBA', (RW, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([M, TY0, RW - M, TY1], 34, fill=WHITE)
    # 홈. 경계 위아래에 반원을 파고, 그 사이 점선
    for k in (1, 2):
        x = k * W
        for y in (TY0, TY1):
            d.ellipse([x - NOTCH, y - NOTCH, x + NOTCH, y + NOTCH], fill=(0, 0, 0, 0))
        for y in range(TY0 + NOTCH + 22, TY1 - NOTCH - 10, 26):
            d.line([(x, y), (x, y + 12)], fill=INK + (90,), width=3)
    # 그림자
    sh = Image.new('RGBA', (RW, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([M, TY0 + 18, RW - M, TY1 + 18], 34, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    sheet.alpha_composite(sh)
    sheet.alpha_composite(lay)

    d = ImageDraw.Draw(sheet)
    fb = font(KRB, 60)
    fs = font(KR, 27)
    fm = font(KRB, 36)
    cy = (TY0 + TY1) / 2

    # 왼쪽 칸: 이름
    x = M + 44
    d.text((x, cy - 46), 'AFTER MOON', font=fb, fill=INK)
    d.text((x, cy + 22), '2026.09.26 SAT', font=fs, fill=INK + (170,))
    # 왼쪽 칸 오른쪽: 시간
    tw = d.textlength('22:00 – 02:10', font=fm)
    d.text((W - M - 44 - tw, cy - 30), '22:00 – 02:10', font=fm, fill=INK)
    s = '밤 열 시부터'
    d.text((W - M - 44 - d.textlength(s, font=fs), cy + 16), s, font=fs, fill=INK + (170,))

    # 가운데 칸: 장르 · 라인업. 장소는 바로 아래 제목이 말하니 여기선 안 겹친다
    x = W + M + 44
    d.text((x, cy - 40), 'BHO · LYNN · LII · AROS · TS', font=font(KRB, 44), fill=INK)
    d.text((x, cy + 22), 'LINEUP · 5 DJ', font=fs, fill=INK + (170,))

    # 오른쪽 칸: 값 · 바코드
    x = 2 * W + M + 44
    d.text((x, cy - 46), '9,900원', font=fb, fill=INK)
    d.text((x, cy + 22), '웰컴샷 포함 · 1차 30명', font=fs, fill=INK + (170,))
    bx1 = RW - M - 44
    bx = bx1 - 300
    rng = np.random.default_rng(926)
    xx = bx
    while xx < bx1:
        w = int(rng.integers(3, 11))
        d.rectangle([xx, cy - 44, xx + w, cy + 30], fill=INK)
        xx += w + int(rng.integers(4, 12))
    s = 'PM ····'
    d.text((bx1 - d.textlength(s, font=fs), cy + 36), s, font=fs, fill=INK + (170,))


def tile_at(sheet, col, lines, sub, cta):
    t = sheet.crop((col * W, 0, (col + 1) * W, H))
    d = ImageDraw.Draw(t)
    f = font(KRB, 34)
    S = 0.42
    ox, oy = M, 104
    for x, y in DOTS:
        cx, cy = ox + x * S, oy + y * S
        d.ellipse([cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2], fill=WHITE)
    cx, cy = ox + ACC[0] * S, oy + ACC[1] * S
    d.ellipse([cx - 2.6, cy - 2.6, cx + 2.6, cy + 2.6], fill=ACCENT)
    d.text((ox + 48, oy + 4), '파티모아', font=f, fill=WHITE)

    ly = int(H * 0.86)
    head(d, lines, sub, HEAD_TYPE, 470)
    cta_plate(d, cta, ly - 92 - 48)

    fb = font(KR, 22)
    d.text((M, ly + 22), 'partymoa.com', font=fb, fill=WHITE + (200,))
    r = 'App Store'
    d.text((W - M - d.textlength(r, font=fb), ly + 22), r, font=fb, fill=WHITE + (200,))
    return t.convert('RGB')


def main():
    sheet = background_row()
    ticket(sheet)
    done = {}
    for name, lines, sub, cta in TOP:
        col = SLOT[name]
        im = tile_at(sheet, col, lines, sub, cta)
        im.save(os.path.join(OUT, f'{name}.jpg'), quality=94)
        done[col] = im

    # 미리보기. 네 줄 — 새 줄 + 올린 아홉
    rows = [
        [done[0], done[1], done[2]],
        ['U6', 'U5', 'U4'],
        ['U3', 'U2', 'U1'],
        ['P1', 'P2', 'P3'],
    ]
    g = Image.new('RGB', (W * 3 + 16, H * 4 + 24), (255, 255, 255))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            if isinstance(im, str):
                p = os.path.join(OUT, f'{im}.jpg')
                if not os.path.exists(p):
                    continue
                im = Image.open(p)
            g.paste(im, (c * (W + 8), r * (H + 8)))
    g.resize((g.width // 4, g.height // 4), Image.LANCZOS).save(
        os.path.join(OUT, '_격자_위셋.jpg'), quality=92)
    print('완료: V1~V3')


if __name__ == '__main__':
    main()
