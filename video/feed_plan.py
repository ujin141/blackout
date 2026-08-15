"""프로필 그리드 배치도 — **올리기 전에 그리드를 미리 본다.**

줄판을 여럿 만들어 놓고 나면 "뭘 먼저 올리지" 에서 매번 막힌다. 인스타는
새 글을 왼쪽 위에 넣기 때문에 **보고 싶은 그림의 반대 순서로 올려야 한다** —
그걸 머릿속으로 뒤집다 보면 한 칸씩 어긋난다.

    화면에 보이는 것        올리는 순서
    ┌───┬───┬───┐
    │ 1 │ 2 │ 3 │  ← 맨 위 줄 = 제일 나중에 올린 줄
    ├───┼───┼───┤
    │ 1 │ 2 │ 3 │
    └───┴───┴───┘
      한 줄 안에서도 3 → 2 → 1 순서로 올려야 왼쪽부터 1 이 온다

**줄 사이에 다른 글을 끼우면 그 아래가 전부 한 칸씩 밀린다.** 한 줄은
세 개를 붙여 올리고, 그 사이에 낱장을 올리지 않는다.

`ROWS` 는 화면에 보이길 원하는 순서(위→아래). 스크립트가 뒤집어서
올리는 순서를 찍어 준다.

python feed_plan.py  →  out/feed_plan.png + 올리는 순서
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from poster_kit import BRAND, tmask, paint, tmask_bl, paint_bl
from fonts import KR, KRB

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')

# 화면에 보이길 원하는 순서 — 위가 최신
ROWS = [
    ('feed_event', 'follow',   '팔로우 혜택 — 웰컴드링크 1+1'),
    ('feed_event', 'promo',    '참여 이벤트 — 샴페인 추첨'),
    ('feed_event', 'wave',     '모집 현황 — 차수'),
    ('feed_event', 'event',    '행사 포스터'),
    ('feed_event', 'shortrow', '바이럴 영상 줄'),
    ('feed_event', 'tagrow',   '번호표'),
    ('feed_row',   'v',        '멤버 V'),
    ('feed_row',   'aros',     '멤버 AROS'),
    ('feed_row',   'lynn',     '멤버 LYNN'),
    ('feed_row',   'ts',       '멤버 TS'),
    ('feed_row',   'demic',    '멤버 DEMIC'),
]

TW, TH = 232, 290                       # 배치도 안에서의 칸 크기
GAP = 5
PAD = 26
LABEL = 34                              # 줄 이름이 들어가는 왼쪽 띠


def tiles(folder, stem):
    """세 칸을 읽는다. 하나라도 없으면 그 줄은 건너뛴다."""
    out = []
    for i in (1, 2, 3):
        p = os.path.join(OUT, folder, f'{stem}_{i}.png')
        if not os.path.exists(p):
            return None
        out.append(Image.open(p).convert('RGB').resize((TW, TH), Image.LANCZOS))
    return out


def build():
    rows = [(f, s, n, t) for f, s, n in ROWS if (t := tiles(f, s))]
    W = PAD * 2 + LABEL + TW * 3 + GAP * 2
    H = PAD * 2 + 76 + len(rows) * (TH + GAP)
    img = np.zeros((H, W, 3), np.float32)
    img[:] = np.float32([0.055, 0.058, 0.064])

    paint_bl(img, tmask_bl('프로필 그리드 배치도', KRB, 26, 0.02), PAD, PAD + 30,
             color=np.float32([0.98, 0.98, 1.0]))
    paint_bl(img, tmask_bl('위가 최신 · 올리는 순서는 아래 줄부터, 한 줄 안에서는 3 → 2 → 1',
                           KR, 15, 0.01), PAD, PAD + 58,
             color=np.float32([0.55, 0.62, 0.72]))

    y = PAD + 76
    for i, (_, stem, name, ts) in enumerate(rows):
        for c, t in enumerate(ts):
            x = PAD + LABEL + c * (TW + GAP)
            img[y:y + TH, x:x + TW] = np.asarray(t).astype(np.float32) / 255
        paint_bl(img, tmask_bl(f'{i + 1}', BRAND, 15, 0.16), PAD, y + TH / 2 + 6,
                 color=np.float32([0.94, 0.78, 0.40]), a=0.9)
        y += TH + GAP

    a = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im)
    yy = PAD + 76
    for i, (_, stem, name, _) in enumerate(rows):
        d.text((PAD + LABEL + TW * 3 + GAP * 2 + 8, yy + 6), '', fill=(255, 255, 255))
        yy += TH + GAP
    return im, rows


if __name__ == '__main__':
    im, rows = build()
    p = os.path.join(OUT, 'feed_plan.png')
    im.save(p, optimize=True)
    print(p)
    print('\n올리는 순서 — 위에서부터 그대로 따라 올리면 됩니다\n')
    n = 1
    for folder, stem, name, _ in reversed(rows):
        print(f'  ─ {name}')
        for i in (3, 2, 1):
            print(f'    {n:2d}.  out/{folder}/{stem}_{i}.png')
            n += 1
    print('\n※ 줄 사이에 낱장을 끼우면 그 아래가 전부 한 칸씩 밀립니다.')
