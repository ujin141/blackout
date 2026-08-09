"""
Z안 — **세 궤도.** 서로 다른 평면에 놓인 고리 셋이 한 점에서 만납니다.

물 · 혼자 · 일렉을 각각 하나의 궤도로 두고, 기울기를 달리해 겹칩니다.
벤 다이어그램(V안)이 **논리**로 말한다면 이 판은 **공간**으로 말합니다 —
따로 돌던 셋이 오늘 밤 한 자리를 지나갑니다.

**궤도는 타원이어야 합니다.** 정원 셋을 겹치면 평면 위의 도형이고,
납작한 타원을 기울여 겹쳐야 서로 다른 평면에 있는 것으로 보입니다.

만나는 점을 밝히고, 그 자리에 날짜를 둡니다. 시간과 장소가 곧 교점입니다.

python poster_orbit.py  →  out/poster/orbit_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import specks, vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.012, 0.014, 0.028])
AQUA  = np.float32([0.22, 0.90, 1.00])
ROSE  = np.float32([1.00, 0.26, 0.62])
LIME  = np.float32([0.74, 1.00, 0.26])
PAPER = np.float32([0.98, 0.99, 1.00])
DIM   = np.float32([0.58, 0.64, 0.72])


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK

    CX = W / 2
    CY = H * (0.430 if story else 0.425)
    RA = W * 0.360
    RB = W * 0.130                                 # 납작해야 궤도로 보인다

    ORB = [(-28.0, AQUA, 'POOL'), (30.0, ROSE, 'SOLO'), (86.0, LIME, 'ELECTRONIC')]

    for ang, col, _ in ORB:   # 궤도를 세 번 그리며 후광을 쌓는다
        layer = np.zeros((H, W), np.float32)
        cv2.ellipse(layer, (int(CX), int(CY)), (int(RA), int(RB)), ang, 0, 360,
                    1.0, max(2, int(4 * V)), cv2.LINE_AA)
        img += cv2.GaussianBlur(layer, (0, 0), 16 * V)[..., None] * col * 0.85
        img += cv2.GaussianBlur(layer, (0, 0), 46 * V)[..., None] * col * 0.45
        m = layer[..., None]
        img[:] = img * (1 - m * 0.9) + col * m * 0.9

    # **만나는 점.** 세 궤도가 다 지나가는 가운데를 밝힌다
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 교점이 작으면 글자가 얹힐 자리가 없다. **글자를 얹을 거면 그만큼 넓혀야 한다.**
    core = np.exp(-(((xx - CX) / (W * 0.105)) ** 2 + ((yy - CY) / (W * 0.070)) ** 2)) ** 1.4
    img += core[..., None] * PAPER * 1.85
    img += cv2.GaussianBlur(core, (0, 0), W * 0.110)[..., None] * PAPER * 0.45
    specks(img, 120, H * 0.08, H * 0.86, PAPER, 0.15, seed=71, rmax=1.8)

    # 궤도마다 이름표 — 타원의 끝자락에
    for (ang, col, txt), (lx, ly) in zip(ORB, ((0.155, 0.300), (0.845, 0.300), (0.5, 0.688))):
        paint(img, tmask(txt, BRAND, int((24 if len(txt) < 8 else 18) * V), 0.26),
              W * lx, H * ly, color=col, anchor='c')

    # 교점에 날짜
    paint(img, tmask(EV.DATE, KR, int(34 * V), 0.02), CX, CY - 18 * V,
          color=np.float32([0.03, 0.04, 0.07]), anchor='c')
    paint(img, tmask(EV.TIME, KR, int(20 * V), 0.02), CX, CY + 20 * V,
          color=np.float32([0.05, 0.06, 0.09]), anchor='c')

    # ── 글자 ─────────────────────────────────────────────
    M = int(W * 0.075)
    CWD = W - M * 2
    ty = H * (0.062 if story else 0.055)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.85, anchor='c')

    ny = H * (0.128 if story else 0.120)
    img *= (1 - 0.55 * np.exp(-((yy - ny) / (H * 0.068)) ** 2))[..., None]
    ns = justify(EV.NAME, CWD, 0.10, cap=int(138 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.34), W / 2, ny + ns * 0.82,
          color=AQUA, anchor='c')

    ly2 = H * (0.845 if story else 0.835)
    img *= (1 - 0.60 * np.exp(-((yy - (ly2 + 56 * V)) / (H * 0.075)) ** 2))[..., None]
    rule(img, ly2, M, W - M, PAPER, 0.20, max(1, int(2 * V)))
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly2 + 42 * V, color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(f'{EV.VENUE}   {EV.ADDR}', KR, int(17 * V), 0.02),
          W / 2, ly2 + 84 * V, color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, ly2 + 116 * V,
          color=DIM, a=0.55, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * 0.972,
          color=LIME, a=0.88, anchor='c')

    vignette(img, 0.34, 2.1)
    grain(img, 0.007, 42)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'orbit_{k}')
        save(im, f'orbit_{k}')
