"""
풀파티 × 솔로파티 — 실사 물 사진, 밤 (F안).

**타이틀이 안 보인다는 지적을 받아 다시 짰습니다.** 원인은 하나였습니다 —
밝은 수면 위에 흰 글자를 그냥 얹고, 안 보이니까 그림자를 덧대는 방식.
그림자는 대비를 만들지 못하고 글자를 지저분하게만 만듭니다.

    · 글자가 앉을 자리를 **사진에서 먼저 만든다**. 위에서 아래로 눌러 어둡게.
    · 그림자·외곽선은 안 쓴다. 대비는 배경이 만든다.
    · 노란 알약·노란 CTA 띠를 뺐다. 노랑은 라벨과 × 에만 남긴다.
    · 좌측 기준선 하나. 가운데 정렬 안 한다.

행사 정보는 `event.py` 한 곳에서 옵니다.

**행사가 오후 7시부터 자정까지라 밤으로 갑니다.** 낮 물색으로 두면
포스터와 실제 행사가 어긋납니다. 사진은 그대로 두고 세 가지로 밤을 만듭니다.
    · 듀오톤을 짙은 남색 쪽으로 — 수면이 어두워야 밤이다
    · 수중 조명 — 물 밑에서 올라오는 시안색 빛. 이게 없으면 그냥 어두운 물이다
    · 비네트 — 가장자리를 눌러 조명 밖은 안 보이게

사진 pool-cc0.jpg (CC0 — 표기 의무 없음, 상업적 사용 가능)

python poster_photo.py  →  out/poster/photo_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, POOL, SIZES, tmask, fit, paint, rule, duotone,
                        logo, grain, save, timetable)
from fonts import KR
import event as EV

OUT_NAME = 'photo'

INK    = np.array([0.01, 0.02, 0.08], np.float32)   # 밤 물색. 검정으로 누르면 사진이 죽는다
WHITE  = np.array([1.00, 1.00, 1.00], np.float32)
AMBER  = np.array([1.00, 0.74, 0.22], np.float32)   # 밤에는 노랑보다 호박색이 램프처럼 읽힌다
POOLLT = np.array([0.35, 0.90, 1.00], np.float32)   # 수중 조명

ROWS = [('DATE', EV.DATE), ('TIME', EV.TIME), ('VENUE', EV.VENUE),
        ('ADDRESS', EV.ADDR), ('ENTRY', EV.ENTRY)]


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0
    M = int(W * 0.088)
    lx = M + int(W * 0.215)

    img = duotone(POOL, W, H,
                  np.array([0.00, 0.05, 0.20], np.float32),
                  np.array([0.30, 0.62, 0.82], np.float32),
                  contrast=1.42, keep=0.05, focus=0.55, zoom=1.10)

    # 수중 조명 — 물 밑에서 올라오는 빛. 이게 없으면 그냥 어두운 물이다.
    yy2, xx2 = np.mgrid[0:H, 0:W].astype(np.float32)
    for cx, cy, r, k in ((0.22, 0.30, 0.34, 0.55), (0.74, 0.20, 0.30, 0.40),
                         (0.50, 0.44, 0.40, 0.30)):
        d2 = np.sqrt(((xx2 / W - cx) / r) ** 2 + ((yy2 / H - cy) / (r * (W / H))) ** 2)
        img += (np.clip(1 - d2, 0, 1) ** 2.4)[..., None] * POOLLT * k

    # 글자 자리를 사진에서 만든다. 위는 살짝, 아래로 갈수록 확실히.
    yy = np.mgrid[0:H, 0:1][0].astype(np.float32) / H
    d = np.clip((yy - 0.12) / 0.22, 0, 1) ** 1.15 * 0.80
    d += np.clip((yy - 0.46) / 0.10, 0, 1) * 0.18
    img = img * (1 - d[..., None]) + INK * d[..., None]
    t = np.clip(1 - yy / 0.13, 0, 1)[..., None] * 0.48
    img = img * (1 - t) + INK * t

    # 비네트 — 조명 밖은 안 보이게. 밤 사진의 절반은 이것이다.
    vr = np.sqrt(((xx2 / W - 0.5) / 0.70) ** 2 + ((yy2 / H - 0.32) / 0.80) ** 2)
    vg = (np.clip(vr - 0.45, 0, 1) ** 1.3 * 0.85)[..., None]
    img = img * (1 - vg) + INK * vg

    # ── 상단 ──────────────────────────────────────────────
    hy = H * 0.062
    paint(img, logo(int(44 * V)), M, hy, color=WHITE, a=0.95)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(17 * V), 0.30),
          M + int(44 * V) + int(18 * V), hy, color=WHITE, a=0.9)
    paint(img, tmask('SEOUL', BRAND, int(17 * V), 0.30), W - M, hy,
          color=AMBER, a=0.85, anchor='r')

    # ── 타이틀 — 눌러 놓은 자리 위에 그냥 얹는다 ─────────────
    tw = int(W - M * 1.3)
    t1 = tmask('POOL PARTY', BRAND, fit('POOL PARTY', BRAND, tw, 0.02), 0.02)
    t2 = tmask('SOLO PARTY', BRAND, fit('SOLO PARTY', BRAND, tw, 0.02), 0.02)
    ty = H * (0.238 if story else 0.248)
    paint(img, t1, M, ty, color=WHITE)
    my = ty + t1.shape[0] / 2 + 44 * U
    rule(img, my, M, W - M - int(70 * V), WHITE, 0.30, max(1, int(2 * V)))
    paint(img, tmask('×', BRAND, int(48 * V)), W - M, my, color=AMBER, anchor='r')
    paint(img, t2, M, my + t2.shape[0] / 2 + 44 * U, color=WHITE)

    # ── 정보표 ────────────────────────────────────────────
    y0 = H * (0.492 if story else 0.505)
    step = H * (0.034 if story else 0.036)
    for i, (k, v) in enumerate(ROWS):
        y = y0 + step * i
        rule(img, y - step * 0.46, M, W - M, WHITE, 0.16)
        paint(img, tmask(k, BRAND, int(15 * V), 0.24), M, y, color=AMBER, a=0.85)
        paint(img, tmask(v, KR, min(int(24 * V), fit(v, KR, W - M - lx)), 0.01), lx, y, a=0.97)
    rule(img, y0 + step * (len(ROWS) - 0.46), M, W - M, WHITE, 0.16)

    # ── 타임테이블 ────────────────────────────────────────
    ty2 = H * (0.680 if story else 0.690)
    paint(img, tmask('TIME TABLE', BRAND, int(15 * V), 0.24), M, ty2, color=AMBER, a=0.85)
    timetable(img, EV.TIMETABLE, M, W - M, ty2 + H * 0.035, H * 0.033, V,
              AMBER, WHITE, cols=2, ksize=14, vsize=18)

    # ── 협업 브랜드 ───────────────────────────────────────
    if EV.PARTNERS_STR:
        py = H * (0.878 if story else 0.885)
        rule(img, py - H * 0.030, M, W - M, WHITE, 0.16)
        paint(img, tmask('PARTNERS', BRAND, int(15 * V), 0.24), M, py, color=AMBER, a=0.85)
        sz = min(int(20 * V), fit(EV.PARTNERS_STR, KR, W - M - lx))
        paint(img, tmask(EV.PARTNERS_STR, KR, sz, 0.01), lx, py, a=0.88)

    # ── 하단 ──────────────────────────────────────────────
    by = H * 0.950
    paint(img, tmask(EV.HANDLE, BRAND, int(19 * V), 0.16), M, by, a=0.92)
    paint(img, tmask(EV.NOTE, KR, int(21 * V), 0.02), W - M, by, color=AMBER, anchor='r')

    grain(img, 0.010, 6)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for tag, (W, H, story) in SIZES.items():
        save(build(W, H, story), f'{OUT_NAME}_{tag}')
