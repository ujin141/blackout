"""
O안 — **레인.** 수영장의 짜임을 그대로 정보 구조로 씁니다.

수영장은 로프로 칸이 나뉘어 있고, 한 칸에 한 사람씩 들어갑니다.
그래서 레인은 **혼자**의 그림입니다 — 그걸 라인업 표로 쓰면
칸마다 DJ 이름이 들어가고, 판 전체가 수영장 도면이 됩니다.

**한 자리만 로프를 뺍니다.** 두 칸이 트인 그 자리가 솔로파티이고,
나머지가 다 막혀 있어야 트인 한 칸이 보입니다.

로프는 선이 아니라 **구슬이 꿰인 줄**입니다. 선만 그으면 밑줄입니다.

python poster_lane.py  →  out/poster/lane_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, tmask_bl, paint, paint_bl, rule, box, grain, save
from fest_kit import water, rope, vignette, justify, night
from fonts import KR
import event as EV

DEEP    = (0.014, 0.034, 0.058)
SHALLOW = (0.026, 0.062, 0.094)
LIME    = np.float32([0.72, 0.98, 0.35])
BUOY    = np.float32([0.96, 0.97, 0.98])
BUOY2   = np.float32([0.30, 0.70, 0.86])
PAPER   = np.float32([0.97, 0.99, 1.00])
DIM     = np.float32([0.60, 0.74, 0.82])


def build(W, H, story=False):
    V = W / 1080.0
    img = water(W, H, DEEP, SHALLOW, amp=0.11, seed=8)

    M = int(W * 0.075)
    CWD = W - M * 2

    # ── 머리 ─────────────────────────────────────────────
    ty = H * (0.070 if story else 0.064)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.80, anchor='c')
    ny = H * (0.150 if story else 0.142)
    ns = justify(EV.NAME, CWD, 0.10, cap=int(138 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + ns * 0.82,
          color=LIME, anchor='c')

    # ── 레인 ─────────────────────────────────────────────
    # 타임테이블 여덟 줄이 그대로 여덟 레인이 된다
    top = H * (0.265 if story else 0.255)
    bot = H * (0.790 if story else 0.775)
    # 병행 슬롯까지 다 보이는 열한 줄(EV.BOARD). 하위 줄은 **트인 칸 안에**
    # 들어가므로 로프를 안 긋고 레인 번호도 안 붙인다 — 별도 레인이 아니다
    rows = EV.BOARD
    lh = (bot - top) / len(rows)
    lane_no = 0
    for i, (s, e, name, sub) in enumerate(rows):
        y0 = top + lh * i
        cy = y0 + lh * 0.5
        prog = name in EV.PROGRAM

        if prog or sub:
            # **트인 칸.** 위아래 로프를 안 그리고 바닥을 밝혀 둔다
            box(img, M, y0 + (lh * 0.06 if prog else 0), W - M,
                y0 + lh * (0.94 if i == len(rows) - 1 or not rows[i + 1][3] else 1.0),
                np.float32([0.10, 0.20, 0.16]), 0.85)
            box(img, M, y0, M + int(6 * V), y0 + lh, LIME, 1.0)

        kb = tmask_bl(f'{s}–{e}', BRAND, int((17 if sub else 21) * V), 0.10)
        vb = tmask_bl(name, BRAND,
                      int((24 if sub else (34 if not prog else 30)) * V), 0.10)
        yb = cy + vb[0].shape[0] * 0.5
        paint_bl(img, kb, M + (54 if sub else 26) * V, yb, color=DIM,
                 a=0.80 if sub else 0.95)
        paint_bl(img, vb, M + CWD * (0.36 if sub else 0.30), yb,
                 color=LIME if prog else PAPER, a=0.86 if sub else 1.0)
        # 레인 번호 — 수영장은 칸마다 번호가 붙어 있다. 하위 줄은 안 센다
        if not sub:
            lane_no += 1
            paint(img, tmask(f'{lane_no:02d}', BRAND, int(20 * V), 0.14),
                  W - M - 26 * V, cy, color=DIM, a=0.55, anchor='r')

        # 칸을 가르는 로프. **트인 칸의 위아래는 긋지 않는다**
        if (i > 0 and not prog and not sub
                and not rows[i - 1][3] and rows[i - 1][2] not in EV.PROGRAM):
            rope(img, y0, W, BUOY, max(3, int(7 * V)), int(14 * V), alt=BUOY2)

    # ── 발 ───────────────────────────────────────────────
    fy = H * (0.845 if story else 0.832)
    rule(img, fy, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    paint(img, tmask(EV.DATE, KR, int(32 * V), 0.02), W / 2, fy + 44 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(20 * V), 0.02),
          W / 2, fy + 84 * V, color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02), W / 2, fy + 114 * V,
          color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, H * 0.945,
          color=DIM, a=0.55, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * 0.972,
          color=LIME, a=0.85, anchor='c')

    vignette(img, 0.40, 2.1)
    grain(img, 0.007, 20)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'lane_{k}')
        save(im, f'lane_{k}')
