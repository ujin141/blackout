"""
**DJ 한 명짜리 판 — E안.** 프레임을 뚫고 나온다.

    python poster_dj5.py                 일곱 명 전부
    python poster_dj5.py lynn chips      골라서

A~D안은 전부 **평평합니다.** 인물이 배경 앞에 붙어 있을 뿐 공간이 없습니다.
"와" 소리는 화려함이 아니라 **깊이**에서 납니다 — 사람이 판 안에 있는 게
아니라 판 밖으로 걸어 나와야 합니다.

    사각 프레임      판 안에 액자를 하나 긋는다
    인물이 넘는다    머리와 어깨가 그 액자 위로 삐져나온다.
                     **이 한 겹이 전부다** — 액자가 있으니 넘는 게 보인다
    거대한 원        인물 뒤에 해 하나. 역광이 되고, 액자 안이 꽉 찬다
    잔상             좌우로 민 실루엣 두 겹. 멈춰 있지 않고 방금 움직였다
    바닥 반사        액자 아래로 인물이 비친다. 서 있는 바닥이 생긴다

인물 사진은 **실사 그대로** 얹습니다(D안과 같은 규칙) — 흑백으로 바꾸거나
색을 덮으면 사람과 배경이 한 덩어리가 됩니다.
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, tmask, paint, rule, box, glow, grain, outline,
                        save, sign, bloom)
from poster_crew import crop_head, rimlight
from fest_kit import justify, night, vignette, rays, specks, haze
from poster_dj import HUE, LINE
from poster_dj2 import MATE
from poster_dj4 import fringe, sharpen, debris, nebula, melt
from fonts import KR, KRB
from members import get
import event as EV

PAPER = np.float32([0.98, 0.98, 0.97])
DIM   = np.float32([0.60, 0.62, 0.66])

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}
SIZES = {'sq': (1080, 1080), 'story': (1080, 1920)}


def disc(img, cx, cy, r, c1, c2, a=1.0):
    """인물 뒤의 해. 안쪽이 밝고 테두리에서 한 번 더 탄다."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    body = np.clip(1 - d, 0, 1) ** 0.7
    ring = np.exp(-((d - 1.0) / 0.045) ** 2)
    img += body[..., None] * (c1 * 0.30 + c2 * 0.22) * a
    img += ring[..., None] * (c1 * 0.85 + PAPER * 0.15) * a * 1.1
    halo = np.exp(-((d - 1.0) / 0.34) ** 2)
    img += halo[..., None] * c1 * 0.16 * a


def frame(img, x0, y0, x1, y1, color, V, a=0.85):
    """액자. **얇아야 한다** — 굵으면 액자가 주인공이 된다."""
    t = max(1, int(2.4 * V))
    rule(img, y0, x0, x1, color, a, t)
    rule(img, y1, x0, x1, color, a, t)
    box(img, x0, y0, x0 + t, y1, color, a)
    box(img, x1 - t, y0, x1, y1, color, a)
    # 네 귀퉁이만 두껍게 — 액자가 아니라 조준선처럼 보인다
    L = int((x1 - x0) * 0.055)
    for cx, cy in ((x0, y0), (x1 - L, y0), (x0, y1 - t * 3), (x1 - L, y1 - t * 3)):
        box(img, cx, cy, cx + L, cy + t * 3, color, a)


def ghost(dst, al, color, dx, a):
    """잔상 한 겹. 멈춰 있지 않고 방금 움직인 것으로 보인다."""
    m = np.zeros_like(al)
    if dx >= 0:
        m[:, dx:] = al[:, :al.shape[1] - dx] if dx else al
    else:
        m[:, :dx] = al[:, -dx:]
    dst += cv2.GaussianBlur(m, (0, 0), abs(dx) * 0.35)[..., None] * color * a


