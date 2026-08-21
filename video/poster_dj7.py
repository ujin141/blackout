"""
**DJ 한 명짜리 판 — G안.** 판은 흑백, 사람만 컬러.

    python poster_dj7.py                 일곱 명 전부
    python poster_dj7.py lynn chips      골라서

A~F안은 사람마다 색을 하나씩 줬습니다. 화려하지만 **우리 판으로는 안 보입니다** —
BLACKOUT 자산은 흑백이 기본이고, 일곱 색이 걸리면 크루가 아니라 색 모음이
됩니다.

여기서는 색을 **딱 한 군데만** 씁니다. 사람입니다.

    판          검정 · 흰색 · 은색뿐. 브랜드 그대로
    사람        실사 컬러 그대로. 판에서 유일하게 색이 있는 것
    화려함      색이 아니라 **질감**으로 만든다 — 크롬 · 유리 · 반사 · 광선

색이 하나뿐이면 그 하나가 강해집니다. 판 전체가 무채색인데 사람만 컬러라
**눈이 갈 데가 사람밖에 없습니다.** 색을 일곱 개 뿌린 판보다 이쪽이 셉니다.

일곱 장이 나란히 걸려도 한 크루로 보입니다 — 구분은 색이 아니라 얼굴이
합니다.
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, tmask, paint, rule, box, glow, outline, grain,
                        save, sign, bloom, logo)
from poster_crew import crop_head, rimlight
from fest_kit import justify, night, vignette, rays, specks, haze, torus
from poster_dj import HUE, LINE
from poster_dj3 import chrome
from poster_dj4 import fringe, sharpen, melt, debris, nebula
from fonts import KR, KRB
from members import get
import event as EV

PAPER  = np.float32([0.98, 0.98, 0.97])
SILVER = np.float32([0.72, 0.75, 0.82])          # 은색 — 살짝 푸른 회색
STEEL  = np.float32([0.24, 0.26, 0.32])
DIM    = np.float32([0.58, 0.60, 0.65])

# 판에 들어가는 유일한 카피. **crew.py 처럼 맨 위 상수로 둔다**
SLOGAN = 'WHERE THE LIGHTS FADE,  THE MUSIC TAKES OVER.'

ORDER = EV.LINEUP
SET_AT = EV.SLOTS                  # 병행 슬롯까지 들어 있다
SIZES = {'sq': (1080, 1080), 'story': (1080, 1920)}


def build(name, W, H, safe=False):
    V = W / 1080.0
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    M = int(W * 0.068)

    img = np.repeat(np.repeat(np.float32([0.016, 0.016, 0.021])[None, None, :],
                              H, 0), W, 1).copy()

    # ── 배경 ─────────────────────────────────────────────
    # 색이 없으니 **밝기와 결로만** 공간을 만든다
    cx, cy = W * 0.50, H * 0.395
    img += nebula(W, H, cx, cy, STEEL * 1.6, SILVER, seed=len(name) * 19 + 8,
                  spread=0.96 if safe else 0.74)
    rays(img, cx, cy, 34, int(26 * V), int(H * 0.78), PAPER, 0.040,
         phase=0.09, duty=0.28)
    torus(img, cx, cy + H * 0.02, H * 0.245, max(2, int(3 * V)), SILVER, 0.55,
          glow=22 * V)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - cx) / (W * 0.34)) ** 2
                    + ((yy - cy) / (H * 0.22)) ** 2))[..., None] * SILVER * 0.14
    debris(img, 34, cx, cy, SILVER, len(name) * 13 + 2, 9 * V, 42 * V)
    haze(img, int(H * 0.28), int(H * 0.94), SILVER, 0.070, seed=len(name) * 7 + 3)

    # ── 이름 (인물 뒤) ───────────────────────────────────
    ny = H * 0.640
    ns = justify(name, W * 0.88, 0.01, cap=int(225 * V))
    nm = tmask(name, BRAND, ns, 0.01)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.028)),) * 2))
    sh = cv2.GaussianBlur(nm.astype(np.float32) / 255.0, (0, 0), 13 * V)
    paint(img, (sh * 255).astype(np.uint8), W / 2, ny + 10 * V,
          color=np.float32([0, 0, 0]), a=0.66, anchor='c')
    glow(img, nm, W / 2, ny, SILVER, 0.30, int(28 * V), anchor='c')
    chrome(img, nm, W / 2, ny, PAPER, STEEL)

    # ── 사람 ─────────────────────────────────────────────
    hero_h = int(H * 0.658)
    top = int(H * 0.115)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = np.clip((al[:n].copy() - 0.045) / 0.955, 0, 1)
    px = sharpen(np.clip(fig[..., :3], 0, 1), 2.4 * V, 0.62)[:n].copy()
    a_, px = melt(a_, px, 0.34, len(name) * 31 + 2, V)

    # 뒤 그림자 — 배경이 은색이라 이게 없으면 사람이 배경에 붙는다
    back = cv2.GaussianBlur(a_, (0, 0), 26 * V)
    img[sl] *= (1 - back[..., None] * 0.72)

    # 테두리 빛도 흰색 하나. **여기에 색을 넣으면 규칙이 깨진다**
    edge = rimlight(a_, V)          # 얇게, 위쪽은 죽인다 — poster_crew 참고
    img[sl] += edge[..., None] * PAPER * 0.54

    img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None]

    # 가린 구간도 읽히게 윤곽선 한 겹
    paint(img, nm, W / 2, ny, color=PAPER, a=0.50, anchor='c')
    paint(img, outline(nm, max(2, int(3.6 * V))), W / 2, ny, color=PAPER,
          a=0.94, anchor='c')

    # ── 브랜드 ───────────────────────────────────────────
    s, e = SET_AT[name]
    gs = get(name)['genres']['ko'][:3]
    ig = get(name)['instagram']

    lg = logo(int(46 * V))
    paint(img, lg, W / 2 - lg.shape[1] / 2, y0 + 52 * V, color=PAPER, a=0.95)
    paint(img, tmask(f'{s} — {e}', BRAND, int(20 * V), 0.22), W - M, y0 + 52 * V,
          color=PAPER, a=0.90, anchor='r')
    paint(img, tmask(EV.HANDLE, BRAND, int(13 * V), 0.24), M, y0 + 52 * V,
          color=DIM, a=0.85, anchor='l')

    yb = y1 - 30 * V
    paint(img, tmask(SLOGAN, BRAND, int(13 * V), 0.30), W / 2, yb, color=DIM,
          a=0.62, anchor='c')
    yb -= 40 * V
    paint(img, tmask(f'{EV.DATE_EN}   ·   {EV.VENUE}   ·   {EV.ADDR}', KR,
                     int(16 * V), 0.02), W / 2, yb, color=DIM, a=0.92, anchor='c')
    yb -= 44 * V
    em = tmask(EV.NAME, BRAND, int(34 * V), 0.16)
    paint(img, em, W / 2, yb, color=PAPER, anchor='c')
    rule(img, yb + 34 * V, W / 2 - em.shape[1] * 0.60, W / 2 + em.shape[1] * 0.60,
         SILVER, 0.55, max(1, int(2 * V)))
    yb -= 42 * V
    bits = [b for b in ('  /  '.join(gs), '@' + ig if ig else '') if b]
    paint(img, tmask('     ·     '.join(bits), KR, int(17 * V), 0.02), W / 2, yb,
          color=PAPER, a=0.76, anchor='c')
    yb -= 36 * V
    paint(img, tmask(LINE[name], KRB, int(29 * V), 0.01), W / 2, yb, color=PAPER,
          anchor='c')

    specks(img, 150, 0, int(y1), PAPER, 0.20, seed=len(name) * 11 + 6, rmax=2.8)
    bloom(img, 0.80, 18 * V, 0.24, PAPER)
    fringe(img, 0.0016)
    vignette(img, 0.48, 2.0)
    grain(img, 0.006, 23)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        for k, (w, h) in SIZES.items():
            im = build(name, w, h, safe=(k == 'story'))
            night(im, f'dj7_{key}_{k}')
            save(im, f'dj7_{key}_{k}')
