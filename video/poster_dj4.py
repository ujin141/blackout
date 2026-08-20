"""
**DJ 한 명짜리 판 — D안.** 우진이 준 레퍼런스(월디페 ANYMA 판) 문법.

    python poster_dj4.py                 일곱 명 전부
    python poster_dj4.py lynn chips      골라서

레퍼런스 세 장(WDJF ANYMA · CLUB LIVEN × DUO · SUNDAY NIGHT)에서 공통으로
지키고 있는 것만 뽑았습니다. 우리 A·B·C안이 셋 다 안 하고 있던 것들입니다.

    정사각          1:1. 클럽·페스티벌 게스트 판은 세로가 아니라 정사각이다
    폭발 배경       인물 뒤가 비어 있지 않다. 성운 · 파편 · 방사형 빛으로 꽉 찬다
    이름은 가슴께   판 가운데가 아니라 인물 가슴 위에 얹는다. 얼굴을 안 가린다
    흰 정보 띠      아래를 흰 띠로 끊고 그 안에 행사·장소·날짜를 칸으로 나눈다
    잔글씨 줄       맨 아래 한 줄 — 연령 고지 · 계정. 이게 있어야 진짜 판으로 보인다

C안(`poster_dj3.py`)의 크롬 이름은 여기서 안 씁니다. 레퍼런스는 전부
**그냥 굵은 흰 글자**입니다 — 배경이 화려할수록 글자는 단순해야 읽힙니다.

## 배경을 코드로 만든다

성운은 노이즈 두 겹을 다른 크기로 흐려 겹치고, 가운데에서 멀어질수록
꺼뜨립니다. 파편은 다각형을 뿌리되 **가까운 것일수록 크고 흐리게** 합니다 —
크기만 다르고 초점이 같으면 벽지가 되고 공간이 안 됩니다.
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, tmask, paint, fit, rule, box, glow, grain,
                        save, sign, bloom)
from poster_crew import crop_head
from fest_kit import justify, night, vignette, rays, specks
from fonts import KR, KRB
from members import get
from poster_dj import HUE, LINE
from poster_dj2 import MATE
import event as EV

PAPER = np.float32([0.98, 0.98, 0.97])
INK   = np.float32([0.045, 0.045, 0.050])
DIM   = np.float32([0.62, 0.64, 0.68])

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}

SIZES = {'sq': (1080, 1080), 'story': (1080, 1920)}


def nebula(W, H, cx, cy, c1, c2, seed):
    """인물 뒤 성운. **노이즈 한 겹으로는 구름이 안 된다** — 큰 덩어리와
    잔결을 따로 만들어 겹쳐야 깊이가 생긴다."""
    rng = np.random.default_rng(seed)
    def layer(s, sig):
        n = rng.standard_normal((max(2, int(H * s)), max(2, int(W * s)))).astype(np.float32)
        n = cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)
        return cv2.GaussianBlur(n, (0, 0), sig)
    f = layer(0.045, W * 0.018) + layer(0.11, W * 0.007) * 0.55
    f = (f - f.min()) / (f.max() - f.min() + 1e-6)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - cx) / (W * 0.66)) ** 2 + ((yy - cy) / (H * 0.66)) ** 2)
    m = np.clip(1 - r, 0, 1) ** 1.5
    # **문턱을 높게 잡아야 구름이 된다.** 낮으면 판 전체가 뿌옇게 뜨고
    # 인물이 안개 속에 선 꼴이 된다 — 검은 데가 넓어야 밝은 데가 산다
    v = np.clip(f * 2.0 - 0.72, 0, 1) * m
    return v[..., None] * c1 * 0.70 + (v ** 2.0)[..., None] * c2 * 1.25


def debris(img, n, cx, cy, color, seed, rmin, rmax):
    """떠 있는 파편. **가까운 것일수록 크고 흐리다** — 크기만 다르고 초점이
    같으면 벽지가 되고 공간이 안 된다."""
    H, W = img.shape[:2]
    rng = np.random.default_rng(seed)
    for _ in range(n):
        ang = rng.uniform(0, 2 * np.pi)
        d = rng.uniform(0.16, 1.05)
        x = cx + np.cos(ang) * d * W * 0.62
        y = cy + np.sin(ang) * d * H * 0.58
        size = rng.uniform(rmin, rmax) * (0.35 + d * 1.5)
        k = rng.integers(5, 8)
        a = np.sort(rng.uniform(0, 2 * np.pi, k))
        pts = np.stack([x + np.cos(a) * size * rng.uniform(0.55, 1.0, k),
                        y + np.sin(a) * size * rng.uniform(0.55, 1.0, k)], 1).astype(np.int32)
        lay = np.zeros((H, W), np.float32)
        cv2.fillPoly(lay, [pts], 1.0)
        blur = max(0.8, size * (0.05 + d * 0.22))
        lay = cv2.GaussianBlur(lay, (0, 0), blur)
        img += lay[..., None] * color * rng.uniform(0.14, 0.42)


def chip(img, text, x, y, h, font, size, fg, bg, V, pad=None, track=0.10):
    """정보 띠 안의 칸 하나. 돌려주는 값은 오른쪽 끝 x."""
    m = tmask(text, font, size, track)
    pad = int(size * 0.85) if pad is None else pad
    w = m.shape[1] + pad * 2
    if bg is not None:
        box(img, x, y - h / 2, x + w, y + h / 2, bg)
    paint(img, m, x + pad, y, color=fg, anchor='l')
    return x + w


def build(name, W, H, safe=False):
    V = W / 1080.0
    C, C2 = HUE[name], MATE[name]
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    BH = y1 - y0
    M = int(W * 0.055)
    tall = H > W * 1.2                                 # 9:16 이면 인물을 더 키운다

    # 아래 두 띠는 판 크기와 상관없이 같은 두께다 — 잔글씨는 줄어들면 안 읽힌다
    fine_h = 40 * V
    bar_h = 92 * V
    bar_y = y1 - fine_h - bar_h / 2

    img = np.repeat(np.repeat(np.float32([0.014, 0.013, 0.020])[None, None, :],
                              H, 0), W, 1).copy()

    # ── 배경 ─────────────────────────────────────────────
    cx, cy = W * 0.50, y0 + BH * 0.36
    img += nebula(W, H, cx, cy, C2 * 0.55 + C * 0.45, C, seed=len(name) * 13 + 4)
    rays(img, cx, cy, 26, int(40 * V), int(BH * 0.80), C * 0.6 + PAPER * 0.4, 0.055,
         phase=0.11, duty=0.34)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - cx) / (W * 0.30)) ** 2
                    + ((yy - cy) / (BH * 0.20)) ** 2))[..., None] * (C * 0.7 + PAPER * 0.3) * 0.16
    debris(img, 34, cx, cy, PAPER * 0.40 + C * 0.60, len(name) * 7 + 1,
           9 * V, 44 * V)

    # ── 사람 ─────────────────────────────────────────────
    hero_h = int(BH * (0.815 if tall else 0.760))
    top = int(y0 + BH * 0.105)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = al[:n]

    # 인물 뒤 그림자 — 배경이 밝아서 이게 없으면 사람이 배경에 먹힌다
    back = cv2.GaussianBlur(a_, (0, 0), 26 * V)
    img[sl] *= (1 - back[..., None] * 0.74)

    k = np.ones((max(3, int(6 * V)),) * 2, np.uint8)
    edge = cv2.GaussianBlur(np.clip(cv2.dilate(a_, k) - a_, 0, 1), (0, 0), 5 * V)
    # 0.85 로 뒀더니 테두리가 또렷해서 오려 붙인 스티커로 보였다.
    # 빛은 번져야 빛이다
    edge = cv2.GaussianBlur(edge, (0, 0), 6 * V)
    img[sl] += (edge / max(edge.max(), 1e-6))[..., None] * (C * 0.5 + PAPER * 0.5) * 0.60

    g = (fig[..., 0] * .299 + fig[..., 1] * .587 + fig[..., 2] * .114)
    g = np.clip((g - 0.5) * 1.36 + 0.5, 0, 1)
    g = np.where(g > 0.74, 0.74 + (g - 0.74) * 0.46, g)[..., None]
    px = (np.repeat(g, 3, 2) * (1 - 0.14 * (1 - g)) + C * (1 - g) * 0.14) * 0.94
    img[sl] = img[sl] * (1 - a_[..., None]) + px[:n] * a_[..., None]

    # 발치를 흰 띠 바로 위에서 끊는다
    cut = int(bar_y - bar_h * 0.5 - 26 * V)
    fade = int(BH * 0.13)
    if cut - fade > 0:
        t = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None] ** 1.4
        img[cut - fade:cut] *= (1 - t * 0.96)
    img[cut:int(y1)] *= 0.42

    # ── 이름 ─────────────────────────────────────────────
    # **가슴께에 얹는다.** 판 가운데에 두면 얼굴을 가리고, 아래로 내리면
    # 흰 띠에 붙는다 — 레퍼런스는 전부 가슴 위다
    ny = y0 + BH * (0.650 if tall else 0.615)
    ns = justify(name, W * 0.80, 0.01, cap=int(190 * V))
    m = tmask(name, BRAND, ns, 0.01)
    m = cv2.dilate(m, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.026)),) * 2))
    # 글자 뒤 그림자. 배경이 화려해서 이게 없으면 흰 글자가 배경에 붙는다
    sh = cv2.GaussianBlur(m.astype(np.float32) / 255.0, (0, 0), 10 * V)
    paint(img, (sh * 255).astype(np.uint8), W / 2, ny + 8 * V,
          color=np.float32([0, 0, 0]), a=0.55, anchor='c')
    paint(img, m, W / 2, ny, color=PAPER, anchor='c')

    # ── 머리 ─────────────────────────────────────────────
    s, e = SET_AT[name]
    sign(img, M, y0 + 44 * V, size=int(13 * V), color=PAPER, a=0.92, anchor='l')
    paint(img, tmask(f'{s} — {e}', BRAND, int(20 * V), 0.20), W - M, y0 + 44 * V,
          color=PAPER, a=0.92, anchor='r')

    # ── 흰 정보 띠 ───────────────────────────────────────
    box(img, 0, bar_y - bar_h / 2, W, bar_y + bar_h / 2, PAPER)
    x = M
    x = chip(img, EV.NAME, x, bar_y, bar_h, BRAND, int(31 * V), INK, None, V,
             pad=int(6 * V), track=0.13)
    x += 22 * V
    x = chip(img, '양재', x, bar_y, bar_h * 0.62, KRB, int(24 * V), PAPER, INK, V)
    x += 14 * V
    x = chip(img, EV.VENUE, x, bar_y, bar_h, KR, int(21 * V), INK * 3.2, None, V,
             pad=int(8 * V), track=0.02)
    # 날짜는 오른쪽 끝에 색 박스로. **판에서 두 번째로 큰 정보가 날짜다**
    dm = tmask('8/29 SAT', BRAND, int(28 * V), 0.10)
    dw = dm.shape[1] + 40 * V
    box(img, W - M - dw, bar_y - bar_h * 0.34, W - M, bar_y + bar_h * 0.34, C * 0.85)
    paint(img, dm, W - M - dw / 2, bar_y, color=PAPER, anchor='c')

    # ── 잔글씨 줄 ────────────────────────────────────────
    fy = y1 - fine_h / 2
    box(img, 0, y1 - fine_h, W, y1, INK * 0.5)
    left = f'19+  {EV.AGE}'
    paint(img, tmask(left, KR, int(15 * V), 0.02), M, fy, color=DIM, a=0.92, anchor='l')
    paint(img, tmask(f'{EV.ENTRY}   ·   {EV.HANDLE}', KR, int(15 * V), 0.02),
          W - M, fy, color=DIM, a=0.92, anchor='r')

    # ── 곁들이 ───────────────────────────────────────────
    gs = get(name)['genres']['ko'][:3]
    ig = get(name)['instagram']
    # **이름 바로 밑에 붙인다.** 아래로 내리면 인물 발치가 어두워지는
    # 구간에 들어가서, 흰 글자인데도 회색으로 읽힌다
    sy = ny + ns * 0.56
    paint(img, tmask(LINE[name], KRB, int(29 * V), 0.01), W / 2, sy, color=PAPER,
          anchor='c')
    bits = [b for b in ('  /  '.join(gs), '@' + ig if ig else '') if b]
    if bits:
        paint(img, tmask('     ·     '.join(bits), KR, int(18 * V), 0.02), W / 2,
              sy + 36 * V, color=PAPER, a=0.84, anchor='c')

    if safe:
        # **검게 잘라내지 않는다.** 그냥 0 으로 만들었더니 위아래에 까만 띠가
        # 남아서 판이 덜 끝난 것처럼 보였다(우진 지적).
        # 위는 배경을 가장자리까지 흘리면서 밝기만 죽이고,
        # 아래는 잔글씨 띠를 판 끝까지 늘여서 발치로 만든다
        t = np.linspace(0.18, 1.0, int(y0), dtype=np.float32)[:, None, None]
        img[:int(y0)] *= t
        # 발치를 단색으로 채웠더니 그래도 '검은 여백' 으로 보였다.
        # 자기 색이 옅게 번지는 무대 바닥 반사를 깔아서, 비어 있는 게 아니라
        # 판이 거기까지 이어지는 것으로 만든다
        foot = img[int(y1):]
        gr = np.linspace(0, 1, foot.shape[0], dtype=np.float32)[:, None, None]
        foot[:] = INK * 0.5 + C * 0.16 * (1 - (2 * gr - 1) ** 2) ** 1.4
        rule(img, int(y1), 0, W, C, 0.55, max(1, int(2 * V)))

    specks(img, 120, int(y0), int(cut), PAPER, 0.20, seed=len(name) * 5 + 9, rmax=2.6)
    bloom(img, 0.82, 16 * V, 0.22, PAPER)
    vignette(img, 0.34, 2.2)
    grain(img, 0.005, 13)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        for k, (w, h) in SIZES.items():
            im = build(name, w, h, safe=(k == 'story'))
            night(im, f'dj4_{key}_{k}')
            save(im, f'dj4_{key}_{k}')
