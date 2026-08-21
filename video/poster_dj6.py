"""
**DJ 한 명짜리 판 — F안.** 네온 간판.

    python poster_dj6.py                 일곱 명 전부
    python poster_dj6.py lynn chips      골라서

A~E안은 전부 **빛이 뒤에서 옵니다** — 성운이든 해든 빔이든 인물 뒤에 광원이
있고 인물은 그 앞에 섭니다. 이 판은 반대입니다. **빛이 벽에 붙어 있습니다.**

    벽            콘크리트 한 면. 배경이 아니라 진짜 벽이라야 간판이 걸린다
    네온 이름     속이 빈 튜브. 채우면 글자고, 비워야 유리관이다
    벽 번짐       튜브에서 나온 빛이 벽에 번진다. **이게 없으면 스티커다**
    바닥 반사     간판 아래 젖은 바닥. 클럽 앞 골목이 된다

인물은 벽 앞에 서서 그 빛을 받습니다 — 실사 그대로 얹고, 네온 색은
테두리에만 줍니다(D·E안과 같은 규칙).
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, tmask, paint, rule, box, glow, outline, grain,
                        save, sign, bloom)
from poster_crew import crop_head
from fest_kit import justify, night, vignette, specks, haze
from poster_dj import HUE, LINE
from poster_dj2 import MATE
from poster_dj4 import fringe, sharpen, melt
from fonts import KR, KRB
from members import get
import event as EV

PAPER = np.float32([0.98, 0.98, 0.97])
DIM   = np.float32([0.58, 0.60, 0.64])

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}
SIZES = {'sq': (1080, 1080), 'story': (1080, 1920)}


def concrete(W, H, seed):
    """콘크리트 벽. **얼룩이 있어야 벽이다** — 고른 회색은 그냥 배경이다."""
    rng = np.random.default_rng(seed)
    def octave(s, sig, amt):
        n = rng.standard_normal((max(2, int(H * s)), max(2, int(W * s)))).astype(np.float32)
        return cv2.GaussianBlur(cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC),
                                (0, 0), sig) * amt
    f = octave(0.02, W * 0.03, 1.0) + octave(0.10, W * 0.006, 0.45) \
        + octave(0.45, 1.4, 0.10)
    f = (f - f.min()) / (f.max() - f.min() + 1e-6)
    base = 0.052 + f * 0.048
    # 위에서 아래로 조금 어두워진다 — 천장 조명이 있는 방으로 읽힌다
    g = np.linspace(1.12, 0.66, H, dtype=np.float32)[:, None]
    img = (base * g)[..., None] * np.float32([1.0, 0.99, 1.04])
    return img


def neon(img, m, x, y, core, halo, V, anchor='c', a=1.0):
    """네온 한 줄. **속을 비운다** — 채우면 글자고, 비워야 유리관이다.

    후광은 두 겹이다. 넓고 옅은 겹이 벽을 물들이고, 좁고 진한 겹이
    관 바로 옆에서 탄다 — 한 겹만 쓰면 흐릿한 글자로 보인다."""
    tube = outline(m, max(2, int(4.5 * V)))
    glow(img, tube, x, y, halo, 0.85 * a, int(40 * V), anchor=anchor)
    glow(img, tube, x, y, halo, 0.70 * a, int(15 * V), anchor=anchor)
    paint(img, tube, x, y, color=core, a=a, anchor=anchor)
    return tube


def build(name, W, H, safe=False):
    V = W / 1080.0
    C, C2 = HUE[name], MATE[name]
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    M = int(W * 0.075)

    img = concrete(W, H, seed=len(name) * 23 + 7)

    # ── 네온 이름 ────────────────────────────────────────
    ny = H * (0.470 if safe else 0.430)
    ns = justify(name, W * 0.80, 0.04, cap=int(215 * V))
    nm = tmask(name, BRAND, ns, 0.04)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.020)),) * 2))
    # 벽 번짐을 먼저 넓게 깐다 — 간판이 벽에 붙어 있다는 유일한 증거다
    glow(img, nm, W / 2, ny, C, 0.30, int(120 * V), anchor='c')
    tube = neon(img, nm, W / 2, ny, C * 0.28 + PAPER * 0.72, C, V)

    # 이름 위 작은 네온 한 줄
    km = tmask('BLACKOUT CREW', BRAND, int(21 * V), 0.44)
    neon(img, km, W / 2, ny - ns * 0.72, C2 * 0.30 + PAPER * 0.70, C2, V, a=0.85)

    haze(img, int(H * 0.18), int(H * 0.95), C * 0.7 + PAPER * 0.3, 0.055,
         seed=len(name) * 3 + 1)

    # ── 사람 ─────────────────────────────────────────────
    hero_h = int(H * 0.640)
    top = int(H * 0.138)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = np.clip((al[:n].copy() - 0.07) / 0.93, 0, 1)
    px = sharpen(np.clip(fig[..., :3], 0, 1), 2.4 * V, 0.60)[:n].copy()
    a_, px = melt(a_, px, 0.36, len(name) * 31 + 2, V)

    # 인물이 벽에 드리우는 그림자. 간판 빛이 앞에서 오니 그림자는 뒤에 진다
    sh = cv2.GaussianBlur(a_, (0, 0), 30 * V)
    img[sl] *= (1 - sh[..., None] * 0.55)

    k = np.ones((max(3, int(7 * V)),) * 2, np.uint8)
    edge = cv2.GaussianBlur(np.clip(cv2.dilate(a_, k) - a_, 0, 1), (0, 0), 7 * V)
    edge = edge / max(edge.max(), 1e-6)
    lr = np.linspace(0, 1, W, dtype=np.float32)[None, :, None] ** 0.8
    two = C2[None, None, :] * (1 - lr) + C[None, None, :] * lr
    img[sl] += edge[..., None] * (two * 0.80 + PAPER * 0.20) * 0.78

    img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None]

    # 관이 사람 앞을 지나가는 것으로 보이게 한 겹 더. 0.30 으로 뒀더니
    # **사람에 가린 구간이 흐려서 이름이 안 읽혔다** — 네온은 원래 가는 선이라
    # 여기서 아끼면 가운데가 통째로 사라진다
    paint(img, tube, W / 2, ny, color=C * 0.18 + PAPER * 0.82, a=0.62, anchor='c')
    glow(img, tube, W / 2, ny, C, 0.45, int(16 * V), anchor='c')

    # ── 젖은 바닥 ────────────────────────────────────────
    fl = int(H * (0.760 if safe else 0.785))
    strip = img[max(0, fl - int(H * 0.30)):fl][::-1].copy()
    if strip.shape[0] > 8:
        strip = cv2.GaussianBlur(strip, (0, 0), 11 * V)
        # 세로로 흔들어 물결처럼
        yy = np.arange(strip.shape[0], dtype=np.float32)
        off = (np.sin(yy / (11 * V)) * 5 * V).astype(np.int32)
        for i, o in enumerate(off):
            strip[i] = np.roll(strip[i], int(o), axis=0)
        t = np.linspace(1, 0, strip.shape[0], dtype=np.float32)[:, None, None] ** 1.5
        rr = min(H, fl + strip.shape[0]) - fl
        if rr > 0:
            img[fl:fl + rr] = img[fl:fl + rr] * (1 - t[:rr] * 0.42) + strip[:rr] * t[:rr] * 0.42
    rule(img, fl, 0, W, C, 0.22, max(1, int(2 * V)))

    # ── 글 ───────────────────────────────────────────────
    s, e = SET_AT[name]
    gs = get(name)['genres']['ko'][:3]
    ig = get(name)['instagram']

    sign(img, M, y0 + 44 * V, size=int(13 * V), color=PAPER, a=0.80, anchor='l')
    paint(img, tmask(f'{s} — {e}', BRAND, int(21 * V), 0.22), W - M, y0 + 44 * V,
          color=PAPER, a=0.88, anchor='r')

    yb = y1 - 32 * V
    paint(img, tmask(f'{EV.DATE_EN}   ·   {EV.VENUE}   ·   {EV.ADDR}', KR,
                     int(16 * V), 0.02), W / 2, yb, color=DIM, a=0.92, anchor='c')
    yb -= 44 * V
    paint(img, tmask(EV.NAME, BRAND, int(33 * V), 0.16), W / 2, yb, color=PAPER,
          anchor='c')
    yb -= 42 * V
    bits = [b for b in ('  /  '.join(gs), '@' + ig if ig else '') if b]
    paint(img, tmask('     ·     '.join(bits), KR, int(17 * V), 0.02), W / 2, yb,
          color=PAPER, a=0.76, anchor='c')
    yb -= 36 * V
    paint(img, tmask(LINE[name], KRB, int(28 * V), 0.01), W / 2, yb, color=PAPER,
          anchor='c')

    specks(img, 90, 0, int(y1), PAPER, 0.14, seed=len(name) * 7 + 5, rmax=2.2)
    bloom(img, 0.78, 20 * V, 0.26, PAPER)
    fringe(img, 0.0015)
    vignette(img, 0.50, 1.9)
    grain(img, 0.007, 19)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        for k, (w, h) in SIZES.items():
            im = build(name, w, h, safe=(k == 'story'))
            night(im, f'dj6_{key}_{k}')
            save(im, f'dj6_{key}_{k}')
