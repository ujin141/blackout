"""
Y안 — **믹서.** 디제이 장비를 그대로 판으로 씁니다.

채널 셋을 세우고 라벨을 붙입니다 — POOL · SOLO · ELECTRONIC.
셋 다 페이더가 끝까지 올라가 있고, 마스터 미터가 빨간불에 걸려 있습니다.
**세 채널이 동시에 열려 있다**는 게 이 행사의 구조 그대로입니다.

크루가 디제이 크루라 이 물건이 가장 정직한 은유입니다 —
비유를 만들 필요 없이 실제로 쓰는 기계입니다.

믹서로 읽히려면 넷이 있어야 합니다. **채널 스트립 · 페이더 · 미터 · 노브.**
하나라도 빠지면 그냥 세로 막대 그래프입니다.

python poster_mixer.py  →  out/poster/mixer_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK    = np.float32([0.036, 0.036, 0.040])
PANEL  = np.float32([0.085, 0.088, 0.098])
AQUA   = np.float32([0.22, 0.90, 1.00])
ROSE   = np.float32([1.00, 0.26, 0.62])
LIME   = np.float32([0.74, 1.00, 0.26])
RED    = np.float32([1.00, 0.16, 0.12])
AMBER  = np.float32([1.00, 0.72, 0.18])
PAPER  = np.float32([0.95, 0.96, 0.96])
DIM    = np.float32([0.50, 0.51, 0.54])

CH = [('POOL', AQUA), ('SOLO', ROSE), ('ELECTRONIC', LIME)]


def knob(img, cx, cy, r, col, ang, V):
    """노브 하나. **표시선이 없으면 노브가 아니라 점이다.**"""
    cv2.circle(img, (int(cx), int(cy)), int(r), tuple(float(v) for v in PANEL * 2.2), -1,
               cv2.LINE_AA)
    cv2.circle(img, (int(cx), int(cy)), int(r), tuple(float(v) for v in col),
               max(1, int(2 * V)), cv2.LINE_AA)
    cv2.line(img, (int(cx), int(cy)),
             (int(cx + np.cos(ang) * r * 0.78), int(cy + np.sin(ang) * r * 0.78)),
             tuple(float(v) for v in col), max(2, int(3 * V)), cv2.LINE_AA)


def meter(img, x, y0, y1, w, level, V, seg=16):
    """레벨 미터. 위 세 칸이 빨강이라야 '꽉 찼다'로 읽힌다."""
    h = (y1 - y0) / seg
    for i in range(seg):
        yy = y1 - h * (i + 1)
        on = (i / seg) < level
        c = RED if i >= seg - 3 else (AMBER if i >= seg - 6 else LIME)
        box(img, x, yy + h * 0.16, x + w, yy + h * 0.84,
            c if on else PANEL * 1.7, 1.0 if on else 0.9)


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    M = int(W * 0.070)
    CWD = W - M * 2

    ty = H * (0.062 if story else 0.055)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=DIM, a=0.95)
    paint(img, tmask('3 CH  ·  ALL OPEN', BRAND, int(17 * V), 0.30), W - M, ty,
          color=RED, a=0.95, anchor='r')

    ny = H * (0.135 if story else 0.126)
    ns = justify(EV.NAME, CWD, 0.10, cap=int(132 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(21 * V), 0.34), W / 2, ny + ns * 0.84,
          color=AQUA, anchor='c')

    # ── 채널 스트립 셋 ───────────────────────────────────
    top = H * (0.245 if story else 0.235)
    bot = H * (0.760 if story else 0.745)
    cw = CWD / 3
    for i, (name, col) in enumerate(CH):
        x0 = M + cw * i + cw * 0.06
        x1 = M + cw * (i + 1) - cw * 0.06
        box(img, x0, top, x1, bot, PANEL, 1.0)
        box(img, x0, top, x1, top + 6 * V, col, 1.0)          # 채널 색 띠

        cx = (x0 + x1) * 0.5
        paint(img, tmask(name, BRAND, int((21 if len(name) < 8 else 15) * V), 0.24),
              cx, top + 34 * V, color=col, anchor='c')

        # 노브 셋 — GAIN / HI / LOW. 다 열려 있다
        for j, ang in enumerate((-0.35, -0.15, 0.05)):
            knob(img, cx, top + (86 + j * 62) * V, 22 * V, col, ang * np.pi + np.pi * 1.25, V)

        # 미터 + 페이더. **페이더가 끝까지 올라가 있어야 '열려 있다'가 된다**
        fy0, fy1 = top + 288 * V, bot - 78 * V
        meter(img, cx - 42 * V, fy0, fy1, 14 * V, 0.94, V)
        box(img, cx + 14 * V, fy0, cx + 20 * V, fy1, PANEL * 2.4, 1.0)   # 페이더 홈
        cap_y = fy0 + (fy1 - fy0) * 0.06                       # 끝까지 위
        box(img, cx - 2 * V, cap_y - 13 * V, cx + 36 * V, cap_y + 13 * V, col, 1.0)
        box(img, cx - 2 * V, cap_y - 2 * V, cx + 36 * V, cap_y + 2 * V, INK, 0.9)

        paint(img, tmask('MAX', BRAND, int(14 * V), 0.22), cx, bot - 46 * V,
              color=col, a=0.9, anchor='c')

    # ── 크로스페이더 — 가운데 고정 ───────────────────────
    xy = bot + 44 * V
    box(img, M, xy - 8 * V, W - M, xy + 8 * V, PANEL * 2.4, 1.0)
    box(img, W / 2 - 26 * V, xy - 22 * V, W / 2 + 26 * V, xy + 22 * V, PAPER, 1.0)
    box(img, W / 2 - 26 * V, xy - 3 * V, W / 2 + 26 * V, xy + 3 * V, INK, 1.0)

    # ── 발 ───────────────────────────────────────────────
    fy = H * (0.845 if story else 0.833)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.96, 0.12)), 0.12),
          W / 2, fy, color=PAPER, a=0.95, anchor='c')
    rule(img, fy + 34 * V, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    paint(img, tmask(f'{EV.DATE}   ·   {EV.TIME}', KR, int(24 * V), 0.02), W / 2, fy + 74 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}   {EV.ADDR}', KR, int(16 * V), 0.02), W / 2, fy + 106 * V,
          color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, fy + 136 * V,
          color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * (0.968 if story else 0.962),
          color=LIME, a=0.90, anchor='c')

    vignette(img, 0.30, 2.5)
    grain(img, 0.008, 40)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'mixer_{k}')
        save(im, f'mixer_{k}')
