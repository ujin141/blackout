"""
T안 — **물튀김.** 셔터가 1/2000 로 끊은 그 순간입니다.

풀파티에서 제일 자극적인 그림은 물이 조용히 있는 게 아니라 **터지는** 장면입니다.
가운데에서 왕관 모양으로 솟은 물기둥, 사방으로 날아간 물방울,
뒤에서 때린 플래시. 전부 그립니다 — 사진은 안 씁니다.

**물방울은 정지해야 자극적입니다.** 흐리면 분위기가 되고, 딱 멈춰야 순간이 됩니다.
그래서 방울마다 **한쪽에만 밝은 점**을 찍습니다 — 역광에서 물이 그렇게 보입니다.

터진 자리에서 판 전체로 빛이 뻗습니다. 빛줄기는 방울 뒤에서 나와야 하고,
방울 위에 그으면 물이 아니라 스티커가 됩니다.

python poster_splash.py  →  out/poster/splash_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.010, 0.020, 0.034])
ELEC  = np.float32([0.35, 0.95, 1.00])            # 전기 시안
WHITE = np.float32([1.00, 1.00, 1.00])
HOT   = np.float32([1.00, 0.45, 0.55])
PAPER = np.float32([0.97, 0.99, 1.00])
DIM   = np.float32([0.58, 0.72, 0.80])


def crown(layer, cx, cy, r, n, seed=2):
    """물기둥의 왕관. **끝이 방울로 끊겨야** 물이지, 이어지면 그냥 뿔이다."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        a = -np.pi / 2 + (i / (n - 1) - 0.5) * np.pi * 1.35
        h = r * rng.uniform(0.28, 0.62)   # 길면 물기둥이 아니라 불꽃이다
        x1, y1 = cx + np.cos(a) * h * 0.72, cy + np.sin(a) * h
        w = max(3, int(r * rng.uniform(0.055, 0.115)))   # 굵어야 물이다
        cv2.line(layer, (int(cx), int(cy)), (int(x1), int(y1)), 1.0, w, cv2.LINE_AA)
        cv2.circle(layer, (int(x1), int(y1)), int(w * rng.uniform(0.9, 1.7)), 1.0, -1,
                   cv2.LINE_AA)
        # 끊긴 방울 하나 더 — 떨어져 나간 게 보여야 터진 것이다
        if rng.random() < 0.7:
            k = rng.uniform(1.18, 1.55)
            cv2.circle(layer, (int(cx + np.cos(a) * h * 0.72 * k), int(cy + np.sin(a) * h * k)),
                       int(w * rng.uniform(0.5, 1.1)), 1.0, -1, cv2.LINE_AA)


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    CX = W / 2
    CY = H * (0.470 if story else 0.465)
    R = W * 0.40

    # 뒤에서 때린 플래시 — 물이 역광이라야 방울이 빛난다
    back = np.exp(-(((xx - CX) / (W * 0.42)) ** 2 + ((yy - CY) / (H * 0.26)) ** 2))
    img += back[..., None] * ELEC * 0.20
    img += back[..., None] * WHITE * 0.04

    layer = np.zeros((H, W), np.float32)
    crown(layer, CX, CY, R, 15, seed=4)
    # 사방으로 날아간 방울
    rng = np.random.default_rng(7)
    for _ in range(150):
        a = rng.uniform(0, 2 * np.pi)
        d = R * rng.uniform(0.55, 1.70) * (0.45 if np.sin(a) > 0 else 1.0)
        x, y = CX + np.cos(a) * d, CY + np.sin(a) * d * 0.80
        rr = max(1, int(R * rng.uniform(0.006, 0.026)))
        cv2.circle(layer, (int(x), int(y)), rr, 1.0, -1, cv2.LINE_AA)
    # 수면 — 터진 자리 아래
    # 터진 자리의 물 테두리 — 이게 있어야 '수면에서 솟았다'가 된다
    for k, (rx, ry, th) in enumerate(((0.52, 0.13, 11), (0.78, 0.19, 6), (1.05, 0.25, 4))):
        cv2.ellipse(layer, (int(CX), int(CY + R * 0.22)), (int(R * rx), int(R * ry)),
                    0, 0, 360, 1.0 - k * 0.28, max(2, int(th * V)), cv2.LINE_AA)

    # 방울 뒤의 빛무리 → 방울 → 방울 위의 하이라이트. 순서가 전부다
    img += cv2.GaussianBlur(layer, (0, 0), 22 * V)[..., None] * ELEC * 0.70
    m = np.clip(layer, 0, 1)[..., None]
    img[:] = img * (1 - m * 0.88) + np.float32([0.60, 0.86, 0.96]) * m * 0.88
    # **한쪽에만 밝은 점.** 역광에서 물방울이 그렇게 보인다
    hi = np.clip(layer - np.roll(np.roll(layer, int(3 * V), 0), int(3 * V), 1), 0, 1)
    img += hi[..., None] * WHITE * 0.60

    # 튀는 방향으로 뻗은 빛줄기 — 방울 뒤에서만
    streak = cv2.GaussianBlur(layer, (0, 0), 3.0)
    for k in (1, 2, 3):
        img += np.roll(streak, -int(9 * V * k), axis=0)[..., None] * ELEC * (0.05 / k)

    # ── 글자 ─────────────────────────────────────────────
    M = int(W * 0.075)
    CWD = W - M * 2
    ty = H * (0.072 if story else 0.065)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=PAPER, a=0.85, anchor='c')

    ny = H * (0.170 if story else 0.160)
    img *= (1 - 0.58 * np.exp(-((yy - ny) / (H * 0.080)) ** 2))[..., None]
    ns = justify(EV.NAME, CWD, 0.10, cap=int(148 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + ns * 0.82,
          color=HOT, anchor='c')

    ly = H * (0.278 if story else 0.266)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.95, anchor='c')

    fy = H * (0.845 if story else 0.835)
    img *= (1 - 0.60 * np.exp(-((yy - (fy + 62 * V)) / (H * 0.075)) ** 2))[..., None]
    rule(img, fy, M, W - M, PAPER, 0.26, max(2, int(3 * V)))
    paint(img, tmask(EV.DATE, KR, int(34 * V), 0.02), W / 2, fy + 46 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(20 * V), 0.02),
          W / 2, fy + 86 * V, color=DIM, a=0.98, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02), W / 2, fy + 116 * V,
          color=DIM, a=0.75, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, H * 0.948,
          color=DIM, a=0.60, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * 0.974,
          color=ELEC, a=0.95, anchor='c')

    vignette(img, 0.48, 1.8)
    grain(img, 0.008, 30)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'splash_{k}')
        save(im, f'splash_{k}')
