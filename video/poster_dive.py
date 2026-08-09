"""
AH안 — **다이브.** 장면이 판을 꽉 채우고 글자가 그 위에 얹힙니다.

셋 중 제일 그림 같은 판입니다. 글자를 최소로 줄이고 **행사명 한 줄**만 크게 얹습니다 —
장면이 설명을 다 하고 있으니 글이 거들 필요가 없습니다.

행사명은 **수면 위**에 놓습니다. 물이 어두워서 흰 글자가 그대로 살고,
하늘에 올리면 전구줄·빔과 겹칩니다.

python poster_dive.py  →  out/poster/dive_{feed,story}.png
"""
import numpy as np
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save, info_block
from fest_kit import vignette, justify, night
from scene_kit import poolscene
from fonts import KR
import event as EV

PAPER = np.float32([0.98, 0.99, 1.00])
AQUA  = np.float32([0.36, 0.92, 1.00])
ROSE  = np.float32([1.00, 0.36, 0.68])
DIM   = np.float32([0.62, 0.74, 0.82])


def build(W, H, story=False):
    V = W / 1080.0
    img = poolscene(W, H, story, wy=0.475 if story else 0.450, dj=0.72)
    M = int(W * 0.075)
    CWD = W - M * 2
    yy = np.arange(H, dtype=np.float32)[:, None, None]

    ty = H * (0.058 if story else 0.052)
    img *= (1 - 0.55 * np.clip((H * 0.115 - yy) / (H * 0.115), 0, 1))
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=PAPER, a=0.90, anchor='c')

    # 행사명은 수면 위에 크게. 물이 어두워 흰 글자가 그대로 산다
    ny = H * (0.700 if story else 0.680)
    img *= (1 - 0.66 * np.exp(-((yy - ny) / (H * 0.070)) ** 2))
    ns = justify(EV.NAME, CWD, 0.10, cap=int(150 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask('루프탑 풀파티  ×  솔로파티', KR, int(24 * V), 0.06), W / 2,
          ny + ns * 0.84, color=AQUA, anchor='c')
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.13)), 0.13),
          W / 2, ny + ns * 0.84 + 52 * V, color=PAPER, a=0.94, anchor='c')

    fy = H - 322 * V
    img *= (1 - 0.76 * np.clip((yy - (fy - 30 * V)) / (60 * V), 0, 1))
    rule(img, fy, M, W - M, PAPER, 0.20, max(1, int(2 * V)))
    yb = info_block(img, M, fy + 42 * V, CWD, V, AQUA, PAPER, step=42 * V)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 30 * V,
          color=DIM, a=0.62)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 64 * V,
          color=ROSE, a=0.92)

    vignette(img, 0.36, 2.1)
    grain(img, 0.007, 64)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'dive_{k}')
        save(im, f'dive_{k}')
