"""
**백투백 판 — 두 사람이 같이 선다.**

    python poster_b2b.py                     타임테이블에 있는 세트 전부
    python poster_b2b.py "HEIDY x CHIPS"     골라서

개인 판(`poster_dj8`)은 **같은 사람을 세 번** 세워 거리를 만듭니다. 백투백은
그 문법을 쓸 수 없습니다 — 사람이 둘인데 각자를 세 번 세우면 여섯 겹이
되고, 누가 누구인지가 사라집니다.

여기서는 **둘을 좌우에 세우고 가운데서 겹칩니다.** 겹치는 자리가 이 판의
주제입니다 — 두 사람이 한 부스에 같이 선다는 게 백투백이니까요.

    뒤       둘의 실루엣이 크게, 흐리게. 무대 뒤 그림자
    앞       각자 원래 크기·컬러. 오른쪽 사람이 앞으로 온다

이름은 한 덩어리로 씁니다. `HEIDY` 와 `CHIPS` 를 따로 크게 쓰면 개인 판
두 장을 붙인 것이 되고, 세트로 안 읽힙니다. **`×` 가 이름의 일부입니다.**

판은 검정·흰색·은색뿐이고 색은 사람에게만 있습니다(`poster_dj7` 규칙).
"""
import sys

import cv2
import numpy as np

from poster_kit import (BRAND, tmask, paint, rule, glow, outline, grain, save,
                        sign, bloom, logo)
from poster_crew import crop_head, rimlight
from poster_dj3 import chrome
from poster_dj4 import fringe, sharpen, melt, nebula
from poster_dj7 import PAPER, SILVER, STEEL, DIM, SLOGAN
from fest_kit import justify, night, vignette, rays, specks, haze
from fonts import KR, KRB
from members import get
import event as EV

SIZES = {'feed': (1080, 1350), 'sq': (1080, 1080), 'story': (1080, 1920)}

# (중심 x 비율, 세로 위치, 앞에 오는지) — 왼쪽 · 오른쪽.
# **완전히 좌우로 갈라 놓으면 두 장을 나란히 붙인 판이 된다.** 0.5 쪽으로
# 당겨 겹치게 해야 '같이 선다' 가 그림으로 보인다.
SIDES = [(0.315, 0.150, False), (0.675, 0.128, True)]


def figure(img, name, W, H, V, cx, ytop, base_h, front):
    """한 사람. 뒤 그림자를 먼저 깔고 그 위에 본체를 얹는다."""
    fw = int(W * 0.74)
    fig = crop_head(name, fw, base_h)
    x0 = int(cx * W - fw / 2)
    top = int(H * ytop)

    # 판 밖으로 나가는 만큼 잘라 낸다
    sx0, sx1 = max(0, x0), min(W, x0 + fw)
    sy1 = min(H, top + base_h)
    if sx1 <= sx0 or sy1 <= top:
        return
    a_ = np.clip((fig[:sy1 - top, sx0 - x0:sx1 - x0, 3].copy() - 0.045) / 0.955, 0, 1)
    px = np.clip(fig[:sy1 - top, sx0 - x0:sx1 - x0, :3], 0, 1).copy()
    px = sharpen(px, 2.4 * V, 0.62)
    a_, px = melt(a_, px, 0.34, len(name) * 37 + int(front) * 11, V)

    sl = (slice(top, sy1), slice(sx0, sx1))
    # 뒤쪽 사람은 조금 죽인다. 둘이 같은 밝기면 앞뒤가 안 생겨 납작해진다
    dim = 1.0 if front else 0.82
    back = cv2.GaussianBlur(a_, (0, 0), 24 * V)
    img[sl] *= (1 - back[..., None] * (0.62 if front else 0.50))
    img[sl] += rimlight(a_, V)[..., None] * PAPER * (0.52 if front else 0.40)
    img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None] * dim


