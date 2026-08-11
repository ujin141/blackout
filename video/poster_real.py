"""
AA안 — **사진 한 장, 정보 그대로.** 제일 직접적인 판입니다.

앞선 시안들(벤·프리즘·궤도)은 컨셉을 도형으로 말했습니다. 그게 추상적이라는
지적을 받았고, 맞습니다 — **처음 보는 사람은 도형을 해석하지 않습니다.**
사진을 보고 글자를 읽습니다.

그래서 이 판은 은유가 하나도 없습니다. 밤 수영장 사진 한 장을 꽉 채우고,
그 위에 행사 이름과 **한글 정보 네 줄**을 얹습니다.
언제 · 어디서 · 누가 트는지 · 어떻게 들어가는지. 그게 전부입니다.

**글자 자리는 사진을 눌러서 만듭니다.** 그림자를 덧대면 대비는 안 생기고
글자만 지저분해집니다 — 사진을 어둡게 깔아야 흰 글자가 삽니다.

python poster_real.py  →  out/poster/real_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import (BRAND, HERO, HERO_CROP, SIZES, tmask, tmask_bl, paint, paint_bl,
                        rule, box, duotone, grain, save)
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

DEEP  = np.float32([0.034, 0.066, 0.100])          # 밤 물빛 그림자
# 밝은 쪽을 0.62 로 두니 평균 0.32 · 밝은 픽셀 13% 로 낮 수영장이 됐다.
# **밤 물은 빛나는 게 아니라 젖어 있다** — 밝은 쪽을 반으로 내린다.
LIT   = np.float32([0.52, 0.69, 0.79])             # 물에 닿은 빛
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA  = np.float32([0.30, 0.92, 1.00])
DIM   = np.float32([0.66, 0.78, 0.86])

# 라벨과 값. **문장으로 늘어놓지 않고 표로 씁니다** — 라벨이 있어야 눈이 훑습니다.
ROWS = [('일시', f'{EV.DATE}  {EV.TIME_EN}'),
        ('장소', f'{EV.VENUE}  {EV.ADDR}'),
        ('라인업', EV.LINEUP_STR),
        ('입장', EV.ENTRY),
        ('안내', EV.AGE)]


def build(W, H, story=False):
    V = W / 1080.0
    # 물 사진. zoom·focus 는 다이빙대가 대각선으로 들어오는 자리
    img = duotone(HERO, W, H, DEEP, LIT, contrast=1.20, keep=0.18, **HERO_CROP)

    # **아래를 확실히 눌러 정보 자리를 만든다.** 그림자가 아니라 사진을 죽인다
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.90 * np.clip((yy / H - (0.360 if story else 0.340)) / 0.26, 0, 1) ** 1.1)
    img *= (1 - 0.62 * np.clip(((0.220 if story else 0.200) - yy / H) / 0.22, 0, 1))

    M = int(W * 0.085)
    CWD = W - M * 2

    ty = H * (0.062 if story else 0.056)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.90)

    ny = H * (0.470 if story else 0.455)
    ns = justify(EV.NAME, CWD, 0.08, cap=int(140 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), M, ny, color=PAPER)
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.30), M, ny + ns * 0.80,
          color=AQUA, a=0.98)
    # 카피는 **한 줄까지.** 네 줄을 넣으면 포스터가 아니라 안내문이 된다
    paint(img, tmask(EV.TAGLINE, KR, int(21 * V), 0.04), M, ny + ns * 0.80 + 34 * V,
          color=PAPER, a=0.85)

    # ── 한글 정보 네 줄 ──────────────────────────────────
    y0 = ny + ns * 0.80 + 104 * V
    step = 54 * V
    rule(img, y0 - 30 * V, M, W - M, PAPER, 0.22, max(1, int(2 * V)))
    for i, (k, v) in enumerate(ROWS):
        yb = y0 + step * i
        paint_bl(img, tmask_bl(k, KR, int(20 * V), 0.06), M, yb, color=AQUA, a=1.0)
        paint_bl(img, tmask_bl(v, KR, int(23 * V), 0.01), M + CWD * 0.20, yb,
                 color=PAPER, a=0.98)
        if i < len(ROWS) - 1:
            rule(img, yb + 20 * V, M, W - M, PAPER, 0.10, max(1, int(1 * V)))

    fy = y0 + step * len(ROWS) + 26 * V
    # 상세는 캡션·구글폼으로 간다. 포스터에는 **거기로 가는 길**만
    paint(img, tmask(EV.RESERVE, KR, int(19 * V), 0.01), M, fy, color=DIM, a=0.98)
    # **핸들을 다른 줄과 같은 y 에 두지 않는다.** 오른쪽 정렬이라 값이 길어지면
    # 왼쪽 줄과 부딪힌다 — 실제로 협업 줄과 겹쳤다. 한 줄을 따로 준다.
    paint(img, tmask(EV.HANDLE, BRAND, int(19 * V), 0.24), M, fy + 38 * V,
          color=AQUA, a=0.98)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), M, fy + 74 * V,
          color=DIM, a=0.65)

    vignette(img, 0.34, 2.2)
    grain(img, 0.007, 44)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'real_{k}')
        save(im, f'real_{k}')
