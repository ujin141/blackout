"""
L안 — **두 물결이 만난다.** 이 행사의 조합을 한 장치로 말하는 판입니다.

수면을 위에서 내려다봅니다. 물에 닿은 자리가 **두 곳**이고, 거기서 퍼진 동심원이
가운데에서 겹칩니다. 원은 물결이라 풀파티이고, 두 개라서 솔로파티입니다 —
혼자 온 사람 둘이 만나는 지점이 화면 한가운데입니다.

**겹치는 자리에 이름을 놓습니다.** 원 두 개를 그려 놓고 이름을 다른 데 두면
그냥 무늬가 됩니다. 교차점에 놓아야 "여기서 만난다"가 그림의 뜻이 됩니다.

원이 화면 밖으로 다 나가면 하나의 무늬로 보여 두 개인 게 안 읽힙니다 —
**두 중심이 화면 안에 보여야** 합니다.

python poster_ripple.py  →  out/poster/ripple_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save, info_block
from fest_kit import ripple, specks, vignette, justify, night
from scene_kit import photoscene
from fonts import KR
import event as EV

DEEP    = (0.012, 0.030, 0.056)
SHALLOW = (0.030, 0.075, 0.110)
CYAN    = np.float32([0.42, 0.95, 1.00])
WARM    = np.float32([1.00, 0.62, 0.34])
PAPER   = np.float32([0.97, 0.99, 1.00])
DIM     = np.float32([0.60, 0.74, 0.82])


def build(W, H, story=False):
    V = W / 1080.0
    # **배경은 무늬가 아니라 장면이다.** 물결·타일만 깔면 여전히 상징이라
    # "추상적"이라는 지적이 남는다. 밤 루프탑 수영장에 사람이 있고 디제이가
    # 틀고 있는 그림을 뒤에 두면, 앞의 도형이 무슨 얘기를 하든 일단
    # 무슨 행사인지가 먼저 보인다. 뒤로 물러나야 하니 한 단 눌러 둔다.
    # **그린 장면은 자연스럽지 않다.** 선으로 그린 실루엣은 도표로 읽히고
    # 그 위에 네온을 얹으면 둘이 따로 논다. 자연스러움은 **사진의 결**에서
    # 온다 — 헤이즈의 얼룩, 물결의 불규칙은 코드로 흉내 낼수록 가짜 티가 난다.
    img = photoscene(W, H, story, wy=0.52 if story else 0.495) * 0.92

    # 두 중심. 화면 안에 보여야 "둘"로 읽힌다
    CYm = H * (0.470 if story else 0.480)
    dx = W * 0.215
    A = (W / 2 - dx, CYm - H * 0.035)
    B = (W / 2 + dx, CYm + H * 0.035)

    # 원을 11 개씩 옅게 깔았더니 물결이 아니라 배경 무늬가 됐다.
    # **적게, 세게.** 셀 수 있어야 두 중심에서 퍼진 것으로 읽힌다.
    ripple(img, A[0], A[1], W * 0.075, W * 0.62, 6, CYAN, 1.00, th=3.4 * V)
    ripple(img, B[0], B[1], W * 0.075, W * 0.62, 6, WARM, 0.85, th=3.4 * V)
    # 닿은 자리 — 점 하나. 여기서 시작했다는 표시
    for (cx, cy), col in ((A, CYAN), (B, WARM)):
        cv2.circle(img, (int(cx), int(cy)), max(2, int(7 * V)),
                   tuple(float(v) for v in col), -1, cv2.LINE_AA)
        d0 = np.sqrt((np.mgrid[0:H, 0:W][1].astype(np.float32) - cx) ** 2 +
                     (np.mgrid[0:H, 0:W][0].astype(np.float32) - cy) ** 2)
        img += cv2.GaussianBlur((d0 < 11 * V).astype(np.float32),
                                (0, 0), 34 * V)[..., None] * col * 1.6

    specks(img, 90, H * 0.08, H * 0.92, PAPER, 0.16, seed=21, rmax=1.8)

    # **겹치는 자리를 눌러 글자 자리를 만든다.** 그림자가 아니라 배경을 죽인다
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    band = np.exp(-((yy - CYm) / (H * 0.085)) ** 2)
    img *= (1 - 0.55 * band)[..., None]

    M = int(W * 0.085)
    CWD = W - M * 2
    ns = justify(EV.NAME, CWD, 0.10, cap=int(140 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, CYm - 18 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, CYm + 44 * V,
          color=CYAN, anchor='c')

    # 머리 — 두 중심 위로 각각 한 낱말. 어느 원이 무엇인지 이름을 붙인다
    ty = H * (0.150 if story else 0.145)
    paint(img, tmask('POOL', BRAND, int(44 * V), 0.22), A[0], ty, color=CYAN, a=0.9, anchor='c')
    paint(img, tmask('SOLO', BRAND, int(44 * V), 0.22), B[0], ty, color=WARM, a=0.9, anchor='c')
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), W / 2,
          ty - 52 * V, color=DIM, a=0.75, anchor='c')

    # 라인업 — 아래쪽. 물결이 잦아든 자리
    # 라인업도 발치에서 역산한다
    # 정보가 네 줄에서 **다섯 줄**로 늘었다(입장 조건 추가). 한 줄(46V)만큼
    # 발치를 더 올려야 캔버스를 안 넘는다.
    fy = H - 404 * V
    ly = fy - 110 * V
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.92, anchor='c')
    prog = '  ·  '.join(sorted(EV.PROGRAM))
    paint(img, tmask(prog, BRAND, int(20 * V), 0.30), W / 2, ly + 46 * V,
          color=WARM, a=0.90, anchor='c')

    # **바쁜 배경에서는 발치를 눌러야 글자가 산다.** 그림자를 덧대면 지저분해지고,
    # 배경을 죽이면 깨끗하다 — 이 판 전체에서 지켜 온 규칙과 같다.
    _fy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.68 * np.clip((_fy - (fy - 30 * V)) / (60 * V), 0, 1))
    rule(img, fy, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    # 정보는 **event.INFO 형식 그대로**. 순서·표기를 판마다 바꾸지 않는다
    yb = info_block(img, M, fy + 44 * V, CWD, V, CYAN, PAPER, head_color=PAPER)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, yb + 34 * V,
          color=DIM, a=0.60)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 70 * V,
          color=CYAN, a=0.90)


    vignette(img, 0.44, 1.9)
    grain(img, 0.007, 14)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'ripple_{k}')
        save(im, f'ripple_{k}')
