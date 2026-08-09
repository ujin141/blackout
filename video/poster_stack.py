"""
K안 — **활판 밴드.** 옛날 흥행 포스터(권투·서커스·공연)의 짜임입니다.

판을 가로 띠로 자르고 띠마다 낱말 하나를 **전폭으로** 채웁니다.
낱말 길이가 다르니 크기가 저절로 달라지고, 그 차이가 리듬이 됩니다.
글자가 곧 판이라 여백이 없습니다 — 페스티벌 포스터 중 제일 시끄러운 판입니다.

**반전 띠는 딱 하나만 둡니다.** 밤 행사라 밝은 면이 여럿이면 낮 행사처럼 보이고,
하나면 그 띠가 시선을 독점합니다(E안 그리드에서 배운 것과 같습니다).

띠 높이는 픽셀이 아니라 **비중**으로 잡습니다 — 피드와 스토리는 세로가 1.42배
차이 나서 픽셀로 박으면 한쪽이 남거나 넘칩니다.

python poster_stack.py  →  out/poster/stack_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.030, 0.032, 0.030])
PAPER = np.float32([0.94, 0.95, 0.90])
ACID  = np.float32([0.78, 0.96, 0.20])            # 반전 띠에 쓰는 산성 라임
DIM   = np.float32([0.56, 0.60, 0.54])


def rough(img, y0, y1, seed=3, amt=0.06):
    """띠 가장자리를 아주 조금 흩뜨린다. **활판은 가장자리가 깨끗하지 않다** —
    자로 자른 듯 반듯하면 인쇄물이 아니라 화면 그래픽으로 보인다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    for y in (int(y0), int(y1) - 1):
        if not (0 <= y < H):
            continue
        n = rng.random(W) < amt
        img[y][n] = img[max(0, y - 1)][n]


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    M = int(W * 0.055)
    CWD = W - M * 2

    # 띠 — (내용, 비중). 비중 합으로 나눠야 두 사이즈에서 같은 짜임이 나온다
    half = (len(EV.LINEUP) + 1) // 2
    ROWS = [
        ('label', 'BLACKOUT CREW  ·  SEOUL', 0.52),
        ('word',  'AFTER',                   1.35),
        # **유일한 밝은 띠.** 0.92 로 뒀더니 밝은 픽셀이 14.7% 가 돼 낮 행사처럼 보였다.
        # 띠 하나가 시선을 독점하는 데 필요한 건 넓이가 아니라 유일함이다.
        ('invert', EV.DATE,                  0.42),
        ('word',  'SUNSET',                  1.35),
        ('label', EV.FORMAT,                 0.50),
        ('line',  '  ·  '.join(EV.LINEUP[:half]), 0.72),
        ('line',  '  ·  '.join(EV.LINEUP[half:]), 0.72),
        ('prog',  '  ·  '.join(sorted(EV.PROGRAM)), 0.60),
        ('foot',  '', 1.05),
    ]
    top, bot = H * 0.045, H * 0.955
    tot = sum(w for _, _, w in ROWS)
    y = top
    for kind, txt, w in ROWS:
        h = (bot - top) * w / tot
        cy = y + h / 2

        if kind == 'invert':
            box(img, 0, y + h * 0.06, W, y + h * 0.94, ACID, 1.0)
            rough(img, y + h * 0.06, y + h * 0.94, seed=int(y) % 97)
            s = justify(txt, CWD * 0.86, 0.06, path=KR, cap=int(h * 0.62))
            paint(img, tmask(txt, KR, s, 0.06), W / 2, cy, color=INK, anchor='c')
        elif kind == 'word':
            s = justify(txt, CWD, 0.02, cap=int(h * 1.05))
            paint(img, tmask(txt, BRAND, s, 0.02), W / 2, cy, color=PAPER, anchor='c')
        elif kind == 'line':
            s = justify(txt, CWD * 0.96, 0.10, cap=int(h * 0.66))
            paint(img, tmask(txt, BRAND, s, 0.10), W / 2, cy, color=PAPER, a=0.95, anchor='c')
        elif kind == 'prog':
            s = justify(txt, CWD * 0.58, 0.20, cap=int(h * 0.50))
            paint(img, tmask(txt, BRAND, s, 0.20), W / 2, cy, color=ACID, a=0.92, anchor='c')
        elif kind == 'label':
            s = min(int(22 * V), int(h * 0.44))
            paint(img, tmask(txt, BRAND, s, 0.40), W / 2, cy, color=DIM, a=0.95, anchor='c')
        else:                                              # foot
            paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(23 * V), 0.02),
                  W / 2, cy - h * 0.26, color=PAPER, a=0.95, anchor='c')
            paint(img, tmask(EV.ADDR, KR, int(16 * V), 0.02),
                  W / 2, cy - h * 0.02, color=DIM, a=0.85, anchor='c')
            paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30),
                  W / 2, cy + h * 0.22, color=DIM, a=0.60, anchor='c')
            paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26),
                  W / 2, cy + h * 0.42, color=ACID, a=0.80, anchor='c')

        # 띠 사이 괘선. 활판은 칸을 선으로 나눈다
        if kind not in ('invert',) and y > top + 1:
            rule(img, y, M, W - M, PAPER, 0.14, max(1, int(2 * V)))
        y += h

    # 잉크가 번진 느낌. 아주 약하게 — 세게 주면 초점 안 맞은 사진이 된다
    img[:] = img * 0.94 + cv2.GaussianBlur(img, (0, 0), 1.6) * 0.06
    vignette(img, 0.26, 2.8)
    grain(img, 0.010, 12)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'stack_{k}')
        save(im, f'stack_{k}')
