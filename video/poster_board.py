"""
**타임테이블 판 — 브랜드 톤.** 검정 · 흰색 · 은색뿐입니다.

    python poster_board.py            피드 · 스토리 · 정사각
    python poster_board.py story      골라서

`poster_time`(시안·자홍)과 `poster_lane`(라임)은 시안 비교용으로 색을 넣은
판입니다. 실제로 나가는 판은 **크루 판·개인 판과 같은 팔레트**여야 합니다 —
프로필 격자에 같이 걸렸을 때 색 하나가 튀면 그 판만 남의 것처럼 보입니다.

`poster_dj7` 이 정한 규칙을 그대로 따릅니다. 판은 무채색이고, 강조는 색이
아니라 **밝기와 크기**로 합니다. 여기는 사람이 없으므로 색이 아예 없습니다.

## 표가 두 층이다

솔로파티 90분 동안 다른 부스에서 세 세트가 돕니다. 그 셋을 같은 크기로
세우면 솔로파티가 끝나고 다시 시작하는 것처럼 읽힙니다 — **들여쓰고 줄이고
왼쪽에 세로선을 그어** 안에 든 것으로 만듭니다.

솔로파티 줄만 판을 깝니다. DJ 가 아니라 프로그램이라는 걸 색으로 말할 수
없으니(무채색이라) **면으로** 말합니다.
"""
import sys

import numpy as np

from poster_kit import (BRAND, tmask, tmask_bl, paint, paint_bl, rule, box,
                        glow, outline, bloom, grain, logo, sign, save)
from poster_dj3 import chrome
from poster_dj4 import nebula, fringe
from poster_dj7 import PAPER, SILVER, STEEL, DIM, SLOGAN
from fest_kit import justify, night, vignette, rays, specks, haze
from fonts import KR, KRB
import event as EV

# 스토리만 안전영역을 잡는다. 피드·정사각은 UI 가 판을 안 덮는다.
SIZES = {'feed': (1080, 1350, False),
         'story': (1080, 1920, True),
         'sq': (1080, 1080, False)}


