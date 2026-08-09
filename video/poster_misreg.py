"""
X안 — **삼색 판 어긋남.** 인쇄 사고를 일부러 냅니다.

옛날 인쇄는 색마다 판을 따로 찍습니다. 판이 조금씩 어긋나면 글자가 세 겹으로
갈라져 보이는데, 그게 **세 가지가 겹쳐 있다**는 걸 재료 자체로 말합니다.
컨셉을 그림으로 그리는 게 아니라 **인쇄 방식으로** 말하는 판입니다.

세 판에 각각 다른 낱말을 얹습니다 — 시안판에 POOL, 마젠타판에 SOLO,
라임판에 ELECTRONIC. 어긋난 세 판이 겹치는 자리에서만 흰 글자가 나옵니다.

**어긋남은 W 의 1.5% 안쪽.** 넘기면 세 겹이 아니라 세 개의 다른 글자가 되고,
그러면 읽히지 않습니다.

python poster_misreg.py  →  out/poster/misreg_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.024, 0.024, 0.026])
CY_   = np.float32([0.10, 0.85, 0.95])
MG_   = np.float32([1.00, 0.16, 0.55])
LM_   = np.float32([0.70, 0.98, 0.20])
PAPER = np.float32([0.97, 0.97, 0.95])
DIM   = np.float32([0.56, 0.56, 0.56])

PLATES = [(CY_, 'POOL', (-1.0, -0.55)),
          (MG_, 'SOLO', (1.0, -0.15)),
          (LM_, 'ELECTRONIC', (-0.15, 1.0))]


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    M = int(W * 0.062)
    CWD = W - M * 2
    off = W * 0.013                                # 판 어긋남

    ty = H * (0.070 if story else 0.062)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=DIM, a=0.95)
    paint(img, tmask('3 PLATES  ·  1 NIGHT', BRAND, int(17 * V), 0.30), W - M, ty,
          color=DIM, a=0.95, anchor='r')

    # ── 세 판에 각각 다른 낱말 ───────────────────────────
    wy = H * (0.300 if story else 0.290)
    for i, (col, word, (dx, dy)) in enumerate(PLATES):
        sz = justify(word, CWD, 0.02, cap=int(190 * V))
        m = tmask(word, BRAND, sz, 0.02)
        y = wy + i * (H * (0.115 if story else 0.118))
        # 판마다 살짝 어긋나게. **어긋남이 곧 이 판의 내용이다**
        paint(img, m, W / 2 + dx * off, y + dy * off * 0.6, color=col, a=0.92, anchor='c')
        # 같은 자리에 흰 글자를 아주 옅게 — 세 판이 맞은 부분
        paint(img, m, W / 2, y, color=PAPER, a=0.34, anchor='c')

    # ── 이름 : 세 판을 겹쳐 찍는다 ───────────────────────
    ny = H * (0.640 if story else 0.625)
    ns = justify(EV.NAME, CWD, 0.08, cap=int(120 * V))
    nm = tmask(EV.NAME, BRAND, ns, 0.08)
    for col, _, (dx, dy) in PLATES:
        paint(img, nm, W / 2 + dx * off * 0.75, ny + dy * off * 0.45, color=col, a=0.80,
              anchor='c')
    paint(img, nm, W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.34), W / 2, ny + ns * 0.86,
          color=DIM, a=0.95, anchor='c')

    # ── 인쇄 표식. 이게 있어야 '판'으로 읽힌다 ────────────
    for sx in (M * 0.55, W - M * 0.55):
        for sy in (H * 0.032, H * 0.968):
            for col, r in ((CY_, 15), (MG_, 11), (LM_, 7)):
                cv2.circle(img, (int(sx), int(sy)), int(r * V),
                           tuple(float(v) for v in col), max(1, int(2 * V)), cv2.LINE_AA)
    # 색 띠 — 인쇄 교정용 컬러바
    bw = CWD / 12
    by = H * (0.735 if story else 0.722)
    for i in range(12):
        c = (CY_, MG_, LM_, PAPER)[i % 4]
        box(img, M + bw * i, by, M + bw * (i + 1), by + 22 * V, c, 0.85)

    # ── 발 ───────────────────────────────────────────────
    fy = H * (0.800 if story else 0.788)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.96, 0.12)), 0.12),
          W / 2, fy, color=PAPER, a=0.95, anchor='c')
    prog = '  ·  '.join(sorted(EV.PROGRAM))
    paint(img, tmask(prog, BRAND, int(20 * V), 0.30), W / 2, fy + 44 * V,
          color=LM_, a=0.95, anchor='c')

    gy = H * (0.862 if story else 0.850)
    rule(img, gy, M, W - M, PAPER, 0.20, max(1, int(2 * V)))
    paint(img, tmask(f'{EV.DATE}   ·   {EV.TIME}', KR, int(24 * V), 0.02), W / 2, gy + 38 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}   {EV.ADDR}', KR, int(16 * V), 0.02), W / 2, gy + 70 * V,
          color=DIM, a=0.95, anchor='c')
    # 협업 줄과 핸들이 같은 자리에 겹쳤다. 발끝은 **고정 좌표가 아니라
    # 바로 위 줄에서 이어 내려야** 두 사이즈에서 다 안 겹친다.
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, gy + 102 * V,
          color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, gy + 132 * V,
          color=MG_, a=0.95, anchor='c')

    vignette(img, 0.24, 2.8)
    grain(img, 0.011, 38)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'misreg_{k}')
        save(im, f'misreg_{k}')
