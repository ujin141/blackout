"""
G안 — **라인업 블록.** 페스티벌 포스터의 원형이자 가장 강한 형식입니다.

사진도 그림도 안 씁니다. **판 전체가 라인업 하나**입니다.
줄마다 폭을 꽉 채우면 글자 크기가 저절로 등급이 되고 — 헤드라이너가 제일 크고
아래로 갈수록 작아집니다 — 블록 전체가 한 덩어리 비석처럼 섭니다.
코첼라부터 지금까지 안 바뀐 문법이라 설명이 필요 없습니다.

**이 판의 유일한 재료는 글자 크기입니다.** 그래서 장식을 하나도 안 넣습니다 —
장식을 넣는 순간 크기 차이가 안 보이고, 크기 차이가 안 보이면 등급이 사라집니다.
색도 흰색 하나에 청록 한 점뿐입니다.

등급은 타임테이블 순서가 아니라 **자리(billing)** 로 나눕니다.
마지막에 트는 사람이 헤드라이너라 AROS·DEMIC 이 맨 위입니다.

python poster_bill.py  →  out/poster/bill_{feed,story}.png
"""
import numpy as np
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
import cv2
from fest_kit import justify, night, vignette, sky
from fonts import KR
import event as EV

INK    = np.float32([0.028, 0.030, 0.038])
PAPER  = np.float32([0.96, 0.96, 0.94])
ACCENT = np.float32([0.30, 0.86, 0.88])          # 청록 한 점
DIM    = np.float32([0.58, 0.60, 0.64])

# 자리(billing). 타임테이블 순서가 아니라 누가 헤드라이너인지로 나눈다 —
# 마지막에 트는 사람이 맨 위다. 한 줄에 몰아 넣으면 폭에 맞느라 다 같은 크기가 된다.
TIERS = [
    (['AROS', 'DEMIC'], 1.00),
    (['V', 'LYNN', 'TS'], 0.74),
    (['CHIPS', 'HEIDY'], 0.56),
]


def build(W, H, story=False):
    V = W / 1080.0                                # 작은 글자는 폭 기준
    # **너무 어두운 것도 실패다.** 순수 타이포라 검정을 그대로 깔았더니 평균 0.05 —
    # 피드에서 그냥 검은 사각형이 된다. 위에서 아래로 아주 옅게 기울이고
    # 라인업 뒤에 옅은 빛을 깔아 판이 있다는 걸 보이게 한다.
    img = sky(W, H, [(0.0, (0.070, 0.072, 0.088)), (0.55, (0.034, 0.036, 0.046)),
                     (1.0, (0.018, 0.019, 0.026))])
    M = int(W * 0.085)
    CW = W - M * 2

    # ── 머리 ─────────────────────────────────────────────
    y = H * (0.070 if story else 0.078)
    paint(img, tmask('BLACKOUT CREW PRESENTS', BRAND, int(20 * V), 0.42),
          W / 2, y, color=DIM, a=0.85, anchor='c')

    # 행사 이름. 블록 위에 얹히는 유일한 큰 글자
    ny = H * (0.150 if story else 0.165)
    ns = justify(EV.NAME, CW, 0.10, cap=int(150 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.34),
          W / 2, ny + ns * 0.78, color=ACCENT, a=0.95, anchor='c')

    # ── 라인업 블록 ──────────────────────────────────────
    # 줄마다 폭을 채운다. 크기가 곧 등급이라 값을 따로 정하지 않는다.
    top = H * (0.300 if story else 0.325)
    bot = H * (0.735 if story else 0.720)
    rows = []
    for names, weight in TIERS:
        joined = '  ·  '.join(names)
        s = justify(joined, CW * (0.98 if weight == 1.0 else 0.94), 0.06)
        rows.append((joined, int(s * weight if weight < 1 else s), weight))
    # 프로그램 줄. DJ 가 아니라서 색과 크기로 갈라 둔다
    prog = '  ·  '.join(sorted(EV.PROGRAM))
    rows.append((prog, int(justify(prog, CW * 0.58, 0.16)), 0.0))

    heights = [tmask(t, BRAND, s, 0.06).shape[0] for t, s, _ in rows]
    gap = (bot - top - sum(heights)) / max(len(rows) - 1, 1)
    cy = top
    for (txt, s, weight), h in zip(rows, heights):
        col = PAPER if weight else ACCENT
        paint(img, tmask(txt, BRAND, s, 0.06 if weight else 0.16),
              W / 2, cy + h / 2, color=col, a=1.0 if weight >= 0.6 else 0.86, anchor='c')
        cy += h + gap

    # ── 발 ───────────────────────────────────────────────
    fy = H * (0.815 if story else 0.800)
    rule(img, fy, M, W - M, PAPER, 0.22, max(1, int(2 * V)))
    paint(img, tmask(EV.DATE, KR, int(30 * V), 0.02), W / 2, fy + 44 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(20 * V), 0.02),
          W / 2, fy + 84 * V, color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(17 * V), 0.02), W / 2, fy + 116 * V,
          color=DIM, a=0.72, anchor='c')

    py = H * (0.930 if story else 0.925)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(14 * V), 0.30), W / 2, py,
          color=DIM, a=0.60, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), W / 2, py + 36 * V,
          color=ACCENT, a=0.80, anchor='c')

    # 라인업 블록 뒤의 옅은 빛. 글자가 떠 있지 않고 판 위에 앉은 것으로 보인다
    yy = np.arange(H, dtype=np.float32)
    band = np.exp(-((yy - (top + bot) / 2) / (H * 0.24)) ** 2)
    img += band[:, None, None] * np.float32([0.055, 0.058, 0.070])

    vignette(img, 0.30, 2.6)
    grain(img, 0.006, 4)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'bill_{k}')
        save(im, f'bill_{k}')