def build(W, H, story=False):
    V = W / 1080.0
    y0, y1 = (H * 0.085, H * 0.876) if story else (H * 0.030, H * 0.972)
    M = int(W * 0.082)

    img = np.repeat(np.repeat(np.float32([0.015, 0.015, 0.020])[None, None, :],
                              H, 0), W, 1).copy()
    # 빛은 표 위쪽에서 온다. 가운데에 두면 표 한가운데가 밝아져 줄마다
    # 읽히는 정도가 갈린다 — 개인 판에서 이미 한 번 겪었다
    # **개인 판만큼 세우면 안 된다.** 거기는 인물이 구름을 가리지만 여기는
    # 표가 통째로 구름 위에 뜬다 — 반으로 죽이고, 표가 지나가는 구간은
    # 한 번 더 떨어뜨린다. 줄마다 읽히는 정도가 갈리는 게 제일 나쁘다.
    img += nebula(W, H, W * 0.50, H * 0.16, STEEL * 1.5, SILVER, seed=71,
                  spread=0.86) * 0.62
    rays(img, W * 0.50, H * 0.14, 30, int(26 * V), int(H * 0.58), PAPER, 0.020,
         phase=0.13, duty=0.26)
    haze(img, int(H * 0.70), int(H * 0.99), SILVER, 0.038, seed=17)

    # ── 머리 ─────────────────────────────────────────────
    # **아이디는 발치에 한 번만.** 위아래 둘 다 넣었더니 같은 말이 두 번이었고,
    # 위쪽 것은 성운에 묻혀 읽히지도 않았다 — 한 칸을 버린 셈이다
    lg = logo(int(44 * V))
    paint(img, lg, W / 2 - lg.shape[1] / 2, y0 + 40 * V, color=PAPER, a=0.95)
    paint(img, tmask('SEOUL', BRAND, int(13 * V), 0.34), M, y0 + 40 * V,
          color=DIM, a=0.80, anchor='l')
    paint(img, tmask(EV.DATE_EN, BRAND, int(15 * V), 0.20), W - M, y0 + 40 * V,
          color=SILVER, a=0.92, anchor='r')

    ny = y0 + 132 * V
    ns = justify(EV.NAME, W - M * 2, 0.06, cap=int(118 * V))
    nm = tmask(EV.NAME, BRAND, ns, 0.06)
    glow(img, nm, W / 2, ny, SILVER, 0.22, int(24 * V), anchor='c')
    chrome(img, nm, W / 2, ny, PAPER, STEEL)
    paint(img, outline(nm, max(2, int(2.6 * V))), W / 2, ny, color=PAPER,
          a=0.90, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(19 * V), 0.32), W / 2, ny + ns * 0.72,
          color=SILVER, a=0.86, anchor='c')

    # ── 표 ───────────────────────────────────────────────
    top = ny + ns * 0.72 + 56 * V
    rule(img, top - 22 * V, M, W - M, SILVER, 0.42, max(2, int(2 * V)))
    paint(img, tmask('TIME TABLE', BRAND, int(13 * V), 0.34), M, top - 44 * V,
          color=DIM, a=0.70)

    bot = y1 - (232 if story else 244) * V
    # 표 구간을 한 번 더 누른다. 띠를 두르지 않고 위아래로 풀어야 얹은
    # 판으로 안 읽힌다
    yv = np.arange(H, dtype=np.float32)[:, None, None]
    fade = (np.clip((yv - (top - 40 * V)) / (H * 0.05), 0, 1)
            * np.clip((bot + 40 * V - yv) / (H * 0.05), 0, 1))
    img *= (1 - 0.46 * fade)

    rows = EV.BOARD
    step = (bot - top) / len(rows)
    for i, (s, e, name, sub) in enumerate(rows):
        yb = top + step * i + step * 0.66
        prog = name in EV.PROGRAM

        if prog:
            # 색이 없으니 면으로 가른다. **DJ 이름과 같은 층으로 읽히면 안 된다**
            box(img, M, yb - step * 0.62, W - M, yb + step * 0.24, STEEL, 0.42)
            box(img, M, yb - step * 0.62, M + int(5 * V), yb + step * 0.24,
                PAPER, 0.90)
        if sub:
            # 솔로파티 **안에서** 도는 세트. 세로선이 그 소속을 말한다
            box(img, M + int(30 * V), yb - step * 0.54, M + int(33 * V),
                yb + step * 0.16, SILVER, 0.55)

        ind = (58 if sub else 24) * V
        paint_bl(img, tmask_bl(f'{s}–{e}', BRAND, int((17 if sub else 21) * V), 0.10),
                 M + ind, yb, color=SILVER, a=0.74 if sub else 0.92)
        nsz = int((25 if sub else (37 if not prog else 30)) * V)
        paint_bl(img, tmask_bl(name, BRAND, nsz, 0.09),
                 M + (W - M * 2) * (0.42 if sub else 0.36), yb,
                 color=PAPER, a=0.82 if sub else 1.0)
        if not sub and not prog:
            rule(img, yb + step * 0.26, M, W - M, SILVER, 0.14, max(1, int(1 * V)))

    # ── 발 ───────────────────────────────────────────────
    rule(img, bot + 26 * V, M, W - M, SILVER, 0.42, max(2, int(2 * V)))
    fy = bot + 66 * V
    paint_bl(img, tmask_bl(f'{EV.VENUE}   {EV.ADDR}', KR, int(19 * V), 0.01),
             M, fy, color=PAPER, a=0.95)
    paint_bl(img, tmask_bl(EV.ENTRY, KR, int(17 * V), 0.01), M, fy + 34 * V,
             color=SILVER, a=0.92)
    paint_bl(img, tmask_bl(EV.AGE, KR, int(16 * V), 0.01), M, fy + 64 * V,
             color=DIM, a=0.85)
    paint_bl(img, tmask_bl(f'AFTER PARTY   {EV.AFTER}', KR, int(16 * V), 0.01),
             M, fy + 94 * V, color=SILVER, a=0.82)
    paint(img, tmask(EV.RESERVE, KRB, int(18 * V), 0.02), W - M, fy + 20 * V,
          color=PAPER, a=0.96, anchor='r')
    sign(img, W - M, fy + 62 * V, size=int(15 * V), color=SILVER, a=0.80,
         anchor='r')
    paint(img, tmask(SLOGAN, BRAND, int(12 * V), 0.30), M, fy + 134 * V,
          color=DIM, a=0.58)

    if story:
        # **발치가 그냥 검으면 판이 거기서 끝난 게 아니라 잘린 것으로 읽힌다.**
        # UI 가 덮는 자리라 글자는 못 넣지만 빛은 깔 수 있다 — 개인 판과 같은 처리
        gy = np.arange(H, dtype=np.float32)
        gx = np.arange(W, dtype=np.float32)
        spill = (np.exp(-((gy - H * 0.960) / (H * 0.070)) ** 2)[:, None]
                 * np.exp(-((gx - W * 0.5) / (W * 0.58)) ** 2)[None, :])
        img += spill[..., None] * SILVER * 0.22
        rule(img, int(y1), 0, W, SILVER, 0.34, max(1, int(2 * V)))

    specks(img, 120, 0, int(y1), PAPER, 0.15, seed=31, rmax=2.4)
    bloom(img, 0.82, 16 * V, 0.18, PAPER)
    fringe(img, 0.0012)
    vignette(img, 0.44, 2.2)
    grain(img, 0.006, 23)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.lower() for a in sys.argv[1:]] or list(SIZES)
    for k in want:
        if k not in SIZES:
            raise SystemExit(f'{k} 은 없는 크기입니다 — {", ".join(SIZES)}')
        w, h, st = SIZES[k]
        im = build(w, h, st)
        night(im, f'board_{k}')
        save(im, f'board_{k}')
