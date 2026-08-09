"""
R안 — **열화상.** 사람이 아니라 **열덩어리**로 보이는 판입니다.

적외선 카메라의 색표를 씁니다 — 검정 → 남보라 → 자홍 → 주황 → 백열.
같은 관객 실루엣이라도 검정으로 그리면 조용하고, 열로 칠하면 **몸이 뜨겁다**가 됩니다.
자극은 대상이 아니라 **색표**에서 나옵니다.

**열은 번져야 열입니다.** 경계가 또렷하면 색칠한 그림이고,
흐려야 카메라가 잡은 온도로 보입니다.

노출 눈금·타임코드·크로스헤어를 얹어 "카메라 화면"이라고 말합니다 —
이게 있어야 색이 디자인이 아니라 계측으로 읽힙니다.

python poster_heat.py  →  out/poster/heat_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

PAPER = np.float32([0.98, 0.98, 0.98])
HOT   = np.float32([1.00, 0.86, 0.55])
DIM   = np.float32([0.62, 0.60, 0.66])

# 적외선 색표 — (위치, RGB). **중간에 자홍이 있어야 열화상이다.**
# 검정에서 바로 붉은색으로 가면 그냥 불이고, 자홍을 거쳐야 계측 화면이 된다.
RAMP = [(0.00, (0.008, 0.010, 0.038)), (0.30, (0.150, 0.035, 0.290)),
        (0.55, (0.620, 0.070, 0.400)), (0.78, (0.960, 0.300, 0.110)),
        (1.00, (1.000, 0.720, 0.170))]
# 꼭대기를 백열(1,1,1)로 두면 제일 뜨거운 자리가 흰색이 되고, 흰색은 종이로 읽힌다.
# **열화상의 최고점은 노랑까지다** — 흰색까지 가면 낮 판이 된다.


def thermal(field):
    """0~1 값을 열화상 색으로. 색표를 직접 잡아야 중간 색이 안 튄다."""
    pos = np.array([p for p, _ in RAMP], np.float32)
    col = np.array([c for _, c in RAMP], np.float32)
    out = np.empty(field.shape + (3,), np.float32)
    for i in range(3):
        out[..., i] = np.interp(field, pos, col[:, i])
    return out


def build(W, H, story=False):
    V = W / 1080.0

    # 열 마당 — **관객을 따로따로 그린다.**
    # `crowd()` 는 머리와 어깨를 이어 붙여 한 덩어리로 만드는 함수라
    # 열로 칠하면 사람이 아니라 눈밭이 된다(실제로 두 번 그렇게 나왔다).
    # 열화상은 **몸과 몸 사이가 차가워야** 몸이 뜨겁게 보인다.
    heat = np.zeros((H, W), np.float32)
    rng = np.random.default_rng(17)
    # 앞줄이 커야 화면이 찬다. 작게 두면 가운데가 통째로 비어 계측 화면만 남는다
    for scale, base, cool in ((1.00, 0.660, 1.00), (0.80, 0.760, 0.78),
                              (0.62, 0.845, 0.58), (0.48, 0.910, 0.42)):
        y0 = H * (base if story else base - 0.015)
        r = H * 0.052 * scale
        x = -r
        while x < W + r:
            jy = y0 + rng.uniform(-1, 1) * r * 0.30
            cv2.circle(heat, (int(x), int(jy)), int(r * 0.62), cool, -1, cv2.LINE_AA)
            cv2.ellipse(heat, (int(x), int(jy + r * 1.35)), (int(r * 0.86), int(r * 1.30)),
                        0, 0, 360, cool * 0.88, -1, cv2.LINE_AA)
            if rng.random() < 0.14:                    # 손 든 사람 — 제일 뜨겁다
                cv2.line(heat, (int(x + r * 0.5), int(jy)), (int(x + r * 1.1), int(jy - r * 2.4)),
                         cool, max(2, int(r * 0.26)), cv2.LINE_AA)
            x += r * rng.uniform(2.0, 2.9)             # **간격이 있어야 사람이 갈린다**

    heat = (heat * 0.60 + cv2.GaussianBlur(heat, (0, 0), H * 0.008) * 0.55)
    # 바닥에서 올라오는 더운 공기 — 아주 옅게
    n = cv2.resize(rng.random((H // 26, W // 26)).astype(np.float32), (W, H),
                   interpolation=cv2.INTER_CUBIC)
    n = cv2.GaussianBlur(n, (0, 0), W * 0.020)
    yy = np.arange(H, dtype=np.float32)[:, None]
    heat += n * np.clip((yy - H * 0.58) / (H * 0.42), 0, 1) ** 2.0 * 0.13
    heat = np.clip(heat, 0, 0.92) ** 1.10

    img = thermal(heat)

    # ── 계측 화면 표식 ───────────────────────────────────
    M = int(W * 0.062)
    for s, c in ((0, M), (1, W - M)):                # 좌우 눈금
        for i in range(23):
            y = H * 0.16 + (H * 0.62) * i / 22
            w = 22 * V if i % 5 == 0 else 11 * V
            box(img, c - (w if s else 0), y, c + (0 if s else w), y + max(1, int(2 * V)),
                PAPER, 0.40)
    # 크로스헤어 — 화면 한가운데를 재고 있다
    cx, cy = W / 2, H * (0.560 if story else 0.545)
    for dx in (-1, 1):
        box(img, cx + dx * 30 * V, cy - 1.5 * V, cx + dx * 74 * V, cy + 1.5 * V, PAPER, 0.65)
        box(img, cx - 1.5 * V, cy + dx * 30 * V, cx + 1.5 * V, cy + dx * 74 * V, PAPER, 0.65)
    paint(img, tmask('MAX 39.4', BRAND, int(16 * V), 0.20), cx + 86 * V, cy,
          color=PAPER, a=0.70)

    ty = H * (0.062 if story else 0.056)
    paint(img, tmask('THERMAL  ·  BLACKOUT CREW  ·  SEOUL', BRAND, int(16 * V), 0.40),
          M, ty, color=PAPER, a=0.80)
    paint(img, tmask('REC  19:00–24:00', BRAND, int(16 * V), 0.20), W - M, ty,
          color=np.float32([1.0, 0.30, 0.25]), a=0.95, anchor='r')

    # ── 글자 ─────────────────────────────────────────────
    CWD = W - M * 2
    ny = H * (0.180 if story else 0.170)
    # 글자 자리를 눌러 둔다. 열 위에 흰 글자를 그냥 얹으면 획이 먹힌다
    yy2 = np.arange(H, dtype=np.float32)
    img *= (1 - 0.60 * np.exp(-((yy2 - ny) / (H * 0.085)) ** 2))[:, None, None]
    ns = justify(EV.NAME, CWD, 0.10, cap=int(148 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), W / 2, ny, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + ns * 0.82,
          color=HOT, anchor='c')

    ly = H * (0.300 if story else 0.288)
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD * 0.94, 0.14)), 0.14),
          W / 2, ly, color=PAPER, a=0.92, anchor='c')

    fy = H * (0.900 if story else 0.892)
    img *= (1 - 0.62 * np.exp(-((yy2 - (fy + 50 * V)) / (H * 0.070)) ** 2))[:, None, None]
    rule(img, fy, M, W - M, PAPER, 0.30, max(1, int(2 * V)))
    paint(img, tmask(f'{EV.DATE}   ·   {EV.TIME}', KR, int(26 * V), 0.02), W / 2, fy + 38 * V,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}   {EV.ADDR}', KR, int(16 * V), 0.02), W / 2, fy + 72 * V,
          color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(14 * V), 0.26), W / 2, fy + 102 * V,
          color=HOT, a=0.90, anchor='c')

    vignette(img, 0.46, 1.9)
    grain(img, 0.010, 26)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'heat_{k}')
        save(im, f'heat_{k}')
