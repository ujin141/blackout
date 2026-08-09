"""
N안 — **혼자 왔는데 물에 비친 건 둘.** 다섯 중 이야기가 제일 분명한 판입니다.

수면 위에는 사람이 **하나** 서 있고, 물에 비친 상은 **둘**입니다.
솔로파티가 무엇인지 한 줄도 안 쓰고 말합니다. 그리고 그 장치가 물이라
풀파티라는 것도 같은 그림에서 나옵니다.

**반영은 흔들려야 합니다.** 안 흔들면 거울이지 물이 아니고, 물이 아니면
"비친 상이 하나 더 있다"가 착시가 아니라 오류로 보입니다.

과거에 이 컨셉을 "혼자 와도 됩니다"라는 문장으로 쓴 적이 있고 반려됐습니다
(`poster_solo.py`). **문장으로 설명하면 안 되고 그림이 말해야 합니다.**

python poster_mirror.py  →  out/poster/mirror_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import sky, reflect, specks, vignette, justify, night
from fonts import KR
import event as EV

TOP    = (0.014, 0.018, 0.034)
LOW    = (0.240, 0.130, 0.095)   # 수평선 바로 위의 잔광
WATER  = (0.014, 0.036, 0.052)
AMBER  = np.float32([1.00, 0.68, 0.30])
PAPER  = np.float32([0.97, 0.96, 0.94])
DIM    = np.float32([0.66, 0.66, 0.70])


def figure(img, cx, base_y, h, color, a=1.0, lean=0.0):
    """서 있는 사람 하나. 머리·몸통·다리만 — 자세히 그리면 사람이 아니라 삽화가 된다."""
    hh = h * 0.16                                   # 머리 지름
    cv2.circle(img, (int(cx + lean * h * 0.10), int(base_y - h * 0.92)), int(hh * 0.5),
               tuple(float(v) for v in color), -1, cv2.LINE_AA)
    pts = np.array([
        [cx - h * 0.105 + lean * h * 0.06, base_y - h * 0.80],
        [cx + h * 0.105 + lean * h * 0.06, base_y - h * 0.80],
        [cx + h * 0.085, base_y - h * 0.36],
        [cx + h * 0.070, base_y],
        [cx + h * 0.012, base_y],
        [cx + h * 0.020, base_y - h * 0.36],
        [cx - h * 0.020, base_y - h * 0.36],
        [cx - h * 0.012, base_y],
        [cx - h * 0.070, base_y],
        [cx - h * 0.085, base_y - h * 0.36]], np.int32)
    cv2.fillPoly(img, [pts], tuple(float(v) for v in color), cv2.LINE_AA)


def build(W, H, story=False):
    V = W / 1080.0
    img = sky(W, H, [(0.0, TOP), (0.34, TOP), (0.55, LOW), (1.0, (0.12, 0.07, 0.06))])

    HZ = H * (0.545 if story else 0.550)            # 수면
    # 물은 하늘보다 차다. 경계가 색으로 갈려야 수면으로 읽힌다
    img[int(HZ):] = np.float32(WATER)
    img[int(HZ):] += (np.linspace(1, 0, H - int(HZ), dtype=np.float32)[:, None, None] ** 2
                      * np.float32([0.22, 0.11, 0.08]))   # 수면에 남는 잔광

    # **실루엣은 뒤가 밝아야 보인다.** 처음엔 검정 하늘에 검정 사람이라
    # 아무것도 안 보였다. 수평선 바로 위에 잔광 띠를 깔고 그 앞에 세운다.
    yy0 = np.arange(H, dtype=np.float32)
    glowband = np.exp(-((yy0 - (HZ - H * 0.055)) / (H * 0.115)) ** 2)
    img += glowband[:, None, None] * np.float32([0.42, 0.20, 0.13]) * 0.85

    # 물 위 — 사람 하나
    fh = H * (0.230 if story else 0.235)
    figure(img, W * 0.50, HZ, fh, np.float32([0.006, 0.006, 0.010]))
    # 옆에 옅은 빛. 사람이 배경에서 떨어져 나온다
    glow = np.exp(-((np.mgrid[0:H, 0:W][1].astype(np.float32) - W * 0.50) / (W * 0.20)) ** 2)
    glow *= np.exp(-((np.mgrid[0:H, 0:W][0].astype(np.float32) - (HZ - fh * 0.5)) / (H * 0.14)) ** 2)
    img += glow[..., None] * AMBER * 0.10

    # 물 아래 — **둘.** 하나는 원래 자리, 하나는 옆에서 다가온다
    below = np.zeros_like(img)
    figure(below, W * 0.50, HZ, fh, np.float32([1, 1, 1]))
    figure(below, W * 0.635, HZ, fh * 0.96, np.float32([1, 1, 1]), lean=-0.35)
    mask = below[..., 0]
    # 뒤집어 아래로 내리고 흔든다
    depth = int(min(fh * 1.25, H - HZ))
    src = mask[int(HZ) - depth:int(HZ)][::-1]
    rows = np.arange(depth, dtype=np.float32)
    dxs = np.sin(rows * 0.12 + 0.6) * (5.0 * V) * (0.35 + rows / depth)
    gx, gy = np.meshgrid(np.arange(W, dtype=np.float32), rows)
    src = cv2.remap(src, (gx + dxs[:, None]).astype(np.float32), gy.astype(np.float32),
                    cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    src = cv2.GaussianBlur(src, (0, 0), 2.2)
    k = (src * (0.60 * (1 - rows / depth) ** 0.9)[:, None])[..., None]
    img[int(HZ):int(HZ) + depth] = (img[int(HZ):int(HZ) + depth] * (1 - k)
                                    + np.float32([0.020, 0.016, 0.020]) * k)

    # 수면의 잔물결 — 촘촘해야 물이다
    for i in range(int(H * 0.006), H - int(HZ), max(3, int(H * 0.010))):
        rule(img, HZ + i, 0, W, np.float32([0.45, 0.75, 0.85]),
             0.055 * (1 - i / (H - HZ)) + 0.02, max(1, int(2 * V)))
    rule(img, HZ, 0, W, AMBER, 0.30, max(1, int(2 * V)))
    specks(img, 70, H * 0.06, HZ, PAPER, 0.14, seed=41, rmax=1.7)

    # ── 글자 ─────────────────────────────────────────────
    M = int(W * 0.085)
    CWD = W - M * 2
    ty = H * (0.075 if story else 0.068)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2, ty,
          color=DIM, a=0.80, anchor='c')

    ny = H * (0.160 if story else 0.150)
    ns = justify(EV.NAME, CWD, 0.10, cap=int(140 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + ns * 0.82,
          color=AMBER, anchor='c')

    ly = H * (0.290 if story else 0.278)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.92, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.88, anchor='c')

    fy = H * (0.845 if story else 0.838)
    rule(img, fy, M, W - M, PAPER, 0.16, max(1, int(2 * V)))
    paint(img, tmask(EV.DATE, KR, int(32 * V), 0.02), W / 2, fy + 44 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(20 * V), 0.02),
          W / 2, fy + 84 * V, color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02), W / 2, fy + 114 * V,
          color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, H * 0.948,
          color=DIM, a=0.55, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, H * 0.974,
          color=AMBER, a=0.85, anchor='c')

    vignette(img, 0.42, 2.0)
    grain(img, 0.007, 18)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'mirror_{k}')
        save(im, f'mirror_{k}')
