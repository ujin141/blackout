"""
**릴스 세 개를 피드에서 잇는 커버.**

    python cover_reels.py   →  out/cover/ 커버 세 장 + 이어붙인 확인용 한 장

## 무엇을 잇고 무엇을 안 잇나

    **배경은 잇는다**   세 칸을 가로지르는 큰 링과 물결. 격자에서 한 장으로
                       보이는 건 이것 때문이다
    **글자는 안 잇는다** 칸마다 그 안에서 완결된다. 릴스를 하나만 열어 본
                       사람에게도 말이 돼야 한다 — 'AFTER SUN' 까지만 보이면
                       그건 잘린 판이지 이어지는 판이 아니다

## 격자에서 보이는 자리

커버는 1080×1920 으로 올리지만 **프로필 격자는 가운데만 보여 준다.**
4:5(1080×1350)로 잘리고, 예전 계정은 정사각으로 잘린다. 둘 다 통하게
핵심 요소를 **정사각 안**에 둔다.

    커버 캔버스   1080 × 1920
    격자에 보임   가운데 1080 × 1350   (커버의 y 285~1635)
    안전한 자리   그 안의 정사각        (커버의 y 420~1500)

## 올리는 순서 — 거꾸로다

인스타 격자는 **최신이 왼쪽 위**다. 왼쪽 칸을 마지막에 올려야 한다.
순서를 틀리면 그림이 뒤집힌다. 파일 이름 앞의 숫자가 올리는 차례다.

## 세트가 둘이다

    python cover_reels.py         cut  — close · neon · water (지금 쓰는 것)
    python cover_reels.py first   lineup · sunset · pool (먼저 나간 세 편)

**릴스가 바뀌면 커버 내용도 바뀌어야 한다.** 배경과 조각 내는 방식은
같지만 칸에 들어가는 말이 다르다 — 마감 릴스 커버에 라인업을 적으면
열어 본 사람이 딴 걸 보게 된다.

## 어느 칸에 뭘 둘지

**제일 급한 걸 왼쪽에 둔다.** 격자에서 왼쪽 위가 최신이라 프로필을
연 사람이 거기부터 본다 — 지금은 마감이 거기다.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

import event as EV
from fest_kit import vignette, specks
from fonts import KR, KRB
from poster_dj4 import fringe, nebula
from poster_dj7 import PAPER, SILVER, STEEL, DIM
from poster_kit import BRAND, tmask, paint, rule, glow, grain, logo

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'cover')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350                  # 격자에 보이는 한 칸
W, H = TW * 3, TH                    # 이어붙인 판
CW, CH = 1080, 1920                  # 실제로 올리는 커버
PAD = (CH - TH) // 2                 # 위아래로 늘리는 양 (285)
SAFE_T, SAFE_B = 135, 1215           # 정사각으로 잘려도 남는 구간

# (파일 앞 글자, 올리는 차례, 릴스, 칸 제목)
SETS = {
    'cut':   [('A', 3, 'close', '왼쪽'),
              ('B', 2, 'neon', '가운데'),
              ('C', 1, 'water', '오른쪽')],
    'first': [('A', 3, 'lineup', '왼쪽'),
              ('B', 2, 'sunset', '가운데'),
              ('C', 1, 'pool', '오른쪽')],
}


def band():
    """세 칸을 가로지르는 판. **여기서 이어지는 건 배경뿐이다.**"""
    img = np.repeat(np.repeat(np.float32([0.016, 0.016, 0.021])[None, None, :],
                              H, 0), W, 1).copy()
    img += nebula(W, H, W * 0.5, H * 0.46, STEEL * 1.5, SILVER,
                  seed=31, spread=0.86)

    # 세 칸을 관통하는 큰 링 두 개. 칸 하나에는 호(弧)로만 보인다
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    for r, a in ((W * 0.30, 0.40), (W * 0.395, 0.22)):
        d = np.abs(np.sqrt((xx - W / 2) ** 2 + ((yy - H * 0.52) * 1.35) ** 2) - r)
        img += np.exp(-(d / 2.6) ** 2)[..., None] * SILVER * a

    # 물결 한 줄 — 풀파티라는 걸 배경이 말한다
    base = H * 0.80
    for k, (amp, a, sp) in enumerate(((26, 0.30, 0.0028), (16, 0.18, 0.0045))):
        y = base + k * 34 + np.sin(np.arange(W) * sp) * amp
        for x in range(W):
            yi = int(y[x])
            if 2 < yi < H - 2:
                img[yi - 1:yi + 2, x] += SILVER * a * 0.5
    return img


def cell(img, i, draw):
    """칸 하나에 글자를 앉힌다. x 는 칸 기준."""
    x0 = i * TW
    draw(img, x0 + TW / 2, x0)


def build(setname='cut'):
    slots = SETS[setname]
    img = band()

    # ── 왼쪽 · 라인업 ─────────────────────────────────────
    def left(im, cx, x0):
        paint(im, tmask('LINE UP', BRAND, 62, 0.30), cx, SAFE_T + 190,
              color=PAPER, anchor='c')
        rule(im, SAFE_T + 250, x0 + TW * 0.22, x0 + TW * 0.78, SILVER, 0.45, 2)
        y = SAFE_T + 320
        for n in EV.LINEUP:
            paint(im, tmask(n, BRAND, 40, 0.14), cx, y, color=PAPER, a=0.92,
                  anchor='c')
            y += 66
        paint(im, tmask(f'DJ {len(EV.LINEUP)}', BRAND, 22, 0.30), cx, y + 26,
              color=SILVER, a=0.70, anchor='c')

    # ── 가운데 · 행사 ─────────────────────────────────────
    def mid(im, cx, x0):
        lg = logo(132)
        paint(im, lg, cx - lg.shape[1] / 2, SAFE_T + 150, color=PAPER, a=0.95)
        paint(im, tmask(EV.NAME, BRAND, 104, 0.08), cx, SAFE_T + 350,
              color=PAPER, anchor='c')
        paint(im, tmask(EV.FORMAT, BRAND, 21, 0.32), cx, SAFE_T + 420,
              color=SILVER, a=0.80, anchor='c')
        rule(im, SAFE_T + 470, x0 + TW * 0.16, x0 + TW * 0.84, SILVER, 0.45, 2)
        y = SAFE_T + 545
        for line in (EV.DATE_EN, EV.VENUE, EV.ADDR):
            paint(im, tmask(line, KR, 27, 0.02), cx, y, color=PAPER, a=0.92,
                  anchor='c')
            y += 48
        paint(im, tmask(EV.TIME_EN, BRAND, 20, 0.22), cx, y + 14,
              color=SILVER, a=0.75, anchor='c')

    # ── 오른쪽 · 예약 ─────────────────────────────────────
    def right(im, cx, x0):
        paint(im, tmask('POOL  ×  SOLO', BRAND, 44, 0.20), cx, SAFE_T + 190,
              color=PAPER, anchor='c')
        rule(im, SAFE_T + 250, x0 + TW * 0.22, x0 + TW * 0.78, SILVER, 0.45, 2)
        paint(im, tmask(EV.TAGLINE, KRB, 34, 0.01), cx, SAFE_T + 340,
              color=PAPER, a=0.94, anchor='c')
        y = SAFE_T + 440
        for line in EV.STATUS_LINES:
            paint(im, tmask(line, KR, 25, 0.02), cx, y, color=PAPER, a=0.86,
                  anchor='c')
            y += 46
        paint(im, tmask(EV.RESERVE, KRB, 30, 0.01), cx, y + 32,
              color=PAPER, anchor='c')
        paint(im, tmask(EV.HANDLE, BRAND, 19, 0.24), cx, y + 92,
              color=SILVER, a=0.72, anchor='c')

    # ── cut 세트 ─────────────────────────────────────────
    def c_left(im, cx, x0):
        """마감. **숫자가 제일 크다** — 격자에서 이것만 읽혀도 된다."""
        paint(im, tmask(f'{EV.OPEN_WAVE[0]} 마감', KRB, 40, 0.01), cx,
              SAFE_T + 150, color=SILVER, a=0.92, anchor='c')
        rule(im, SAFE_T + 205, x0 + TW * 0.24, x0 + TW * 0.76, SILVER, 0.45, 2)
        big = tmask(str(EV.OPEN_LEFT), BRAND, 300, 0.02)
        paint(im, big, cx, SAFE_T + 400, color=PAPER, anchor='c')
        paint(im, tmask('자리 남았습니다', KRB, 40, 0.01), cx, SAFE_T + 600,
              color=PAPER, a=0.94, anchor='c')
        paint(im, tmask('오늘 자정에 닫습니다', KR, 30, 0.02), cx, SAFE_T + 665,
              color=SILVER, a=0.88, anchor='c')
        # **막대가 있어야 10 이 왜 급한지가 보인다.** 숫자만 있으면 정원이
        # 얼마인지 모르니 열 자리가 많은 건지 적은 건지도 모른다
        bx0, bx1, by = x0 + TW * 0.24, x0 + TW * 0.76, SAFE_T + 790
        cv2.rectangle(im, (int(bx0), int(by)), (int(bx1), int(by + 16)),
                      tuple(float(v) for v in SILVER * 0.22), -1)
        w = EV.OPEN_WAVE[2] / EV.OPEN_WAVE[1]
        cv2.rectangle(im, (int(bx0), int(by)), (int(bx0 + (bx1 - bx0) * w),
                      int(by + 16)), tuple(float(v) for v in PAPER), -1)
        # **BRAND(Michroma)에 한글을 넘기면 두부가 찍힌다.** '2차' 를 여기
        # 붙였다가 '2□' 로 나갔다 — 차수는 위 제목에 이미 있으니 숫자만
        paint(im, tmask(f'{EV.OPEN_WAVE[2]} / {EV.OPEN_WAVE[1]}', BRAND, 24,
                        0.22), cx, by + 62, color=SILVER, a=0.80, anchor='c')
        paint(im, tmask(EV.RESERVE, KRB, 30, 0.01), cx, SAFE_T + 950,
              color=PAPER, anchor='c')
        paint(im, tmask(EV.HANDLE, BRAND, 19, 0.24), cx, SAFE_T + 1010,
              color=SILVER, a=0.70, anchor='c')

    def c_mid(im, cx, x0):
        """행사. 세 칸 중 유일하게 로고와 이름이 있다."""
        lg = logo(132)
        paint(im, lg, cx - lg.shape[1] / 2, SAFE_T + 150, color=PAPER, a=0.95)
        paint(im, tmask(EV.NAME, BRAND, 104, 0.08), cx, SAFE_T + 350,
              color=PAPER, anchor='c')
        paint(im, tmask(EV.FORMAT, BRAND, 21, 0.32), cx, SAFE_T + 420,
              color=SILVER, a=0.80, anchor='c')
        rule(im, SAFE_T + 470, x0 + TW * 0.16, x0 + TW * 0.84, SILVER, 0.45, 2)
        y = SAFE_T + 545
        for line in (EV.DATE_EN, EV.VENUE, EV.ADDR):
            paint(im, tmask(line, KR, 27, 0.02), cx, y, color=PAPER, a=0.92,
                  anchor='c')
            y += 48
        paint(im, tmask(EV.TIME_EN, BRAND, 20, 0.22), cx, y + 14,
              color=SILVER, a=0.75, anchor='c')
        rule(im, SAFE_T + 780, x0 + TW * 0.30, x0 + TW * 0.70, SILVER, 0.30, 1)
        paint(im, tmask(EV.ENTRY, KR, 26, 0.02), cx, SAFE_T + 845,
              color=PAPER, a=0.90, anchor='c')
        paint(im, tmask(EV.AGE, KR, 22, 0.02), cx, SAFE_T + 900,
              color=SILVER, a=0.80, anchor='c')
        paint(im, tmask(f'AFTER PARTY   {EV.AFTER}', KR, 21, 0.02), cx,
              SAFE_T + 985, color=SILVER, a=0.72, anchor='c')

    def c_right(im, cx, x0):
        """라인업. 여덟 명을 두 줄로 — 한 줄로 세우면 칸을 넘는다."""
        paint(im, tmask('LINE UP', BRAND, 56, 0.30), cx, SAFE_T + 160,
              color=PAPER, anchor='c')
        rule(im, SAFE_T + 215, x0 + TW * 0.24, x0 + TW * 0.76, SILVER, 0.45, 2)
        y = SAFE_T + 285
        for n in EV.LINEUP:
            paint(im, tmask(n, BRAND, 38, 0.14), cx, y, color=PAPER, a=0.92,
                  anchor='c')
            y += 60
        paint(im, tmask(f'DJ {len(EV.LINEUP)}  ·  SOLO PARTY 90MIN', BRAND, 20,
                        0.24), cx, y + 30, color=SILVER, a=0.74, anchor='c')
        # 백투백은 이번에 처음 붙는 것이라 따로 세운다
        rule(im, y + 92, x0 + TW * 0.30, x0 + TW * 0.70, SILVER, 0.30, 1)
        paint(im, tmask('BACK TO BACK', BRAND, 24, 0.30), cx, y + 150,
              color=PAPER, a=0.92, anchor='c')
        yy = y + 210
        for _s, _e, n in EV.B2B_SETS:
            paint(im, tmask(n, BRAND, 26, 0.12), cx, yy, color=PAPER, a=0.88,
                  anchor='c')
            yy += 52

    cells = ((c_left, c_mid, c_right) if setname == 'cut'
             else (left, mid, right))
    for i, fn in enumerate(cells):
        cell(img, i, fn)

    specks(img, 260, 0, H, PAPER, 0.16, seed=17, rmax=2.4)
    grain(img, 0.006, 21)
    img = np.clip(img, 0, 1)

    full = Image.fromarray((img * 255).astype(np.uint8))
    full.save(os.path.join(OUT, f'cover_full_{setname}.png'), optimize=True)

    for i, (tag, order, reel, where) in enumerate(slots):
        piece = img[:, i * TW:(i + 1) * TW]
        # 커버는 9:16 이라 위아래를 늘린다. **가장자리 픽셀을 복제**해서
        # 이음매가 안 생기게 — 따로 그려 넣으면 그 선이 보인다
        cov = cv2.copyMakeBorder(piece, PAD, CH - TH - PAD, 0, 0,
                                 cv2.BORDER_REPLICATE)
        vignette(cov, 0.30, 2.2)
        fringe(cov, 0.0012)
        p = os.path.join(OUT, f'{order}_{tag}_{reel}.png')
        Image.fromarray((np.clip(cov, 0, 1) * 255).astype(np.uint8)).save(
            p, optimize=True)
        print(f'{p}   {where} 칸 · {reel}.mp4 커버 · {order}번째로 올림')

    print()
    print('올리는 순서 — **거꾸로다.** 격자는 최신이 왼쪽 위라 왼쪽 칸을 마지막에 올린다')
    for tag, order, reel, where in sorted(slots, key=lambda s: s[1]):
        print(f'  {order}) {reel}.mp4   커버 {order}_{tag}_{reel}.png   → {where} 칸')
    return OUT


if __name__ == '__main__':
    k = sys.argv[1] if sys.argv[1:] else 'cut'
    if k not in SETS:
        raise SystemExit(f'{k} 은 없는 세트입니다 — {", ".join(SETS)}')
    build(k)
