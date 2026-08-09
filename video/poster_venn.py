"""
V안 — **삼중 벤.** 세 개가 겹친다는 걸 도형 하나로 말합니다.

원 셋이 서로 겹치고, 셋이 다 겹치는 가운데 자리에 행사 이름이 앉습니다.
POOL · SOLO · ELECTRONIC — 각 원에 하나씩. **설명이 필요 없는 유일한 도형**입니다.

**가운데가 제일 밝아야 합니다.** 세 원을 같은 밝기로 두면 도형 셋이고,
셋이 겹친 자리만 흰빛이어야 "여기가 이 행사다"로 읽힙니다.
빛은 겹칠수록 밝아지고, 그 규칙을 지켜야 도형이 아니라 조명이 됩니다.

원은 **속을 비운 테두리**로 그립니다. 채우면 세 색이 진흙이 되고,
비우면 겹친 자리만 계산해서 밝힐 수 있습니다.

python poster_venn.py  →  out/poster/venn_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.014, 0.018, 0.030])
AQUA  = np.float32([0.20, 0.92, 1.00])            # 물
ROSE  = np.float32([1.00, 0.24, 0.60])            # 혼자
LIME  = np.float32([0.72, 1.00, 0.24])            # 일렉
PAPER = np.float32([0.98, 0.99, 1.00])
DIM   = np.float32([0.58, 0.66, 0.74])


def band(H, W, cx, cy, R, t):
    """속 빈 원의 마스크. 채운 원이 아니라 **테두리**여야 겹침을 셀 수 있다."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    return np.clip(1 - np.abs(d - R) / t, 0, 1) ** 0.7


def disc(H, W, cx, cy, R):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    return (np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) < R).astype(np.float32)


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK

    CX = W / 2
    CY = H * (0.435 if story else 0.430)
    R = W * 0.235
    d = R * 0.60                                   # 원 사이 거리
    t = R * 0.085                                  # 테두리 두께

    # 위 하나, 아래 둘 — 삼중 벤의 표준 배치
    P = [(CX, CY - d * 0.72, AQUA, 'POOL'),
         (CX - d * 0.86, CY + d * 0.52, ROSE, 'SOLO'),
         (CX + d * 0.86, CY + d * 0.52, LIME, 'ELECTRONIC')]

    rings = []
    for cx, cy, col, _ in P:
        m = band(H, W, cx, cy, R, t)
        rings.append(m)
        img += cv2.GaussianBlur(m, (0, 0), t * 1.9)[..., None] * col * 0.55
        img[:] = img * (1 - m[..., None] * 0.92) + col * m[..., None] * 0.92

    # **셋이 다 겹치는 자리.** 여기만 흰빛이다
    core = disc(H, W, P[0][0], P[0][1], R)
    for cx, cy, _, _ in P[1:]:
        core = np.minimum(core, disc(H, W, cx, cy, R))
    img += cv2.GaussianBlur(core, (0, 0), R * 0.22)[..., None] * PAPER * 0.55
    img += cv2.GaussianBlur(core, (0, 0), R * 0.55)[..., None] * np.float32([0.7, 0.9, 1.0]) * 0.35

    # 원마다 낱말 하나 — 원 안 바깥쪽에. 가운데는 이름 자리다
    # 라벨을 고리 안쪽에 두니 선 위에 얹혔다. **바깥으로 빼야 고리도 글자도 산다**
    for (cx, cy, col, txt), dyk in zip(P, (-1.22, 1.16, 1.16)):
        sz = int((30 if len(txt) < 8 else 22) * V)
        paint(img, tmask(txt, BRAND, sz, 0.26), cx, cy + R * dyk, color=col, anchor='c')

    # ── 가운데 : 이름 ────────────────────────────────────
    M = int(W * 0.075)
    CWD = W - M * 2
    ns = justify(EV.NAME, R * 1.30, 0.06, cap=int(74 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.06), CX, CY - 14 * V, color=INK, anchor='c')
    paint(img, tmask(EV.DATE, KR, int(22 * V), 0.02), CX, CY + 28 * V, color=INK, anchor='c')

    # ── 머리 · 발 ────────────────────────────────────────
    ty = H * (0.070 if story else 0.062)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.85, anchor='c')
    ny = H * (0.775 if story else 0.760)
    big = justify(EV.NAME, CWD, 0.10, cap=int(120 * V))
    paint(img, tmask(EV.NAME, BRAND, big, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.34), W / 2, ny + big * 0.82,
          color=AQUA, anchor='c')

    ly = ny + big * 0.82 + 52 * V
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.92, anchor='c')

    fy = H * (0.888 if story else 0.878)
    rule(img, fy, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    paint(img, tmask(f'{EV.DATE}   ·   {EV.TIME}', KR, int(24 * V), 0.02), W / 2, fy + 38 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}   {EV.ADDR}', KR, int(16 * V), 0.02), W / 2, fy + 70 * V,
          color=DIM, a=0.90, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, fy + 100 * V,
          color=DIM, a=0.55, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * 0.976,
          color=LIME, a=0.85, anchor='c')

    vignette(img, 0.42, 2.0)
    grain(img, 0.007, 34)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'venn_{k}')
        save(im, f'venn_{k}')
