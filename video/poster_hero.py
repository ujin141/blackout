"""
**사진이 주인공인 판.** 위아래를 비우고 사진을 띠로 앉힌다.

    python poster_hero.py            피드 · 스토리 · 정사각
    python poster_hero.py story      골라서

## 왜 배경으로 안 깔았나

지금까지 판은 전부 사진을 **바탕으로 깔고 그 위에 글자를 얹었다.** 그러려면
사진을 어둡게 눌러야 하고(안 그러면 글자가 안 읽힌다), 눌리면 사진이 사진이
아니라 질감이 된다.

`pool-model-3` 은 물빛과 핑크가 강하고 물방울까지 살아 있는 사진이라 그렇게
쓰면 아깝다. **띠로 잘라 통째로 보여 주고, 글자는 위아래 검정에 둔다.**
잡지 표지의 문법이고, 우리 판 중에는 아직 없다.

## 색 규칙은 그대로다

`poster_dj7` 이 정한 것 — **판은 검정·흰색·은색, 색은 사람에게만.**
여기서 색이 있는 건 사진 한 장뿐이고 글자·선·로고는 전부 무채색이다.
사진을 듀오톤으로 누르면 브랜드 톤에는 맞지만 이 판을 만든 이유가 사라진다.

## 사진을 어디까지 자르나

원본은 6000×4000 가로다. 세로 판에 그냥 넣으면 좌우가 크게 잘린다.

    띠 비율   1080 × 840 (1.286:1) — 원본 1.5:1 에서 좌우를 조금 덜어낸다
    가로 중심 0.56. 인물이 화면 오른쪽에 치우쳐 있어 가운데로 두면 몸이 잘린다
    세로      다 쓴다. 위는 목, 아래는 골반까지가 한 장에 들어간다

**얼굴이 없는 사진이라 이 판이 성립한다.** 얼굴이 있으면 모델 화보가 되고,
없으니 풀파티 그 자체로 읽힌다.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

import event as EV
from fest_kit import justify, night, specks, vignette
from fonts import KR, KRB
from poster_dj3 import chrome
from poster_dj4 import fringe
from poster_dj7 import PAPER, SILVER, STEEL, DIM, SLOGAN
from poster_kit import (BRAND, IMG, tmask, tmask_bl, paint, paint_bl, rule,
                        glow, outline, grain, logo, save)

HERE = os.path.dirname(os.path.abspath(__file__))
PHOTO = os.path.join(IMG, 'stock', 'pool-model-3.jpg')

# (폭, 높이, 사진 띠의 위/아래 비율) — 스토리는 UI 를 피해 띠를 위로 올린다
# **띠를 크게 잡으면 아래 정보가 판 밖으로 밀린다.** 처음에 0.80 까지
# 내렸다가 주소가 통째로 잘렸다 — 행사명·정보·발치가 들어갈 높이를 먼저
# 빼고 남는 만큼만 사진에 준다
SIZES = {'feed':  (1080, 1350, 0.150, 0.560),
         'story': (1080, 1920, 0.175, 0.520),
         'sq':    (1080, 1080, 0.150, 0.500)}

PHOTO_CX = 0.56          # 인물이 오른쪽에 치우쳐 있다. 0.5 로 두면 몸이 잘린다


def band(W, bh):
    """사진 띠. **원본 비율에서 좌우만 덜어낸다** — 세로를 자르면 몸통이 끊긴다."""
    im = cv2.imdecode(np.fromfile(PHOTO, np.uint8), cv2.IMREAD_COLOR)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    h, w = im.shape[:2]
    need_w = int(round(h * (W / bh)))
    need_w = min(need_w, w)
    x0 = int(round(w * PHOTO_CX - need_w / 2))
    x0 = max(0, min(w - need_w, x0))
    crop = im[:, x0:x0 + need_w]
    out = cv2.resize(crop, (W, bh), interpolation=cv2.INTER_AREA)
    # 아주 살짝만 — 판 전체가 어두워서 사진이 뜨는 걸 눌러 준다
    out = np.clip((out - 0.5) * 1.04 + 0.5, 0, 1)
    return out


def build(W, H, top_r, bot_r, story=False):
    V = W / 1080.0
    M = int(W * 0.082)
    y0, y1 = (H * 0.085, H * 0.876) if story else (H * 0.030, H * 0.972)

    img = np.repeat(np.repeat(np.float32([0.014, 0.014, 0.019])[None, None, :],
                              H, 0), W, 1).copy()

    # ── 사진 띠 ──────────────────────────────────────────
    bt, bb = int(H * top_r), int(H * bot_r)
    img[bt:bb] = band(W, bb - bt)
    # 띠 위아래로 아주 짧게 어둠을 흘린다 — 자른 선이 그대로 보이면
    # 붙여 넣은 사진이 되고, 흘리면 판에 들어앉은 것이 된다
    fade = int(H * 0.028)
    for k in range(fade):
        t = (1 - k / fade) ** 1.5
        img[bt + k] *= (1 - 0.85 * t)
        img[bb - 1 - k] *= (1 - 0.85 * t)
    rule(img, bt, 0, W, SILVER, 0.30, max(1, int(2 * V)))
    rule(img, bb, 0, W, SILVER, 0.30, max(1, int(2 * V)))

    # ── 머리 ─────────────────────────────────────────────
    lg = logo(int(42 * V))
    paint(img, lg, W / 2 - lg.shape[1] / 2, y0 + 36 * V, color=PAPER, a=0.95)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(15 * V), 0.34), M, y0 + 40 * V,
          color=DIM, a=0.82, anchor='l')
    paint(img, tmask(EV.DATE_EN, BRAND, int(15 * V), 0.22), W - M, y0 + 40 * V,
          color=SILVER, a=0.92, anchor='r')

    # ── 행사명 — 띠 아래에 걸친다 ────────────────────────
    ny = bb + 62 * V
    ns = justify(EV.NAME, W - M * 2, 0.06, cap=int(112 * V))
    nm = tmask(EV.NAME, BRAND, ns, 0.06)
    glow(img, nm, W / 2, ny, SILVER, 0.24, int(26 * V), anchor='c')
    chrome(img, nm, W / 2, ny, PAPER, STEEL)
    paint(img, outline(nm, max(2, int(2.6 * V))), W / 2, ny, color=PAPER,
          a=0.92, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(18 * V), 0.32), W / 2, ny + ns * 0.70,
          color=SILVER, a=0.86, anchor='c')

    # ── 정보 ─────────────────────────────────────────────
    y = ny + ns * 0.70 + 54 * V
    rule(img, y, M, W - M, SILVER, 0.34, max(1, int(2 * V)))
    y += 50 * V
    paint(img, tmask(f'{EV.DATE}  ·  {EV.TIME}', KRB, int(31 * V), 0.01),
          W / 2, y, color=PAPER, anchor='c')
    y += 46 * V
    paint(img, tmask(f'{EV.VENUE}  ·  {EV.ADDR}', KR, int(22 * V), 0.02),
          W / 2, y, color=SILVER, a=0.92, anchor='c')
    y += 52 * V
    # **지금 파는 것.** 판을 다시 뽑을 때마다 event.py 에서 따라온다
    if EV.LAST_LINES:
        paint(img, tmask(f'{EV.OPEN_WAVE[0]} {EV.OPEN_LEFT}자리  ·  '
                         f'{EV.LAST_LINES[0]}', KRB, int(27 * V), 0.01),
              W / 2, y, color=PAPER, anchor='c')
    else:
        paint(img, tmask(EV.LEFT_LINE, KRB, int(27 * V), 0.01), W / 2, y,
              color=PAPER, anchor='c')
    y += 42 * V
    paint(img, tmask(f'{EV.ENTRY}  ·  {EV.PRICE_PUSH}', KR, int(20 * V), 0.02),
          W / 2, y, color=SILVER, a=0.88, anchor='c')

    # ── 발 ───────────────────────────────────────────────
    fy = y1 - 26 * V
    paint(img, tmask(SLOGAN, BRAND, int(12 * V), 0.30), W / 2, fy, color=DIM,
          a=0.58, anchor='c')
    fy -= 40 * V
    paint(img, tmask(EV.HANDLE, BRAND, int(17 * V), 0.24), M, fy, color=SILVER,
          a=0.88, anchor='l')
    paint(img, tmask(EV.RESERVE, KRB, int(19 * V), 0.01), W - M, fy,
          color=PAPER, a=0.96, anchor='r')

    if story:
        rule(img, int(y1), 0, W, SILVER, 0.30, max(1, int(2 * V)))

    specks(img, 90, 0, bt, PAPER, 0.12, seed=41, rmax=2.2)
    fringe(img, 0.0010)
    vignette(img, 0.34, 2.4)
    grain(img, 0.005, 17)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    if not os.path.exists(PHOTO):
        raise SystemExit(f'사진이 없습니다: {PHOTO}')
    want = [a.lower() for a in sys.argv[1:]] or list(SIZES)
    for k in want:
        if k not in SIZES:
            raise SystemExit(f'{k} 은 없는 크기입니다 — {", ".join(SIZES)}')
        w, h, tr, br = SIZES[k]
        im = build(w, h, tr, br, story=(k == 'story'))
        night(im, f'hero_{k}')
        save(im, f'hero_{k}')
