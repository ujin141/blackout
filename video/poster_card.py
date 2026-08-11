"""
AC안 — **사진 + 정보판.** 사람들이 실제로 캡처해서 돌리는 그 형태입니다.

위 절반은 사진, 아래 절반은 **글자만 있는 판**입니다.
사진 위에 글자를 얹지 않습니다 — 얹으면 사진도 글자도 반씩 죽고,
갈라놓으면 둘 다 온전합니다. 인스타에서 정보를 확인하려고 확대할 때
사진이 아니라 판을 보게 됩니다.

정보는 **표**입니다. 라벨과 값을 왼쪽 두 열로 세우고, 값 열의 기준선을 맞춥니다.
문장으로 늘어놓으면 읽는 게 아니라 훑게 되고, 훑으면 날짜를 놓칩니다.

python poster_card.py  →  out/poster/card_{feed,story}.png
"""
import os
import numpy as np
from poster_kit import (BRAND, SIZES, STOCK, tmask, tmask_bl, paint, paint_bl,
                        rule, box, duotone, grain, save)
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

MIXER = os.path.join(STOCK, 'mixer-cc0.jpg')

M_DEEP = np.float32([0.030, 0.030, 0.045])
M_LIT  = np.float32([0.72, 0.50, 0.28])            # 장비에 닿은 따뜻한 빛
PANEL  = np.float32([0.055, 0.058, 0.066])
PAPER  = np.float32([0.97, 0.97, 0.96])
AMBER  = np.float32([1.00, 0.72, 0.28])
DIM    = np.float32([0.58, 0.59, 0.62])

ROWS = [('일시', f'{EV.DATE}   {EV.TIME_EN}'),
        ('장소', EV.VENUE),
        ('주소', EV.ADDR),
        ('라인업', EV.LINEUP_STR),
        ('입장', EV.ENTRY),
        ('AFTER', EV.AFTER),
        ('안내', EV.AGE)]


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + PANEL

    CUT = int(H * (0.520 if story else 0.500))
    # **사람이 아니라 장비가 보여야** 디제잉으로 읽힌다. 위쪽에 다리가 들어와
    # 아래로 더 파고들어 크롭한다.
    img[:CUT] = duotone(MIXER, W, CUT, M_DEEP, M_LIT, contrast=1.22, keep=0.14,
                        focus=0.70, zoom=1.45)
    # 사진 아래끝을 판 색으로 녹인다. 딱 자르면 두 장을 붙인 것처럼 보인다
    fade = int(CUT * 0.16)
    k = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None] ** 1.4
    img[CUT - fade:CUT] = img[CUT - fade:CUT] * (1 - k) + PANEL * k
    # 위쪽도 살짝 눌러 머리글 자리를 만든다
    ys = np.arange(CUT, dtype=np.float32)[:, None, None] / CUT
    img[:CUT] *= (1 - 0.66 * np.clip((0.34 - ys) / 0.34, 0, 1))

    M = int(W * 0.080)
    CWD = W - M * 2

    ty = H * (0.055 if story else 0.048)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.92)
    paint(img, tmask('ROOFTOP', BRAND, int(17 * V), 0.30), W - M, ty,
          color=AMBER, a=0.92, anchor='r')

    # ── 정보판 ───────────────────────────────────────────
    ny = CUT + 62 * V
    ns = justify(EV.NAME, CWD, 0.08, cap=int(126 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), M, ny, color=PAPER)
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.30), M, ny + ns * 0.82,
          color=AMBER)

    y0 = ny + ns * 0.82 + 66 * V
    step = (H * (0.955 if story else 0.950) - 96 * V - y0) / len(ROWS)
    rule(img, y0 - 28 * V, M, W - M, PAPER, 0.24, max(1, int(2 * V)))
    for i, (kk, vv) in enumerate(ROWS):
        yb = y0 + step * i
        paint_bl(img, tmask_bl(kk, KR, int(17 * V), 0.06), M, yb, color=AMBER, a=0.95)
        # 값이 길면 폭에 맞춰 줄인다. 넘치면 잘린 것으로 보인다
        sz = int(22 * V)
        while tmask(vv, KR, sz, 0.01).shape[1] > CWD * 0.78 and sz > 12:
            sz -= 1
        paint_bl(img, tmask_bl(vv, KR, sz, 0.01), M + CWD * 0.20, yb, color=PAPER)
        rule(img, yb + 20 * V, M, W - M, PAPER, 0.09, max(1, int(1 * V)))

    paint_bl(img, tmask_bl(EV.RULES, KR, int(13 * V), 0.01),
             M, y0 + step * len(ROWS) + 16 * V, color=DIM, a=0.72)
    fy = y0 + step * len(ROWS) + 44 * V
    paint(img, tmask(EV.RESERVE, KR, int(18 * V), 0.01), M, fy, color=DIM, a=0.98)
    paint(img, tmask(EV.HANDLE, BRAND, int(18 * V), 0.24), W - M, fy,
          color=AMBER, a=0.98, anchor='r')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(12 * V), 0.30), M, fy + 34 * V,
          color=DIM, a=0.62)

    vignette(img, 0.20, 2.8)
    grain(img, 0.007, 48)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'card_{k}')
        save(im, f'card_{k}')
