"""
H안 — **지는 해.** 행사 이름이 AFTER SUNSET 이라 이름을 그대로 그린 판입니다.

큰 원판 하나를 지평선에 반쯤 걸치고, 가로 띠로 가릅니다.
**레트로 선셋의 정체는 원이 아니라 띠입니다** — 원만 두면 그냥 동그라미이고,
아래로 갈수록 촘촘해지는 띠가 들어가야 "해가 지고 있다"로 읽힙니다.

지평선은 산이 아니라 **건물**입니다. 루프탑 파티라서요.

밤 행사라 해는 이미 거의 다 졌습니다 — 원판은 화면 아래쪽에 3분의 1만 남기고,
하늘은 남색에서 검정으로 갑니다. **화면에서 밝은 건 해 하나뿐**이고,
밝은 게 하나면 거기로만 시선이 갑니다.

python poster_sun.py  →  out/poster/sun_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import sky, slit, skyline, specks, vignette, justify, night
from fonts import KR
import event as EV

NIGHT  = (0.020, 0.022, 0.040)                   # 하늘 꼭대기
MID    = (0.075, 0.045, 0.105)                   # 보랏빛으로 넘어가는 중간
LOW    = (0.230, 0.085, 0.090)                   # 지평선 근처의 붉은 잔광
# 해의 위쪽 밝기가 밤 톤을 정한다. 0.92 면 밝은 픽셀이 12% 라 낮 행사로 보인다 —
# 0.88 로 내리면 휘도가 0.6 아래로 떨어지면서도 해로는 그대로 읽힌다.
SUN_HI = np.float32([0.88, 0.50, 0.14])
SUN_LO = np.float32([0.86, 0.20, 0.26])
PAPER  = np.float32([0.97, 0.96, 0.94])
DIM    = np.float32([0.72, 0.66, 0.66])


def build(W, H, story=False):
    V = W / 1080.0
    img = sky(W, H, [(0.00, NIGHT), (0.42, NIGHT), (0.66, MID), (0.88, LOW), (1.0, (0.05, 0.02, 0.03))])

    HZ = H * (0.700 if story else 0.685)          # 지평선
    R = W * (0.360 if story else 0.330)
    CX, CY = W / 2, HZ - R * 0.30                 # 해가 3분의 1만 남았다

    # 해 — 위는 주황, 아래는 붉게. 한 색이면 원판이지 해가 아니다
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    grad = np.clip((yy - (CY - R)) / (2 * R), 0, 1)[..., None]
    body = SUN_HI * (1 - grad) + SUN_LO * grad
    d = np.sqrt((np.mgrid[0:H, 0:W][1].astype(np.float32) - CX) ** 2 + (yy - CY) ** 2)
    m = np.clip((R - d) / 2.5, 0, 1)[..., None]
    m = m * (yy < HZ)[..., None]                  # 지평선 아래로는 안 내려간다
    img[:] = img * (1 - m) + body * m

    # 해를 가르는 띠. 아래로 갈수록 굵고 위로 갈수록 촘촘하다
    # 띠는 **해의 위쪽까지 올라가야** 한다. 아래쪽만 가르면 건물 창문처럼 보였다.
    # 굵기를 절반으로 줄이고 개수를 늘리면 창이 아니라 해가 지는 것으로 읽힌다.
    #
    # 다만 **글자가 앉을 자리는 비운다.** 띠 위에 글자를 얹으면 획이 잘려
    # 시간 줄이 통째로 안 읽혔다. 비워 둔 띠 한 칸이 저절로 날짜 배너가 된다.
    BY0 = CY - R * 0.46                            # 글자 띠 위
    BY1 = CY - R * 0.10                            # 글자 띠 아래
    slit(img, CY - R * 0.62, BY0, gap=W * 0.017, thick=int(W * 0.009),
         color=(0.030, 0.020, 0.035), a=0.96)
    slit(img, BY1, HZ, gap=W * 0.017, thick=int(W * 0.009),
         color=(0.030, 0.020, 0.035), a=0.96)

    # 해 주변의 대기광. 번짐이 있어야 뒤에서 빛나는 것으로 보인다
    halo = cv2.GaussianBlur(np.clip(m[..., 0], 0, 1), (0, 0), W * 0.085)
    img += halo[..., None] * np.float32([0.55, 0.22, 0.14]) * 0.55

    # 지평선 — 도시. 옥상에서 보는 그림이라 산이 아니다
    # 스카이라인은 **낮아야 지평선이지** 높으면 벽이다. 0.085 는 담장처럼 보였다.
    skyline(img, HZ, H * 0.052, (0.012, 0.012, 0.020), seed=5, a=1.0)
    rule(img, HZ, 0, W, np.float32([0.95, 0.45, 0.30]), 0.35, max(1, int(2 * V)))

    # 지평선 아래 — 물. 루프탑 풀파티라 해가 물에 한 번 더 비친다
    ref = img[int(HZ) - int(H * 0.16):int(HZ)][::-1]
    hh = min(ref.shape[0], H - int(HZ))
    band = np.clip(1 - np.arange(hh, dtype=np.float32) / hh, 0, 1)[:, None, None]
    img[int(HZ):int(HZ) + hh] = (img[int(HZ):int(HZ) + hh] * (1 - band * 0.42)
                                 + ref[:hh] * band * 0.30)
    for i in range(int(H * 0.012), hh, max(3, int(H * 0.008))):   # 물결 — 촘촘해야 물이다
        rule(img, HZ + i, 0, W, np.float32([0.9, 0.6, 0.5]),
             0.05 + 0.05 * (1 - i / hh), max(1, int(2 * V)))

    specks(img, 120, H * 0.10, HZ, np.float32([1.0, 0.85, 0.7]), 0.30, seed=12, rmax=2.2)

    # ── 글자 ─────────────────────────────────────────────
    M = int(W * 0.085)
    CWD = W - M * 2
    ny = H * (0.245 if story else 0.230)
    ns = justify(EV.NAME, CWD, 0.10, cap=int(148 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + ns * 0.80,
          color=np.float32([1.0, 0.74, 0.35]), anchor='c')

    ly = H * (0.360 if story else 0.345)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.92, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.92, anchor='c')

    # 날짜는 해 위 **비워 둔 띠 자리**에 얹는다 — 밝은 판 위의 검정이라 제일 먼저 걸린다
    dy = (BY0 + BY1) * 0.5
    paint(img, tmask(EV.DATE, KR, int(44 * V), 0.02), W / 2, dy - 22 * V,
          color=np.float32([0.06, 0.02, 0.03]), anchor='c')
    paint(img, tmask(EV.TIME, KR, int(23 * V), 0.02), W / 2, dy + 26 * V,
          color=np.float32([0.10, 0.03, 0.04]), a=0.92, anchor='c')

    fy = H * (0.885 if story else 0.878)
    paint(img, tmask(EV.VENUE, KR, int(26 * V), 0.02), W / 2, fy, color=PAPER, a=0.95, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(17 * V), 0.02), W / 2, fy + 34 * V,
          color=DIM, a=0.80, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, fy + 74 * V,
          color=DIM, a=0.55, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), W / 2, H * 0.960,
          color=np.float32([1.0, 0.70, 0.40]), a=0.85, anchor='c')

    vignette(img, 0.42, 2.0)
    grain(img, 0.007, 6)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'sun_{k}')
        save(im, f'sun_{k}')
