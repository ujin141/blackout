"""
**DJ 한 명짜리 판 — H안.** 같은 사람을 세 번 세운다.

    python poster_dj8.py                 일곱 명 전부
    python poster_dj8.py lynn chips      골라서

A~G안은 전부 **사람이 한 명**입니다. 한 장 얹고 그 뒤를 꾸미는 구조라,
꾸미는 걸 아무리 늘려도 결국 인물 사진 한 장 위의 장식입니다.

여기서는 **같은 사람을 크기를 달리해 세 번** 세웁니다.

    뒤       제일 크게. 거의 안 보일 만큼 어둡고 흐리게
    가운데   중간 크기. 은색 실루엣에 가깝게
    앞       원래 크기. 실사 컬러 그대로 — **색이 있는 건 이 한 겹뿐이다**

크기가 셋이면 거리가 셋이고, 거리가 생기면 판이 공간이 됩니다. 그리고
셋 다 같은 사람이라 **누구인지가 세 번 반복됩니다** — 얼굴이 남습니다.

G안과 같은 규칙을 지킵니다. 판은 검정·흰색·은색뿐이고 색은 사람에게만
있습니다(브랜드 기본이 흑백입니다).
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, tmask, paint, rule, box, glow, outline, grain,
                        save, sign, bloom, logo)
from poster_crew import crop_head
from fest_kit import justify, night, vignette, rays, specks, haze
from poster_dj import HUE, LINE
from poster_dj3 import chrome
from poster_dj4 import fringe, sharpen, melt, nebula
from poster_dj7 import SLOGAN, PAPER, SILVER, STEEL, DIM
from fonts import KR, KRB
from members import get
import event as EV

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}
SIZES = {'sq': (1080, 1080), 'story': (1080, 1920)}

# (높이 배수, 세로 위치, 가로 밀기, 흐림, 밝기, 색을 남길지) — 뒤에서 앞으로.
# **뒤로 갈수록 크고 어둡고 흐리다.** 하나라도 어기면 거리가 안 생긴다.
#
# 처음엔 셋을 전부 가운데 세웠는데, 앞 겹이 뒤를 통째로 가려서 **세 번
# 세운 게 안 보이고 후광처럼만** 보였다. 좌우로 밀어야 계단이 생긴다.
ECHO = [
    (1.40, 0.040, -0.115, 10.0, 0.44, False),
    (1.16, 0.078, +0.070, 3.5, 0.64, False),
    (1.00, 0.120, 0.000, 0.0, 1.00, True),
]


def layer(img, name, W, H, V, mult, ytop, dx, blur, bright, keep_color, base_h):
    """인물 한 겹. 돌려주는 값은 그 겹의 알파(맨 앞 겹만 쓴다)."""
    h = int(base_h * mult)
    fig = crop_head(name, int(W * mult), h)
    # 가운데를 맞춘다 — 배수를 키우면 좌우로 넘치므로 가운데만 잘라 온다
    x0 = int((fig.shape[1] - W) / 2 - dx * W)
    fig = fig[:, max(0, x0):max(0, x0) + W]
    if fig.shape[1] < W:
        fig = np.pad(fig, ((0, 0), (0, W - fig.shape[1]), (0, 0)))
    top = int(H * ytop)
    n = min(H, top + h) - top
    if n <= 0:
        return None, None, None
    a_ = np.clip((fig[:n, ..., 3].copy() - 0.07) / 0.93, 0, 1)
    px = np.clip(fig[:n, ..., :3], 0, 1).copy()
    if keep_color:
        px = sharpen(px, 2.4 * V, 0.62)
    else:
        g = (px[..., 0] * .299 + px[..., 1] * .587 + px[..., 2] * .114)[..., None]
        px = np.repeat(g, 3, 2) * SILVER * 1.25
    a_, px = melt(a_, px, 0.34, len(name) * 31 + int(mult * 100), V)
    if blur > 0:
        a_ = cv2.GaussianBlur(a_, (0, 0), blur * V)
        px = cv2.GaussianBlur(px, (0, 0), blur * V)
    px = px * bright
    sl = (slice(top, top + n), slice(0, W))
    return sl, a_, px


def build(name, W, H, safe=False):
    V = W / 1080.0
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    M = int(W * 0.068)

    img = np.repeat(np.repeat(np.float32([0.015, 0.015, 0.020])[None, None, :],
                              H, 0), W, 1).copy()

    cx, cy = W * 0.50, H * 0.400
    img += nebula(W, H, cx, cy, STEEL * 1.5, SILVER, seed=len(name) * 29 + 4,
                  spread=0.96 if safe else 0.74)
    rays(img, cx, cy, 30, int(26 * V), int(H * 0.76), PAPER, 0.038,
         phase=0.13, duty=0.26)
    haze(img, int(H * 0.26), int(H * 0.94), SILVER, 0.065, seed=len(name) * 3 + 9)

    base_h = int(H * 0.585)

    # ── 뒤 두 겹 ─────────────────────────────────────────
    for mult, ytop, dx, blur, bright, keep in ECHO[:-1]:
        sl, a_, px = layer(img, name, W, H, V, mult, ytop, dx, blur, bright, keep, base_h)
        if sl is None:
            continue
        img[sl] = img[sl] * (1 - a_[..., None] * 0.85) + px * a_[..., None] * 0.85

    # ── 이름 (앞 겹 뒤) ──────────────────────────────────
    ny = H * 0.660
    ns = justify(name, W * 0.88, 0.01, cap=int(220 * V))
    nm = tmask(name, BRAND, ns, 0.01)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.028)),) * 2))
    sh = cv2.GaussianBlur(nm.astype(np.float32) / 255.0, (0, 0), 13 * V)
    paint(img, (sh * 255).astype(np.uint8), W / 2, ny + 10 * V,
          color=np.float32([0, 0, 0]), a=0.70, anchor='c')
    glow(img, nm, W / 2, ny, SILVER, 0.28, int(26 * V), anchor='c')
    chrome(img, nm, W / 2, ny, PAPER, STEEL)

    # ── 앞 겹 ────────────────────────────────────────────
    mult, ytop, dx, blur, bright, keep = ECHO[-1]
    sl, a_, px = layer(img, name, W, H, V, mult, ytop, dx, blur, bright, keep, base_h)
    if sl is not None:
        back = cv2.GaussianBlur(a_, (0, 0), 24 * V)
        img[sl] *= (1 - back[..., None] * 0.62)
        k = np.ones((max(3, int(7 * V)),) * 2, np.uint8)
        edge = cv2.GaussianBlur(np.clip(cv2.dilate(a_, k) - a_, 0, 1), (0, 0), 7 * V)
        img[sl] += (edge / max(edge.max(), 1e-6))[..., None] * PAPER * 0.70
        img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None]

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

    specks(img, 140, 0, int(y1), PAPER, 0.18, seed=len(name) * 13 + 7, rmax=2.6)
    bloom(img, 0.80, 18 * V, 0.22, PAPER)
    fringe(img, 0.0016)
    vignette(img, 0.50, 2.0)
    grain(img, 0.006, 29)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        for k, (w, h) in SIZES.items():
            im = build(name, w, h, safe=(k == 'story'))
            night(im, f'dj8_{key}_{k}')
            save(im, f'dj8_{key}_{k}')
