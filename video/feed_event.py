"""
행사 피드 한 줄 — AFTER SUNSET 을 세 칸으로 나눠 그리드 한 줄을 통째로 채운다.

포스터를 한 장씩 올리면 그리드가 어긋난다. 계정은 세 칸이 한 줄로 읽히게 짜여
있는데 포스터 두 장을 올리면 줄이 안 채워지고, 다음에 올릴 멤버 줄이 한 칸씩
밀린다. **한 줄(3칸)을 통째로 하나의 그림으로 만들면** 그 문제가 없어진다.

    │ 이름 │ 타임테이블 │ 정보·예약 │   ← 세 칸이 이어진 한 장

3240×1350 으로 그린 뒤 1080×1350 세 장으로 자른다. `feed_row.py` 와 같은 규칙.

**이음새(x=1080, 2160)에는 아무것도 올리지 않는다.** 인스타 그리드는 타일 사이가
벌어져서 경계에 걸친 글자·가는 획은 잘려 사라진다. 배경 사진과 가로선만 지나간다.

**올리는 순서는 거꾸로다.** 최신이 왼쪽 위라 3칸 → 2칸 → 1칸 순으로 올려야
`이름 | 타임테이블 | 정보` 로 읽힌다. 반대로 올리면 좌우가 뒤집힌다.

3번 칸은 릴스 커버로도 쓴다 — 커버는 9:16 이고 그리드는 그 가운데를 4:5 로
잘라 보여주므로, 1350 짜리를 그대로 주면 글자 위치가 밀린다.
→ `event_3_cover.png` (1080×1920, 타일을 정확히 가운데) 를 커버로 쓸 것.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이고 포스터와 같은 톤을 쓴다.

python feed_event.py  →  out/feed_event/event_{1,2,3}.png · event_full.png · event_3_cover.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import (BRAND, HERO, HERO_CROP, tmask, tmask_bl, fit, paint, paint_bl,
                        rule, box, duotone, grain, logo, HERO_TAG)
from fest_kit import justify, vignette
from fonts import KR
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_event')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T, SAFE_B = 135, 1215        # 그리드에서 잘리지 않는 세로 구간
SEAM = 90                         # 이음새 좌우로 비워 두는 폭
RULE_Y = 300                      # 세 칸을 관통하는 가로선

DEEP = np.float32([0.020, 0.044, 0.068])
LIT = np.float32([0.330, 0.520, 0.615])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA = np.float32([0.32, 0.92, 1.00])
ROSE = np.float32([1.00, 0.34, 0.62])
DIM = np.float32([0.60, 0.72, 0.80])


def build():
    # 사진 한 장이 세 칸을 관통한다. **칸마다 다른 사진을 쓰면 이어져 보이지 않는다**
    # **가로로 아주 긴 판이라 세로로 얇게 잘린다.** 포스터의 크롭(focus 0.66)을
    # 그대로 쓰면 그 띠가 몸 한가운데에 걸린다 — 포스터는 세로라 괜찮지만
    # 3.2:1 에서는 그 부분만 크게 남는다. 물 쪽으로 내리고 한 단 더 눌러
    # **사진을 결로만** 쓴다. 여기서 읽혀야 하는 건 사진이 아니라 정보다.
    img = duotone(HERO, W, H, DEEP, LIT, contrast=1.18, keep=0.16,
                  focus=0.88, zoom=1.55, offx=HERO_CROP.get('offx', 0.0))
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    img *= 0.46
    # 칸마다 글자가 앉는 자리를 눌러 둔다. 누르는 자리는 이음새를 안 건드린다
    for c in range(3):
        cx = c * TW + TW / 2
        img *= 1 - 0.42 * np.exp(-((xx - cx) / (TW * 0.62)) ** 2) * \
            np.exp(-((yy - H * 0.55) / (H * 0.45)) ** 2)

    # 세 칸을 관통하는 선 하나 — 이게 있어야 세 장이 한 장이었다는 게 보인다
    rule(img, RULE_Y, 0, W, PAPER, 0.26, 3)

    # ── 1칸 · 이름 ────────────────────────────────────────
    x0 = 0
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, 19, 0.42), x0 + TW / 2, SAFE_T + 40,
          color=DIM, a=0.85, anchor='c')
    ns = fit(EV.NAME, BRAND, TW - SEAM * 2, 0.10)
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), x0 + TW / 2, 470, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 25, 0.36), x0 + TW / 2, 545, color=AQUA, anchor='c')
    paint(img, tmask(EV.DATE_EN, BRAND, 42, 0.20), x0 + TW / 2, 700, color=PAPER, anchor='c')
    paint(img, tmask(EV.TIME_EN, BRAND, 24, 0.24), x0 + TW / 2, 760, color=DIM,
          a=0.95, anchor='c')
    paint(img, tmask(EV.TAGLINE, KR, 30, 0.03), x0 + TW / 2, 880, color=PAPER,
          a=0.92, anchor='c')
    lg = logo(84)
    paint(img, lg, x0 + TW / 2, 1060, color=PAPER, a=0.90, anchor='c')

    # ── 2칸 · 타임테이블 ──────────────────────────────────
    x0 = TW
    paint(img, tmask('TIME TABLE', BRAND, 22, 0.34), x0 + TW / 2, SAFE_T + 40,
          color=AQUA, a=0.90, anchor='c')
    top, bot = 400, 1140
    step = (bot - top) / len(EV.TIMETABLE)
    for i, (s, e, name) in enumerate(EV.TIMETABLE):
        yb = top + step * i + step * 0.60
        prog = name in EV.PROGRAM
        if prog:
            box(img, x0 + SEAM, yb - step * 0.62, x0 + TW - SEAM, yb + step * 0.22,
                np.float32([0.20, 0.05, 0.13]), 0.88)
        paint_bl(img, tmask_bl(f'{s}–{e}', BRAND, 22, 0.10), x0 + SEAM + 20, yb,
                 color=ROSE if prog else AQUA, a=0.95)
        paint_bl(img, tmask_bl(name, BRAND, 40 if not prog else 32, 0.08),
                 x0 + TW * 0.44, yb, color=ROSE if prog else PAPER)
        rule(img, yb + step * 0.26, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.10, 1)

    # ── 3칸 · 정보 · 예약 ─────────────────────────────────
    x0 = TW * 2
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, TW - SEAM * 2, 0.12)),
                     0.12), x0 + TW / 2, SAFE_T + 40, color=PAPER, a=0.94, anchor='c')
    # 주소는 VENUE 의 꼬리다. 라벨을 안 붙이고 **값 열에서 그대로 이어** 쓴다 —
    # 라벨 없이 한 줄 띄우면 어느 항목에 붙는 값인지가 안 보인다
    ROWS = [('OPEN', EV.TIME_EN, None), ('VENUE', EV.VENUE, EV.ADDR),
            ('ENTRY', EV.ENTRY, None), ('AFTER', EV.AFTER, None),
            ('NOTICE', EV.AGE, None)]
    y, VX = 430, x0 + SEAM + 150
    for k, v, tail in ROWS:
        paint_bl(img, tmask_bl(k, BRAND, 17, 0.24), x0 + SEAM, y, color=AQUA, a=0.95)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 22,
                               0.14 if v.isascii() else 0.01), VX, y, color=PAPER)
        y += 34
        if tail:
            paint_bl(img, tmask_bl(tail, KR, 18, 0.01), VX, y, color=DIM, a=0.88)
            y += 34
        y += 28
    paint_bl(img, tmask_bl(EV.RULES, KR, 15, 0.01), x0 + SEAM, y + 6, color=DIM, a=0.72)

    # 예매 경로는 제일 크게. 이 줄이 이 판의 목적이다
    paint(img, tmask('예약 · 프로필 링크', KR, 40, 0.02), x0 + TW / 2, 1020,
          color=ROSE, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 21, 0.24), x0 + TW / 2, 1085,
          color=PAPER, a=0.92, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND,
                     min(15, fit(EV.PARTNERS_STR, BRAND, TW - SEAM * 2, 0.16)), 0.16),
          x0 + TW / 2, 1160, color=DIM, a=0.68, anchor='c')

    vignette(img, 0.26, 2.4)
    grain(img, 0.006, 17)
    return np.clip(img, 0, 1)


def cover(tile3):
    """릴스 커버(1080×1920) — 그리드는 이 커버의 가운데를 4:5 로 잘라 보여준다.
    3번 칸을 정확히 가운데 놓아야 잘린 결과가 타일과 같은 자리에 온다."""
    CH = 1920
    top = (CH - TH) // 2
    a = np.asarray(tile3).astype(np.float32) / 255.0
    canvas = np.zeros((CH, TW, 3), np.float32)
    canvas[top:top + TH] = a
    for i in range(top):                        # 위아래는 끝 줄을 늘여 어둡게
        f = (1 - i / top) ** 1.6
        canvas[top - 1 - i] = a[0] * f
        canvas[top + TH + i] = a[-1] * f
    return Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8))


if __name__ == '__main__':
    full = Image.fromarray((build() * 255).astype(np.uint8))
    full.save(os.path.join(OUT, f'event_full{HERO_TAG}.png'), optimize=True)
    tiles = []
    for i in range(3):
        t = full.crop((i * TW, 0, (i + 1) * TW, TH))
        p = os.path.join(OUT, f'event_{i + 1}{HERO_TAG}.png')
        t.save(p, optimize=True)
        tiles.append(t)
        print(p)
    cover(tiles[2]).save(os.path.join(OUT, f'event_3_cover{HERO_TAG}.png'), optimize=True)
    print(os.path.join(OUT, f'event_3_cover{HERO_TAG}.png'), '← 릴스 커버 (1080×1920)')
    print('\n올리는 순서: 3칸 → 2칸 → 1칸  (최신이 왼쪽 위라 거꾸로 올려야 이어진다)')
