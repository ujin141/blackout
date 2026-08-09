"""
J안 — **무대.** 페스티벌 사진에서 가장 많이 찍히는 그 장면입니다.

트러스에서 내려오는 빔, 공기 중의 연기, 손 든 관객, 그 위의 하늘에 이름.
사진은 안 씁니다 — 크루에 공연 사진이 없어서 전부 그립니다(사이트도 같은 방식).

**빔은 선이 아니라 원뿔입니다.** 끝으로 갈수록 넓어지고 옅어져야 공기가 보이고,
선으로 그으면 레이저 포인터가 됩니다. 그리고 **연기가 없으면 빔도 없습니다** —
빛은 공기 중의 먼지에 부딪혀야 보이니까요.

**관객은 머리만 늘어놓으면 자갈밭입니다.** 가끔 손을 든 사람이 섞여야
사람으로 읽히고, 그 순간 판이 "지금 열리고 있는 행사"가 됩니다.

python poster_stage.py  →  out/poster/stage_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import sky, beams, haze, crowd, specks, vignette, justify, night
from fonts import KR
import event as EV

TOP    = (0.020, 0.018, 0.038)
HORZ   = (0.085, 0.030, 0.090)
VIOLET = np.float32([0.62, 0.30, 1.00])
MAGENT = np.float32([1.00, 0.25, 0.62])
PAPER  = np.float32([0.97, 0.96, 0.98])
DIM    = np.float32([0.70, 0.66, 0.76])


def truss(img, y, x0, x1, color, V):
    """트러스. 빔이 어디서 나오는지 보여야 무대가 된다 —
    광원이 안 보이면 빛이 허공에서 생긴 것처럼 뜬다."""
    th = max(2, int(4 * V))
    box(img, x0, y, x1, y + th * 2, color, 1.0)
    box(img, x0, y - th * 7, x1, y - th * 5, color, 1.0)
    n = 22
    for i in range(n):                              # X 자 보강재
        ax = x0 + (x1 - x0) * i / n
        bx = x0 + (x1 - x0) * (i + 1) / n
        cv2.line(img, (int(ax), int(y - th * 5)), (int(bx), int(y)),
                 tuple(float(v) for v in color), th, cv2.LINE_AA)
        cv2.line(img, (int(bx), int(y - th * 5)), (int(ax), int(y)),
                 tuple(float(v) for v in color), th, cv2.LINE_AA)


def build(W, H, story=False):
    V = W / 1080.0
    img = sky(W, H, [(0.0, TOP), (0.55, TOP), (0.86, HORZ), (1.0, (0.03, 0.01, 0.03))])

    TY = H * (0.300 if story else 0.285)            # 트러스 높이
    CY = H * (0.760 if story else 0.745)            # 관객 머리 높이

    haze(img, TY, CY, np.float32([0.35, 0.22, 0.55]), 0.30, seed=5)
    # 빔 두 벌 — 색이 하나면 조명이 아니라 안개다. 각도를 달리해 겹친다
    beams(img, W * 0.32, TY, 7, 0.62, H * 0.78, VIOLET, 0.42, seed=3, wobble=0.05)
    beams(img, W * 0.68, TY, 7, 0.62, H * 0.78, MAGENT, 0.34, seed=8, wobble=0.05)
    haze(img, TY, CY, np.float32([0.30, 0.16, 0.46]), 0.16, seed=9)
    specks(img, 220, TY, CY, np.float32([1.0, 0.9, 1.0]), 0.22, seed=15, rmax=2.0)

    truss(img, TY, 0, W, np.float32([0.045, 0.040, 0.060]), V)   # 음수 x 는 뒤에서부터 잘린다
    # 트러스에 매달린 등 — 빔의 시작점을 찍어 준다
    for i in range(14):
        x = W * (0.06 + 0.88 * i / 13)
        c = VIOLET if i % 2 == 0 else MAGENT
        cv2.circle(img, (int(x), int(TY + 10 * V)), max(2, int(6 * V)),
                   tuple(float(v) for v in c * 0.9), -1, cv2.LINE_AA)
    glowline = cv2.GaussianBlur(
        (np.abs(np.mgrid[0:H, 0:W][0] - (TY + 10 * V)) < 8 * V).astype(np.float32),
        (0, 0), 18 * V)
    img += glowline[..., None] * np.float32([0.55, 0.35, 0.85]) * 0.30

    # 관객이 얇으면 바닥 무늬가 된다. 덩어리로 차야 사람이 모인 것으로 보인다
    crowd(img, CY, H * 0.30, np.float32([0.010, 0.008, 0.016]), seed=11)

    # ── 글자 ─────────────────────────────────────────────
    M = int(W * 0.085)
    CWD = W - M * 2
    ny = H * (0.140 if story else 0.130)
    ns = justify(EV.NAME, CWD, 0.10, cap=int(150 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + ns * 0.80,
          color=np.float32([1.0, 0.55, 0.80]), anchor='c')

    # 라인업은 트러스 바로 위 — 무대에 걸린 것처럼 보인다
    ly = TY - 74 * V
    lin = EV.LINEUP_STR
    paint(img, tmask(lin, BRAND, int(justify(lin, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.95, anchor='c')
    rule(img, ly + 34 * V, W / 2 - CWD * 0.30, W / 2 + CWD * 0.30, VIOLET, 0.55,
         max(1, int(2 * V)))

    # 날짜는 관객 위 어두운 자리에 — 실루엣이 배경을 죽여 놨다
    dy = H * (0.880 if story else 0.872)
    paint(img, tmask(EV.DATE, KR, int(38 * V), 0.02), W / 2, dy, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(21 * V), 0.02),
          W / 2, dy + 44 * V, color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02), W / 2, dy + 74 * V,
          color=DIM, a=0.68, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, H * 0.958,
          color=DIM, a=0.55, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * 0.980,
          color=np.float32([1.0, 0.55, 0.80]), a=0.75, anchor='c')

    vignette(img, 0.40, 2.0)
    grain(img, 0.007, 10)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'stage_{k}')
        save(im, f'stage_{k}')
