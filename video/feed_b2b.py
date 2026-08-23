"""
**백투백 피드 3연작.** 격자에서 한 판으로 보인다.

    python feed_b2b.py   →  out/feed_b2b/ 세 장 + 이어붙인 확인용 한 장

## 왜 세 칸인가

백투백은 두 세트다. 두 장만 올리면 격자에서 **한 줄이 안 채워진다** —
인스타 격자는 세 칸이 한 줄이라 두 장은 어중간하게 걸린다.

가운데에 타이틀 칸을 둔다. 양쪽 세트가 **타이틀을 사이에 두고 마주 본다** —
왼쪽 사람들은 오른쪽을 보고, 오른쪽 사람들은 왼쪽을 본다.

    왼쪽     HEIDY × CHIPS   22:00
    가운데   BACK TO BACK    무엇인지 설명하는 자리
    오른쪽   DEMIC × AROS    22:30

## 올리는 순서 — 거꾸로다

격자는 **최신이 왼쪽 위**다. 오른쪽 칸을 먼저 올린다. 파일 앞의 숫자가
올리는 차례다.

## 잘리는 자리

피드 게시물은 **4:5(1080×1350) 그대로 올린다** — 커버처럼 9:16 으로
늘리지 않는다. 다만 프로필 격자는 그걸 다시 **정사각으로 자른다.**

    올리는 판    1080 × 1350
    격자에 보임  가운데 정사각 (y 135 ~ 1215)

얼굴과 이름은 그 정사각 안에 둔다. 발치는 잘려도 된다.
"""
import os

import cv2
import numpy as np
from PIL import Image

import event as EV
from cover_reels import band, TW, TH, W, H, SAFE_T, SAFE_B
from fest_kit import justify, specks, vignette
from fonts import KR, KRB
from members import get
from poster_crew import crop_head, rimlight
from poster_dj3 import chrome
from poster_dj4 import fringe, sharpen, melt
from poster_dj7 import PAPER, SILVER, STEEL, DIM, SLOGAN
from poster_kit import BRAND, tmask, paint, rule, glow, outline, grain, logo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_b2b')
os.makedirs(OUT, exist_ok=True)

# (칸 안에서의 중심 x 비율, 세로 위치, 앞에 오는지)
# **완전히 갈라 놓으면 두 장을 나란히 붙인 판이 된다.** 겹쳐야 '같이 선다'
SIDES = [(0.300, 0.190, False), (0.690, 0.168, True)]
BASE_H = int(TH * 0.640)


def figure(img, name, cx_abs, ytop, front, seed):
    """한 사람. `cx_abs` 는 이어붙인 판 전체 기준 가로 중심(px)."""
    fw = int(TW * 0.80)
    fig = crop_head(name, fw, BASE_H)
    x0 = int(cx_abs - fw / 2)
    top = int(H * ytop)
    sx0, sx1 = max(0, x0), min(W, x0 + fw)
    sy1 = min(H, top + BASE_H)
    if sx1 <= sx0 or sy1 <= top:
        return
    a_ = np.clip((fig[:sy1 - top, sx0 - x0:sx1 - x0, 3].copy() - 0.045) / 0.955,
                 0, 1)
    px = np.clip(fig[:sy1 - top, sx0 - x0:sx1 - x0, :3], 0, 1).copy()
    px = sharpen(px, 2.4, 0.62)
    a_, px = melt(a_, px, 0.34, seed, 1.0)

    sl = (slice(top, sy1), slice(sx0, sx1))
    dim = 1.0 if front else 0.82
    back = cv2.GaussianBlur(a_, (0, 0), 24.0)
    img[sl] *= (1 - back[..., None] * (0.62 if front else 0.50))
    img[sl] += rimlight(a_, 1.0)[..., None] * PAPER * (0.52 if front else 0.40)
    img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None] * dim


def set_cell(img, i, pair, slot):
    """세트 한 칸. 사람 둘 → 이름 → 앞사람 순으로 얹는다."""
    x0 = i * TW
    cx = x0 + TW / 2
    label = EV.B2B.join(pair)

    paint(img, tmask(f'{slot[0]} — {slot[1]}', BRAND, 26, 0.24), cx,
          SAFE_T + 70, color=PAPER, a=0.92, anchor='c')
    rule(img, SAFE_T + 118, x0 + TW * 0.30, x0 + TW * 0.70, SILVER, 0.40, 2)

    for who, (rx, ytop, front) in zip(pair, SIDES):
        if not front:
            figure(img, who, x0 + TW * rx, ytop, front, len(who) * 37)

    # 이름은 앞사람 뒤에 — 어깨가 글자를 살짝 덮어야 깊이가 생긴다
    ny = H * 0.760
    ns = justify(label, TW * 0.84, 0.01, cap=90)
    nm = tmask(label, BRAND, ns, 0.01)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.030)),) * 2))
    sh = cv2.GaussianBlur(nm.astype(np.float32) / 255.0, (0, 0), 13.0)
    paint(img, (sh * 255).astype(np.uint8), cx, ny + 10,
          color=np.float32([0, 0, 0]), a=0.72, anchor='c')
    glow(img, nm, cx, ny, SILVER, 0.28, 26, anchor='c')
    chrome(img, nm, cx, ny, PAPER, STEEL)

    for who, (rx, ytop, front) in zip(pair, SIDES):
        if front:
            figure(img, who, x0 + TW * rx, ytop, front, len(who) * 37 + 11)

    paint(img, tmask(label, BRAND, ns, 0.01), cx, ny, color=PAPER, a=0.46,
          anchor='c')
    paint(img, outline(nm, 3), cx, ny, color=PAPER, a=0.94, anchor='c')

    igs = '   ·   '.join('@' + get(w)['instagram'] for w in pair
                         if get(w)['instagram'])
    paint(img, tmask(igs, KR, 25, 0.02), cx, SAFE_B - 42, color=PAPER,
          a=0.90, anchor='c')


