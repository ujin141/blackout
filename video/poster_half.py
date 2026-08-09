"""
AB안 — **위는 물, 아래는 클럽.** 사진 두 장으로 행사 형식을 그대로 보여 줍니다.

풀파티 × 솔로파티라고 글로 쓰기 전에, **물과 클럽이 한 장에 있으면** 그게 설명입니다.
도형으로 겹치는 대신 사진을 위아래로 놓습니다 — 해석할 게 없습니다.

경계는 기울이지 않습니다(A안이 7도로 기울였습니다). 여기는 **수평**입니다 —
기울이면 디자인이 되고, 수평이면 사실이 됩니다.

경계 띠에 날짜와 시간을 넣습니다. 두 사진 사이가 판에서 눈이 제일 오래 머무는
자리라, 제일 중요한 정보가 거기 있어야 합니다.

클럽 사진은 아래쪽에 얼굴이 다 나와서 **위 34%만** 씁니다(`CLUB_SAFE`).

python poster_half.py  →  out/poster/half_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, POOL, CLUB, CLUB_SAFE, SIZES, tmask, tmask_bl,
                        paint, paint_bl, rule, box, duotone, grain, save)
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

W_DEEP = np.float32([0.018, 0.042, 0.070])
W_LIT  = np.float32([0.32, 0.50, 0.62])
C_DEEP = np.float32([0.055, 0.020, 0.045])
C_LIT  = np.float32([0.66, 0.26, 0.46])
PAPER  = np.float32([0.98, 0.99, 1.00])
AQUA   = np.float32([0.30, 0.92, 1.00])
ROSE   = np.float32([1.00, 0.45, 0.72])
DIM    = np.float32([0.64, 0.72, 0.80])


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32)

    SEAM = int(H * (0.470 if story else 0.460))
    BAND = int(H * (0.088 if story else 0.092))     # 경계 띠

    top = duotone(POOL, W, SEAM, W_DEEP, W_LIT, contrast=1.18, keep=0.14,
                  focus=0.62, zoom=1.25)
    bot = duotone(CLUB, W, H - SEAM - BAND, C_DEEP, C_LIT, contrast=1.22, keep=0.12,
                  **CLUB_SAFE)
    img[:SEAM] = top
    img[SEAM + BAND:] = bot

    # 위쪽은 위를, 아래쪽은 아래를 눌러 글자 자리를 만든다
    ys = np.arange(SEAM, dtype=np.float32)[:, None, None] / SEAM
    img[:SEAM] *= (1 - 0.76 * np.clip((0.52 - ys) / 0.52, 0, 1) ** 1.0)
    hb = H - SEAM - BAND
    yb = np.arange(hb, dtype=np.float32)[:, None, None] / hb
    img[SEAM + BAND:] *= (1 - 0.90 * np.clip((yb - 0.26) / 0.42, 0, 1) ** 1.0)

    M = int(W * 0.085)
    CWD = W - M * 2

    # ── 위 : 이름 ────────────────────────────────────────
    ty = H * (0.062 if story else 0.056)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.90)
    ny = H * (0.150 if story else 0.140)
    ns = justify(EV.NAME, CWD, 0.08, cap=int(136 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), M, ny, color=PAPER)
    paint(img, tmask('POOL PARTY', BRAND, int(26 * V), 0.30), M, ny + ns * 0.80,
          color=AQUA)

    # ── 경계 띠 : 날짜·시간. **판에서 제일 중요한 정보** ──
    box(img, 0, SEAM, W, SEAM + BAND, np.float32([0.045, 0.048, 0.058]), 1.0)
    rule(img, SEAM, 0, W, AQUA, 0.85, max(2, int(3 * V)))
    rule(img, SEAM + BAND - max(2, int(3 * V)), 0, W, ROSE, 0.85, max(2, int(3 * V)))
    cy = SEAM + BAND * 0.5
    paint_bl(img, tmask_bl(EV.DATE, KR, int(34 * V), 0.02), M, cy + 12 * V, color=PAPER)
    paint_bl(img, tmask_bl(EV.TIME, KR, int(24 * V), 0.02), W - M, cy + 12 * V,
             color=AQUA, anchor='r')

    # ── 아래 : 클럽 · 라인업 · 장소 ──────────────────────
    by = SEAM + BAND + 54 * V
    paint(img, tmask('SOLO PARTY  ·  ELECTRONIC', BRAND, int(26 * V), 0.30), M, by,
          color=ROSE)
    ly = by + 62 * V
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD, 0.12)), 0.12),
          M, ly, color=PAPER, a=0.98)

    fy = H * (0.822 if story else 0.808)
    rule(img, fy - 34 * V, M, W - M, PAPER, 0.22, max(1, int(2 * V)))
    paint_bl(img, tmask_bl(EV.VENUE, KR, int(26 * V), 0.01), M, fy, color=PAPER)
    paint_bl(img, tmask_bl(EV.ADDR, KR, int(17 * V), 0.01), M, fy + 34 * V,
             color=DIM, a=0.95)
    paint_bl(img, tmask_bl(EV.ENTRY, KR, int(18 * V), 0.01), M, fy + 66 * V,
             color=AQUA, a=0.95)
    # 핸들은 자기 줄에. 오른쪽 정렬로 다른 줄과 같은 y 에 두면 부딪힌다
    paint(img, tmask(EV.HANDLE, BRAND, int(18 * V), 0.24), M, fy + 98 * V,
          color=ROSE, a=0.98)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, fy + 130 * V,
          color=DIM, a=0.65)

    vignette(img, 0.30, 2.3)
    grain(img, 0.007, 46)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'half_{k}')
        save(im, f'half_{k}')
