"""
M안 — **겹친 튜브 두 개.** 수영장 물건 하나로 둘 다 말합니다.

튜브는 풀파티의 물건입니다. 그런데 튜브는 원이라서, **두 개를 겹치면
혼자 온 사람 둘이 만나는 그림**이 됩니다. 설명 없이 읽히는 유일한 도형입니다.

**겹치는 자리가 제일 밝아야 합니다.** 두 원을 같은 밝기로 두면 그냥 도형 두 개이고,
겹친 데가 빛나야 "여기가 일어나는 자리"로 읽힙니다.

튜브는 물에 떠 있으니 **아래에 반영이 있어야** 합니다. 반영이 없으면 물이 아니라
검은 배경에 그린 도형입니다.

python poster_float.py  →  out/poster/float_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save, info_block
from fest_kit import torus, reflect, specks, vignette, justify, night
from scene_kit import poolscene
from fonts import KR
import event as EV

DEEP    = (0.010, 0.024, 0.048)
SHALLOW = (0.022, 0.056, 0.088)
AQUA    = np.float32([0.30, 0.92, 0.98])
PINK    = np.float32([1.00, 0.28, 0.62])
PAPER   = np.float32([0.98, 0.98, 1.00])
DIM     = np.float32([0.62, 0.72, 0.80])


def build(W, H, story=False):
    V = W / 1080.0
    # **배경은 무늬가 아니라 장면이다.** 물결·타일만 깔면 여전히 상징이라
    # "추상적"이라는 지적이 남는다. 밤 루프탑 수영장에 사람이 있고 디제이가
    # 틀고 있는 그림을 뒤에 두면, 앞의 도형이 무슨 얘기를 하든 일단
    # 무슨 행사인지가 먼저 보인다. 뒤로 물러나야 하니 한 단 눌러 둔다.
    img = poolscene(W, H, story, wy=0.560 if story else 0.530, dj=0.78) * 0.82

    CYm = H * (0.395 if story else 0.395)
    R = W * 0.235
    t = R * 0.115                                   # 튜브 두께
    dx = R * 0.62                                   # 겹치는 정도
    A = (W / 2 - dx, CYm)
    B = (W / 2 + dx, CYm)

    ma = torus(img, A[0], A[1], R, t, AQUA, 0.95, glow=0.30)
    mb = torus(img, B[0], B[1], R, t, PINK, 0.95, glow=0.26)

    # **겹친 자리만 흰빛으로.** 두 색이 만나면 밝아지는 게 빛의 규칙이고,
    # 그 규칙을 지켜야 도형이 아니라 조명으로 보인다
    both = np.minimum(ma, mb)
    img += cv2.GaussianBlur(both, (0, 0), t * 0.9)[..., None] * PAPER * 1.25
    img += cv2.GaussianBlur(both, (0, 0), t * 3.4)[..., None] * np.float32([0.8, 0.95, 1.0]) * 0.75

    # 물에 뜬 것이라 아래로 비친다
    reflect(img, CYm + R + t * 1.6, int(H * 0.20), wob=7.0 * V, damp=0.34, seed=3)
    specks(img, 80, H * 0.08, H * 0.80, PAPER, 0.14, seed=31, rmax=1.8)

    M = int(W * 0.085)
    CWD = W - M * 2

    # 두 원 안에 낱말 하나씩. 원이 무엇을 뜻하는지 원 안에서 말한다
    paint(img, tmask('POOL', BRAND, int(46 * V), 0.20), A[0], CYm, color=AQUA, a=0.95, anchor='c')
    paint(img, tmask('SOLO', BRAND, int(46 * V), 0.20), B[0], CYm, color=PINK, a=0.95, anchor='c')

    ty = H * (0.088 if story else 0.080)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.80, anchor='c')

    # 이름은 튜브 아래. 위에 두면 원과 겹쳐 둘 다 죽는다.
    # **자리는 발치에서 역산한다** — 비율로 두면 짧은 피드에서 정보와 겹친다
    fy = H - 352 * V
    ny = fy - 168 * V
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    img *= (1 - 0.55 * np.exp(-((yy - (ny + 30 * V)) / (H * 0.075)) ** 2))[..., None]
    ns = justify(EV.NAME, CWD, 0.10, cap=int(140 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + 58 * V,
          color=AQUA, anchor='c')

    ly = fy - 52 * V
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.90, anchor='c')

    # **바쁜 배경에서는 발치를 눌러야 글자가 산다.** 그림자를 덧대면 지저분해지고,
    # 배경을 죽이면 깨끗하다 — 이 판 전체에서 지켜 온 규칙과 같다.
    _fy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.68 * np.clip((_fy - (fy - 30 * V)) / (60 * V), 0, 1))
    rule(img, fy, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    # 정보는 **event.INFO 형식 그대로**. 순서·표기를 판마다 바꾸지 않는다
    yb = info_block(img, M, fy + 44 * V, CWD, V, AQUA, PAPER, head_color=PAPER)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 34 * V,
          color=DIM, a=0.60)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 70 * V,
          color=AQUA, a=0.90)


    vignette(img, 0.42, 2.0)
    grain(img, 0.007, 16)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'float_{k}')
        save(im, f'float_{k}')