def title_cell(img, i):
    """가운데. **여기만 설명한다** — 양쪽 칸은 누가 서는지만 말한다."""
    x0 = i * TW
    cx = x0 + TW / 2
    lg = logo(120)
    paint(img, lg, cx - lg.shape[1] / 2, SAFE_T + 145, color=PAPER, a=0.95)

    nm = tmask('BACK TO BACK', BRAND, 74, 0.14)
    glow(img, nm, cx, SAFE_T + 320, SILVER, 0.24, 26, anchor='c')
    chrome(img, nm, cx, SAFE_T + 320, PAPER, STEEL)
    paint(img, outline(nm, 3), cx, SAFE_T + 320, color=PAPER, a=0.92,
          anchor='c')

    paint(img, tmask('둘이 한 부스에 선다', KRB, 34, 0.01), cx, SAFE_T + 400,
          color=PAPER, a=0.94, anchor='c')
    paint(img, tmask('한 명이 곡을 걸고 다른 한 명이 받는다', KR, 25, 0.02),
          cx, SAFE_T + 452, color=SILVER, a=0.86, anchor='c')

    rule(img, SAFE_T + 520, x0 + TW * 0.20, x0 + TW * 0.80, SILVER, 0.40, 2)

    paint(img, tmask(EV.NAME, BRAND, 60, 0.10), cx, SAFE_T + 600,
          color=PAPER, anchor='c')
    y = SAFE_T + 665
    for line in (EV.DATE_EN, EV.VENUE, EV.ADDR):
        paint(img, tmask(line, KR, 25, 0.02), cx, y, color=PAPER, a=0.90,
              anchor='c')
        y += 44
    # 솔로파티 안에서 도는 세트라는 걸 여기서 말한다 — 양쪽 칸에 적으면
    # 같은 말이 두 번이다
    paint(img, tmask('솔로파티 시간 · 다른 부스', KR, 23, 0.02), cx, y + 24,
          color=SILVER, a=0.84, anchor='c')
    paint(img, tmask(EV.RESERVE, KRB, 27, 0.01), cx, SAFE_B - 95,
          color=PAPER, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 19, 0.24), cx, SAFE_B - 40,
          color=SILVER, a=0.72, anchor='c')


def build():
    sets = [(tuple(n.split(EV.B2B)), (s, e)) for s, e, n in EV.B2B_SETS]
    if len(sets) != 2:
        raise SystemExit(f'백투백 세트가 둘이어야 합니다 — 지금 {len(sets)}개')

    img = band()
    set_cell(img, 0, *sets[0])
    title_cell(img, 1)
    set_cell(img, 2, *sets[1])

    specks(img, 240, 0, H, PAPER, 0.15, seed=61, rmax=2.4)
    grain(img, 0.006, 43)
    img = np.clip(img, 0, 1)

    Image.fromarray((img * 255).astype(np.uint8)).save(
        os.path.join(OUT, 'b2b_full.png'), optimize=True)

    # (칸, 올리는 차례, 파일 이름)
    slots = [(0, 3, 'A_' + '_'.join(sets[0][0]).lower(), '왼쪽'),
             (1, 2, 'B_title', '가운데'),
             (2, 1, 'C_' + '_'.join(sets[1][0]).lower(), '오른쪽')]
    for i, order, tag, where in slots:
        piece = np.ascontiguousarray(img[:, i * TW:(i + 1) * TW])
        vignette(piece, 0.30, 2.2)
        fringe(piece, 0.0012)
        p = os.path.join(OUT, f'{order}_{tag}.png')
        Image.fromarray((np.clip(piece, 0, 1) * 255).astype(np.uint8)).save(
            p, optimize=True)
        print(f'{p}   {where} 칸 · {order}번째로 올림')

    print()
    print('올리는 순서 — **거꾸로다.** 격자는 최신이 왼쪽 위다')
    for i, order, tag, where in sorted(slots, key=lambda s: s[1]):
        print(f'  {order}) {order}_{tag}.png  → {where} 칸')
    return OUT


if __name__ == '__main__':
    build()
