"""
W안 — **세 빛이 하나로.** 프리즘을 거꾸로 쓴 판입니다.

프리즘은 흰빛을 여러 색으로 가릅니다. 이 판은 반대로 갑니다 —
세 색의 빛이 각각 들어와 한 점에서 만나고, 거기서 **흰빛 하나**가 나갑니다.
물 · 혼자 · 일렉이 하나의 밤이 되는 걸 광학으로 말합니다.

**모이는 점이 판에서 제일 밝아야** 합니다. 빛은 겹칠수록 밝아지고,
그 규칙을 어기면 광선 세 개를 그린 그림일 뿐입니다.

빔은 선이 아니라 원뿔입니다 — 멀수록 넓고 옅게. 그리고 **연기가 있어야 빔이 보입니다.**

python poster_prism.py  →  out/poster/prism_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import haze, specks, vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.012, 0.014, 0.026])
AQUA  = np.float32([0.22, 0.90, 1.00])
ROSE  = np.float32([1.00, 0.26, 0.62])
LIME  = np.float32([0.74, 1.00, 0.26])
PAPER = np.float32([0.98, 0.99, 1.00])
DIM   = np.float32([0.58, 0.64, 0.72])


def ray(H, W, x0, y0, x1, y1, w0, w1):
    """한 점에서 다른 점으로 가는 원뿔. 시작이 좁고 끝이 넓다."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = x1 - x0, y1 - y0
    L = float(np.hypot(dx, dy))
    ux, uy = dx / L, dy / L
    px, py = xx - x0, yy - y0
    along = px * ux + py * uy
    perp = np.abs(-px * uy + py * ux)
    wid = w0 + (w1 - w0) * np.clip(along / L, 0, 1)
    m = np.clip(1 - perp / np.maximum(wid, 1e-3), 0, 1) ** 1.5
    return m * np.clip(along / (L * 0.06), 0, 1) * np.clip(1 - along / (L * 1.02), 0, 1) ** 0.7


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK

    CX = W / 2
    CY = H * (0.470 if story else 0.462)

    haze(img, H * 0.10, H * 0.86, np.float32([0.25, 0.28, 0.45]), 0.22, seed=6)

    # 세 방향에서 들어온다 — 왼쪽 위 · 오른쪽 위 · 아래
    SRC = [(-W * 0.12, H * 0.055, AQUA, 'POOL'),
           (W * 1.12, H * 0.055, ROSE, 'SOLO'),
           (CX, H * 1.16, LIME, 'ELECTRONIC')]
    acc = np.zeros((H, W), np.float32)
    for x0, y0, col, _ in SRC:
        m = ray(H, W, x0, y0, CX, CY, W * 0.055, W * 0.010)
        acc += m
        img += cv2.GaussianBlur(m, (0, 0), W * 0.010)[..., None] * col * 0.85
        img += cv2.GaussianBlur(m, (0, 0), W * 0.050)[..., None] * col * 0.30

    # **모이는 점 — 판에서 제일 밝다**
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    core = np.exp(-(((xx - CX) / (W * 0.030)) ** 2 + ((yy - CY) / (W * 0.030)) ** 2))
    img += core[..., None] * PAPER * 1.7
    img += cv2.GaussianBlur(core, (0, 0), W * 0.075)[..., None] * PAPER * 0.85

    # 나가는 흰빛 — 위로 곧게. 셋이 하나가 된 결과
    out = ray(H, W, CX, CY, CX, -H * 0.10, W * 0.012, W * 0.085)
    img += cv2.GaussianBlur(out, (0, 0), W * 0.014)[..., None] * PAPER * 0.55
    specks(img, 130, H * 0.06, H * 0.90, PAPER, 0.16, seed=61, rmax=1.8)

    # 빔마다 이름표 — 어느 빛이 무엇인지
    for (x0, y0, col, txt), (lx, ly) in zip(SRC, ((0.175, 0.215), (0.825, 0.215), (0.5, 0.715))):
        paint(img, tmask(txt, BRAND, int((26 if len(txt) < 8 else 20) * V), 0.26),
              W * lx, H * ly, color=col, anchor='c')

    # ── 글자 ─────────────────────────────────────────────
    M = int(W * 0.075)
    CWD = W - M * 2
    ty = H * (0.062 if story else 0.055)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.85, anchor='c')

    ny = H * (0.128 if story else 0.120)
    img *= (1 - 0.55 * np.exp(-((yy - ny) / (H * 0.070)) ** 2))[..., None]
    ns = justify(EV.NAME, CWD, 0.10, cap=int(140 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.34), W / 2, ny + ns * 0.82,
          color=AQUA, anchor='c')

    ly2 = H * (0.855 if story else 0.842)
    img *= (1 - 0.60 * np.exp(-((yy - (ly2 + 52 * V)) / (H * 0.072)) ** 2))[..., None]
    rule(img, ly2, M, W - M, PAPER, 0.20, max(1, int(2 * V)))
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly2 + 40 * V, color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(f'{EV.DATE}   ·   {EV.TIME}', KR, int(23 * V), 0.02),
          W / 2, ly2 + 80 * V, color=PAPER, a=0.95, anchor='c')
    paint(img, tmask(f'{EV.VENUE}   {EV.ADDR}', KR, int(16 * V), 0.02),
          W / 2, ly2 + 112 * V, color=DIM, a=0.90, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, ly2 + 142 * V,
          color=DIM, a=0.65, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, ly2 + 172 * V,
          color=ROSE, a=0.90, anchor='c')

    vignette(img, 0.44, 1.9)
    grain(img, 0.007, 36)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'prism_{k}')
        save(im, f'prism_{k}')