def build(name, W, H, safe=False):
    V = W / 1080.0
    C, C2 = HUE[name], MATE[name]
    y0, y1 = (H * 0.088, H * 0.872) if safe else (0.0, float(H))
    M = int(W * 0.058)

    img = np.repeat(np.repeat(np.float32([0.012, 0.011, 0.017])[None, None, :],
                              H, 0), W, 1).copy()

    # ── 액자 자리 ────────────────────────────────────────
    fx0, fx1 = int(W * 0.085), int(W * 0.915)
    # 세로가 길어지면 액자도 같이 늘어나야 한다. 비율을 고정하면
    # 스토리에서 액자만 납작해져 인물이 넘는 게 아니라 걸친 것으로 보인다
    fy0 = int(H * (0.200 if safe else 0.175))
    fy1 = int(H * (0.735 if safe else 0.760))

    # ── 배경 ─────────────────────────────────────────────
    cx, cy = W * 0.50, H * 0.400
    img += nebula(W, H, cx, cy, C2 * 0.5 + C * 0.5, C, seed=len(name) * 17 + 3,
                  spread=0.95 if safe else 0.72)
    rays(img, cx, cy, 30, int(30 * V), int(H * 0.72), C * 0.7 + PAPER * 0.3, 0.045,
         phase=0.07, duty=0.30)
    disc(img, cx, cy, H * 0.235, C, C2, 0.95)
    debris(img, 30, cx, cy, PAPER * 0.35 + C * 0.65, len(name) * 11 + 5, 8 * V, 40 * V)
    haze(img, int(H * 0.34), int(H * 0.90), C * 0.7 + PAPER * 0.3, 0.075,
         seed=len(name) * 5 + 2)

    frame(img, fx0, fy0, fx1, fy1, PAPER, V, 0.30)

    # ── 이름 (인물 뒤) ───────────────────────────────────
    ny = H * 0.615
    ns = justify(name, (fx1 - fx0) * 0.94, 0.01, cap=int(230 * V))
    nm = tmask(name, BRAND, ns, 0.01)
    nm = cv2.dilate(nm, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(2, int(ns * 0.028)),) * 2))
    glow(img, nm, W / 2, ny, C, 0.40, int(30 * V), anchor='c')
    sh = cv2.GaussianBlur(nm.astype(np.float32) / 255.0, (0, 0), 13 * V)
    paint(img, (sh * 255).astype(np.uint8), W / 2, ny + 10 * V,
          color=np.float32([0, 0, 0]), a=0.60, anchor='c')
    paint(img, nm, W / 2, ny, color=PAPER, anchor='c')

    # ── 사람 ─────────────────────────────────────────────
    # **머리가 액자 위로 넘어간다.** 액자가 있으니 넘는 게 보인다
    hero_h = int(H * 0.658)
    top = int(H * 0.082)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = np.clip((al[:n].copy() - 0.07) / 0.93, 0, 1)
    px = sharpen(np.clip(fig[..., :3], 0, 1), 2.4 * V, 0.60)[:n].copy()
    a_, px = melt(a_, px, 0.34, len(name) * 31 + 2, V)

    d = int(22 * V)
    ghost(img[sl], a_, C, d, 0.30)
    ghost(img[sl], a_, C2, -d, 0.30)

    edge = rimlight(a_, V)          # 얇게, 위쪽은 죽인다 — poster_crew 참고
    lr = np.linspace(0, 1, W, dtype=np.float32)[None, :, None] ** 0.8
    two = C2[None, None, :] * (1 - lr) + C[None, None, :] * lr
    img[sl] += edge[..., None] * (two * 0.75 + PAPER * 0.25) * 0.58

    img[sl] = img[sl] * (1 - a_[..., None]) + px * a_[..., None]

    # ── 바닥 반사 ────────────────────────────────────────
    # 액자 아래로 인물이 비친다. **서 있는 바닥이 생긴다**
    rh = int(H * 0.135)
    src = min(H, top + hero_h)
    strip = img[max(0, src - rh):src][::-1].copy()
    sa = a_[max(0, n - rh):n][::-1].copy()
    if strip.shape[0] > 8:
        strip = cv2.GaussianBlur(strip, (0, 0), 9 * V)
        t = np.linspace(1, 0, strip.shape[0], dtype=np.float32)[:, None, None] ** 1.8
        ry = fy1 + int(10 * V)
        rr = min(H, ry + strip.shape[0]) - ry
        if rr > 0:
            m = (sa[:rr, ..., None] * t[:rr] * 0.22)
            img[ry:ry + rr] = img[ry:ry + rr] * (1 - m) + strip[:rr] * m

    # **사람에 가린 구간이 흐릿했다.** 알파만 올리면 뒤로 넘긴 느낌이
    # 죽는다 — 면은 반투명으로 두고 **윤곽선만 또렷하게** 한 겹 더 얹는다.
    # 글자는 속이 아니라 테두리로 읽힌다
    paint(img, nm, W / 2, ny, color=PAPER, a=0.58, anchor='c')
    paint(img, outline(nm, max(2, int(3.6 * V))), W / 2, ny, color=PAPER,
          a=0.94, anchor='c')

    # ── 글 ───────────────────────────────────────────────
    s, e = SET_AT[name]
    gs = get(name)['genres']['ko'][:3]
    ig = get(name)['instagram']

    # 시간은 액자 위 왼쪽 모서리에 걸친다
    tm = tmask(f'{s} — {e}', BRAND, int(21 * V), 0.20)
    tw = tm.shape[1] + 44 * V
    box(img, fx0, fy0 - 26 * V, fx0 + tw, fy0 + 26 * V, C * 0.90)
    paint(img, tm, fx0 + tw / 2, fy0, color=PAPER, anchor='c')
    # 액자 위 여백에 둔다. fy0 바로 위에 두니 인물 머리와 겹쳤다
    sign(img, fx1, y0 + 40 * V, size=int(13 * V), color=PAPER, a=0.88, anchor='r')

    yb = y1 - 34 * V
    paint(img, tmask(f'{EV.DATE_EN}   ·   {EV.VENUE}   ·   {EV.ADDR}', KR,
                     int(16 * V), 0.02), W / 2, yb, color=DIM, a=0.90, anchor='c')
    yb -= 42 * V
    em = tmask(EV.NAME, BRAND, int(34 * V), 0.16)
    paint(img, em, W / 2, yb, color=PAPER, anchor='c')
    rule(img, yb + 34 * V, W / 2 - em.shape[1] * 0.62, W / 2 + em.shape[1] * 0.62,
         C, 0.60, max(1, int(2 * V)))
    yb -= 44 * V
    bits = [b for b in ('  /  '.join(gs), '@' + ig if ig else '') if b]
    paint(img, tmask('     ·     '.join(bits), KR, int(17 * V), 0.02), W / 2, yb,
          color=PAPER, a=0.78, anchor='c')
    yb -= 36 * V
    paint(img, tmask(LINE[name], KRB, int(29 * V), 0.01), W / 2, yb, color=PAPER,
          anchor='c')

    specks(img, 150, 0, int(y1), PAPER, 0.20, seed=len(name) * 9 + 4, rmax=2.8)
    bloom(img, 0.80, 18 * V, 0.24, PAPER)
    fringe(img, 0.0018)
    vignette(img, 0.48, 2.0)
    grain(img, 0.005, 17)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        for k, (w, h) in SIZES.items():
            im = build(name, w, h, safe=(k == 'story'))
            night(im, f'dj5_{key}_{k}')
            save(im, f'dj5_{key}_{k}')
