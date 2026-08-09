"""
U안 — **소리 지르는 판.** 글자가 판을 넘칩니다.

G안(라인업 블록)과 정반대입니다. 거기는 여백으로 격을 만들었고,
여기는 **여백을 없애서** 소리를 지릅니다. 낱말을 화면보다 크게 키워
양옆을 잘라 내면, 잘린 글자가 "이 판에 다 안 들어간다"고 말합니다.

**넘치는 건 한 낱말까지.** 전부 넘치면 못 읽고, 못 읽으면 시끄럽기만 합니다.
SUNSET 하나만 넘기고 나머지는 판 안에 둡니다.

반전 블록을 겹쳐 쌓아 계단을 만듭니다 — 같은 글자가 밝은 판과 어두운 판을
가로지르면 획이 반씩 뒤집혀 보여서, 정지한 판인데 움직이는 것처럼 읽힙니다.

python poster_scream.py  →  out/poster/scream_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, fit, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.030, 0.028, 0.026])
BURN  = np.float32([1.00, 0.36, 0.02])            # 형광 오렌지
PAPER = np.float32([0.96, 0.95, 0.92])
DIM   = np.float32([0.56, 0.53, 0.50])


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    M = int(W * 0.055)
    CWD = W - M * 2

    ty = H * (0.058 if story else 0.052)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=DIM, a=0.95)
    paint(img, tmask(EV.DATE, KR, int(21 * V), 0.02), W - M, ty, color=BURN, anchor='r')

    # ── AFTER : 판 안에 딱 맞게 ──────────────────────────
    ay = H * (0.190 if story else 0.180)
    asz = fit('AFTER', BRAND, CWD, 0.0)
    am = tmask('AFTER', BRAND, asz, 0.0)
    paint(img, am, W / 2, ay, color=PAPER, anchor='c')

    # ── SUNSET : **판을 넘긴다.** 잘린 글자가 소리를 지른다 ──
    sy = ay + am.shape[0] * 0.98
    ssz = fit('SUNSET', BRAND, int(W * 1.34), 0.0)
    sm = tmask('SUNSET', BRAND, ssz, 0.0)
    # 반전 계단 — 밝은 판이 글자 아래쪽 절반을 가로지른다
    cut = sy + sm.shape[0] * 0.16
    box(img, 0, cut, W, cut + sm.shape[0] * 0.62, BURN, 1.0)
    paint(img, sm, W / 2, sy, color=PAPER, anchor='c')
    # 밝은 판 위에 걸친 부분만 검정으로 되돌린다 — 같은 글자가 반씩 뒤집힌다
    y0, y1 = int(cut), int(cut + sm.shape[0] * 0.62)
    sub = np.zeros((H, W, 3), np.float32)
    paint(sub, sm, W / 2, sy, color=np.float32([1, 1, 1]), anchor='c')
    k = sub[y0:y1, :, :1]
    img[y0:y1] = img[y0:y1] * (1 - k) + INK * k

    # ── 라인업 : 반전 띠 아래, 굵게 두 줄 ────────────────
    ly = cut + sm.shape[0] * 0.62 + 78 * V
    half = (len(EV.LINEUP) + 1) // 2
    for j, part in enumerate((EV.LINEUP[:half], EV.LINEUP[half:])):
        txt = '  '.join(part)
        s = justify(txt, CWD, 0.04, cap=int(96 * V))
        paint(img, tmask(txt, BRAND, s, 0.04), W / 2, ly + j * (s * 1.18),
              color=PAPER, a=0.98, anchor='c')
    py = ly + 2 * (justify('  '.join(EV.LINEUP[:half]), CWD, 0.04, cap=int(96 * V)) * 1.18)
    prog = '  ·  '.join(sorted(EV.PROGRAM))
    box(img, M, py - 30 * V, W - M, py + 30 * V, BURN, 1.0)
    paint(img, tmask(prog, BRAND, int(28 * V), 0.24), W / 2, py, color=INK, anchor='c')

    # ── 발 ───────────────────────────────────────────────
    fy = H * (0.858 if story else 0.848)
    rule(img, fy, M, W - M, PAPER, 0.24, max(2, int(3 * V)))
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, fy + 42 * V,
          color=BURN, anchor='c')
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(21 * V), 0.02),
          W / 2, fy + 80 * V, color=PAPER, a=0.95, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02), W / 2, fy + 112 * V,
          color=DIM, a=0.90, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, H * 0.948,
          color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), W / 2, H * 0.976,
          color=BURN, a=0.95, anchor='c')

    vignette(img, 0.24, 2.8)
    grain(img, 0.010, 32)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'scream_{k}')
        save(im, f'scream_{k}')
