"""
Q안 — **경고.** 포스터가 아니라 경고문처럼 생겼습니다.

공사장 위험 표지의 문법을 그대로 씁니다 — 사선 위험 띠, 반전 블록, 경고 삼각형.
이 문법이 자극적인 이유는 **읽기도 전에 몸이 먼저 반응하기 때문**입니다.
노랑·검정 사선은 "가까이 가지 마"라고 배운 무늬라 피드에서 스크롤이 멈춥니다.

**띠는 위아래 두 줄까지만.** 판 전체에 깔면 무늬가 되고, 무늬가 되면 경고가 아닙니다.

문구는 지어내지 않습니다. 행사 정보만 경고문 형식으로 배치합니다 —
없는 사실을 경고처럼 쓰면 그건 자극이 아니라 거짓말입니다.

python poster_siren.py  →  out/poster/siren_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, box, grain, save
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

INK    = np.float32([0.030, 0.028, 0.026])
HAZARD = np.float32([0.98, 0.86, 0.05])           # 위험 표지 노랑
RED    = np.float32([0.95, 0.12, 0.10])
PAPER  = np.float32([0.95, 0.95, 0.92])
DIM    = np.float32([0.55, 0.54, 0.50])


def stripes(img, y0, y1, w, color, bg, ang=38.0):
    """사선 위험 띠. **각도가 얕으면 줄무늬, 가파르면 표지판이다.** 38도가 그 선."""
    H, W = img.shape[:2]
    y0, y1 = int(y0), int(y1)
    if y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, 0:W].astype(np.float32)
    k = ((xx + yy / np.tan(np.radians(ang))) % (w * 2) < w).astype(np.float32)[..., None]
    img[y0:y1] = np.float32(bg) * (1 - k) + np.float32(color) * k


def triangle(img, cx, cy, r, color, th, V):
    """경고 삼각형. 안에 느낌표 대신 크루 마크 자리를 비워 둔다."""
    pts = np.array([[cx, cy - r], [cx + r * 0.90, cy + r * 0.62],
                    [cx - r * 0.90, cy + r * 0.62]], np.int32)
    cv2.polylines(img, [pts], True, tuple(float(v) for v in color),
                  max(2, int(th * V)), cv2.LINE_AA)


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK
    M = int(W * 0.070)
    CWD = W - M * 2
    sw = int(W * 0.038)   # 띠가 두꺼우면 노랑이 판을 먹는다

    # 위아래 위험 띠. 두 줄까지만 — 더 깔면 무늬가 된다
    stripes(img, H * 0.030, H * 0.030 + sw, sw, HAZARD, INK)
    stripes(img, H * (0.905 if story else 0.898), H * (0.905 if story else 0.898) + sw,
            sw, HAZARD, INK)

    # ── 경고 블록 ────────────────────────────────────────
    ty = H * (0.115 if story else 0.108)
    triangle(img, W / 2, ty + 34 * V, 40 * V, HAZARD, 4, V)
    paint(img, tmask('!', BRAND, int(40 * V)), W / 2, ty + 42 * V, color=HAZARD, anchor='c')
    paint(img, tmask('NOTICE  ·  BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42),
          W / 2, ty + 104 * V, color=DIM, a=0.95, anchor='c')

    # 이름 — 반전 블록 위에 검정. **경고문에서 제일 큰 글자는 바탕이 반전된다**
    ny = H * (0.235 if story else 0.225)
    ns = justify(EV.NAME, CWD * 0.96, 0.06, cap=int(150 * V))
    nm = tmask(EV.NAME, BRAND, ns, 0.06)
    bh = nm.shape[0] * 1.42
    box(img, M, ny - bh / 2, W - M, ny + bh / 2, HAZARD, 1.0)
    paint(img, nm, W / 2, ny, color=INK, anchor='c')
    # **블록 안에 두 줄을 넣지 않는다.** 형식 줄이 노란 판 경계에 걸쳐
    # 반은 검정 위, 반은 노랑 위가 되면서 획이 끊겨 보였다. 블록 밖으로 뺀다.
    paint(img, tmask(EV.FORMAT, BRAND, int(23 * V), 0.34), W / 2, ny + bh * 0.5 + 30 * V,
          color=HAZARD, a=0.95, anchor='c')

    # 날짜 — 붉은 띠 한 줄. 색이 바뀌면 등급이 바뀐 것으로 읽힌다
    dy = ny + bh / 2 + 96 * V
    box(img, M, dy - 34 * V, W - M, dy + 34 * V, RED, 1.0)
    paint(img, tmask(f'{EV.DATE}   {EV.TIME}', KR, int(30 * V), 0.02), W / 2, dy,
          color=PAPER, anchor='c')

    # ── 라인업 — 규정 목록처럼 번호를 붙인다 ───────────────
    ly = dy + 92 * V
    rule(img, ly, M, W - M, HAZARD, 0.75, max(2, int(3 * V)))
    rows = EV.LINEUP
    half = (len(rows) + 1) // 2
    step = 52 * V
    for i, name in enumerate(rows):
        cx = M + (0 if i < half else CWD * 0.52)
        y = ly + 44 * V + step * (i % half)
        paint(img, tmask(f'{i + 1:02d}', BRAND, int(19 * V), 0.14), cx, y,
              color=HAZARD, a=0.90)
        paint(img, tmask(name, BRAND, int(30 * V), 0.10), cx + CWD * 0.10, y,
              color=PAPER)
    py = ly + 44 * V + step * half + 14 * V
    prog = '  ·  '.join(sorted(EV.PROGRAM))
    box(img, M, py - 26 * V, M + CWD * 0.62, py + 26 * V, RED, 0.90)
    paint(img, tmask(prog, BRAND, int(24 * V), 0.20), M + CWD * 0.31, py,
          color=PAPER, anchor='c')

    # ── 발 ───────────────────────────────────────────────
    fy = H * (0.828 if story else 0.818)
    paint(img, tmask(EV.VENUE, KR, int(26 * V), 0.02), W / 2, fy, color=PAPER, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(17 * V), 0.02), W / 2, fy + 34 * V,
          color=DIM, a=0.95, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), W / 2, fy + 68 * V,
          color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), W / 2, H * (0.965 if story else 0.962),
          color=HAZARD, a=0.95, anchor='c')

    vignette(img, 0.26, 2.8)
    grain(img, 0.008, 24)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'siren_{k}')
        save(im, f'siren_{k}')