def build(pair, W, H, safe=False):
    """`pair` 는 `('HEIDY', 'CHIPS')`."""
    V = W / 1080.0
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    M = int(W * 0.068)
    label = EV.B2B.join(pair)

    img = np.repeat(np.repeat(np.float32([0.015, 0.015, 0.020])[None, None, :],
                              H, 0), W, 1).copy()
    # 빛을 하나만 두면 둘 중 하나가 어둠에 남는다 — 사람마다 하나씩
    for (cx, _, _), seed in zip(SIDES, (17, 43)):
        img += nebula(W, H, W * cx, H * 0.36, STEEL * 1.5, SILVER, seed=seed,
                      spread=0.80 if safe else 0.66) * 0.72
    rays(img, W * 0.50, H * 0.34, 30, int(26 * V), int(H * 0.72), PAPER, 0.032,
         phase=0.13, duty=0.26)
    haze(img, int(H * 0.30), int(H * 0.94), SILVER, 0.060, seed=29)

    base_h = int(H * 0.560)

    # 뒤 그림자 — 둘을 한 덩어리로 크게. 무대 뒤에 선 실루엣이다
    for cx, ytop, _ in SIDES:
        fw = int(W * 0.96)
        fig = crop_head(pair[0] if cx < 0.5 else pair[1], fw, int(base_h * 1.34))
        x0 = int(cx * W - fw / 2 + (-1 if cx < 0.5 else 1) * W * 0.06)
        top = int(H * (ytop - 0.055))
        sx0, sx1 = max(0, x0), min(W, x0 + fw)
        sy0, sy1 = max(0, top), min(H, top + int(base_h * 1.34))
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        a_ = np.clip(fig[sy0 - top:sy1 - top, sx0 - x0:sx1 - x0, 3], 0, 1)
        a_ = cv2.GaussianBlur(a_, (0, 0), 11.0 * V)
        img[sy0:sy1, sx0:sx1] += a_[..., None] * SILVER * 0.085

    for who, (cx, ytop, front) in zip(pair, SIDES):
        if not front:
            figure(img, who, W, H, V, cx, ytop, base_h, front)

    # ── 이름 (앞 사람 뒤) ────────────────────────────────
    ny = H * 0.690
    ns = justify(label, W * 0.90, 0.01, cap=int(150 * V))
    nm = tmask(label, BRAND, ns, 0.01)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.030)),) * 2))
    sh = cv2.GaussianBlur(nm.astype(np.float32) / 255.0, (0, 0), 13 * V)
    paint(img, (sh * 255).astype(np.uint8), W / 2, ny + 10 * V,
          color=np.float32([0, 0, 0]), a=0.72, anchor='c')
    glow(img, nm, W / 2, ny, SILVER, 0.28, int(26 * V), anchor='c')
    chrome(img, nm, W / 2, ny, PAPER, STEEL)

    for who, (cx, ytop, front) in zip(pair, SIDES):
        if front:
            figure(img, who, W, H, V, cx, ytop, base_h, front)

    paint(img, tmask(label, BRAND, ns, 0.01), W / 2, ny, color=PAPER, a=0.46,
          anchor='c')
    paint(img, outline(nm, max(2, int(3.4 * V))), W / 2, ny, color=PAPER,
          a=0.94, anchor='c')

    # ── 브랜드 ───────────────────────────────────────────
    slot = next(((s, e) for s, e, n in EV.B2B_SETS if n == label), None)
    lg = logo(int(46 * V))
    paint(img, lg, W / 2 - lg.shape[1] / 2, y0 + 52 * V, color=PAPER, a=0.95)
    paint(img, tmask(f'{slot[0]} — {slot[1]}' if slot else 'BACK TO BACK',
                     BRAND, int(20 * V), 0.22), W - M, y0 + 52 * V,
          color=PAPER, a=0.90, anchor='r')
    paint(img, tmask(EV.HANDLE, BRAND, int(13 * V), 0.24), M, y0 + 52 * V,
          color=DIM, a=0.85, anchor='l')

    yb = y1 - 30 * V
    paint(img, tmask(SLOGAN, BRAND, int(13 * V), 0.30), W / 2, yb, color=DIM,
          a=0.62, anchor='c')
    yb -= 40 * V
    paint(img, tmask(f'{EV.DATE_EN}   ·   {EV.VENUE}   ·   {EV.ADDR}',
                     KR, int(16 * V), 0.02), W / 2, yb, color=DIM, a=0.92,
          anchor='c')
    yb -= 44 * V
    em = tmask(EV.NAME, BRAND, int(34 * V), 0.16)
    paint(img, em, W / 2, yb, color=PAPER, anchor='c')
    rule(img, yb + 34 * V, W / 2 - em.shape[1] * 0.60, W / 2 + em.shape[1] * 0.60,
         SILVER, 0.55, max(1, int(2 * V)))
    yb -= 42 * V
    # 개인 판은 장르를 적지만 여기는 **둘이 같이 튼다는 것**이 정보다
    gs = []
    for who in pair:
        gs += [g for g in get(who)['genres']['ko'][:2] if g not in gs]
    igs = '   ·   '.join('@' + get(w)['instagram'] for w in pair
                         if get(w)['instagram'])
    paint(img, tmask('  /  '.join(gs[:4]) + ('     ·     ' + igs if igs else ''),
                     KR, int(16 * V), 0.02), W / 2, yb, color=PAPER, a=0.76,
          anchor='c')
    yb -= 36 * V
    paint(img, tmask('BACK TO BACK  ·  한 부스에 둘', KRB, int(27 * V), 0.01),
          W / 2, yb, color=PAPER, anchor='c')

    if safe:
        gy = np.arange(H, dtype=np.float32)
        gx = np.arange(W, dtype=np.float32)
        spill = (np.exp(-((gy - H * 0.955) / (H * 0.075)) ** 2)[:, None]
                 * np.exp(-((gx - W * 0.5) / (W * 0.60)) ** 2)[None, :])
        img += spill[..., None] * SILVER * 0.20
        rule(img, int(y1), 0, W, SILVER, 0.42, max(1, int(2 * V)))

    specks(img, 140, 0, int(y1), PAPER, 0.18, seed=53, rmax=2.6)
    bloom(img, 0.80, 18 * V, 0.22, PAPER)
    fringe(img, 0.0016)
    vignette(img, 0.50, 2.0)
    grain(img, 0.006, 37)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    sets = {n: tuple(n.split(EV.B2B)) for _, _, n in EV.B2B_SETS}
    if sys.argv[1:]:
        want = {}
        for a in sys.argv[1:]:
            key = EV.B2B.join(p.strip().upper() for p in a.replace('×', 'x').split('x'))
            if key not in sets:
                raise SystemExit(f'{key} 은 타임테이블에 없는 세트입니다 — '
                                 f'{" / ".join(sets)}')
            want[key] = sets[key]
    else:
        want = sets

    for label, pair in want.items():
        key = label.replace(EV.B2B, '_').lower()
        for k, (w, h) in SIZES.items():
            im = build(pair, w, h, safe=(k == 'story'))
            night(im, f'b2b_{key}_{k}')
            save(im, f'b2b_{key}_{k}')
