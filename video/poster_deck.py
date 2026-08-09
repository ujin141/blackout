"""
AG안 — **데크.** 위는 장면, 아래는 정보판입니다.

**그림 위에 글자를 얹지 않습니다.** 얹으면 그림도 글자도 반씩 죽고,
갈라놓으면 둘 다 온전합니다. 인스타에서 정보를 확인하려고 확대할 때
그림이 아니라 판을 보게 됩니다.

장면은 `scene_kit.poolscene()` 이 그립니다 — 밤 루프탑 수영장에 사람이 있고
디제이가 틀고 있는 그림이라 해석할 게 없습니다.

python poster_deck.py  →  out/poster/deck_{feed,story}.png
"""
import numpy as np
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save, info_block
from fest_kit import vignette, justify, night
from scene_kit import poolscene
from fonts import KR
import event as EV

PANEL = np.float32([0.030, 0.036, 0.046])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA  = np.float32([0.36, 0.92, 1.00])
DIM   = np.float32([0.62, 0.74, 0.82])


def build(W, H, story=False):
    V = W / 1080.0
    CUT = int(H * (0.575 if story else 0.545))

    img = np.zeros((H, W, 3), np.float32) + PANEL
    img[:CUT] = poolscene(W, CUT, story, wy=0.66, dj=0.74)
    # 장면 아래끝을 판 색으로 녹인다. **딱 자르면 두 장을 붙인 것처럼 보인다**
    fade = int(CUT * 0.13)
    k = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None] ** 1.5
    img[CUT - fade:CUT] = img[CUT - fade:CUT] * (1 - k) + PANEL * k

    M = int(W * 0.075)
    CWD = W - M * 2
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img[:CUT] *= (1 - 0.62 * np.clip((H * 0.115 - yy[:CUT]) / (H * 0.115), 0, 1))

    ty = H * (0.052 if story else 0.046)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.92)
    paint(img, tmask('ROOFTOP POOL', BRAND, int(17 * V), 0.30), W - M, ty,
          color=AQUA, a=0.92, anchor='r')

    ny = CUT + 54 * V
    ns = justify(EV.NAME, CWD, 0.08, cap=int(124 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), M, ny, color=PAPER)
    paint(img, tmask('루프탑 풀파티 · 솔로파티', KR, int(24 * V), 0.04), M, ny + ns * 0.84,
          color=AQUA)

    # **라인업도 발치에서 역산한다.** 이름 바로 밑에 붙이면 스토리(1920)에서
    # 그 아래가 250px 넘게 비어 판이 끊긴 것처럼 보인다.
    fy = H - 352 * V
    ly = fy - 62 * V
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD, 0.12)), 0.12),
          M, ly, color=PAPER, a=0.97)
    rule(img, fy, M, W - M, PAPER, 0.22, max(1, int(2 * V)))
    yb = info_block(img, M, fy + 44 * V, CWD, V, AQUA, PAPER)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 34 * V,
          color=DIM, a=0.62)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 70 * V,
          color=AQUA, a=0.92)

    vignette(img, 0.22, 2.6)
    grain(img, 0.007, 62)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'deck_{k}')
        save(im, f'deck_{k}')
