"""
I안 — **배지.** 페스티벌이 해마다 찍는 그 원형 문장(紋章)입니다.

원 하나에 전부 넣습니다. 바깥 고리에 아치 글자, 안쪽에 방사선,
가운데에 이름, 아래 리본에 날짜. 라인업은 고리를 따라 돕니다.

**배지는 "이 행사는 계속된다"는 뜻입니다.** 1회차라도 배지를 쓰면
연례 행사처럼 보이고, 그게 이 시안을 쓰는 이유입니다.

글자를 통째로 굽히면 뭉개지므로 **한 자씩 돌려서** 놓습니다.
아래쪽 호는 위아래를 뒤집어야 읽힙니다.

색은 검정과 금색 둘뿐입니다. 배지에 색이 셋 이상 들어가면 훈장이 아니라 스티커입니다.

python poster_crest.py  →  out/poster/crest_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import BRAND, SIZES, tmask, paint, rule, grain, save
from fest_kit import arc_text, rays, vignette, justify, night
from fonts import KR
import event as EV

INK   = np.float32([0.026, 0.024, 0.026])
GOLD  = np.float32([0.92, 0.74, 0.38])
GOLD2 = np.float32([0.62, 0.47, 0.22])
PAPER = np.float32([0.95, 0.94, 0.91])


def ring(img, cx, cy, r, th, color, a=1.0):
    cv2.circle(img, (int(cx), int(cy)), int(r), tuple(float(v) for v in color),
               max(1, int(th)), cv2.LINE_AA)


def build(W, H, story=False):
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + INK

    CX = W / 2
    CY = H * (0.435 if story else 0.450)
    R = W * (0.400 if story else 0.385)

    # 안쪽 방사선. 가운데를 향한 시선을 만든다 — 아주 옅게
    # 살이 48 개면 빽빽해서 무늬가 되고 가운데가 안 비친다. 32 개 · 옅게.
    rays(img, CX, CY, 32, R * 0.50, R * 0.86, GOLD2, 0.13, duty=0.40)
    # 가운데를 눌러 글자 자리를 만든다. **그림자가 아니라 배경을 죽인다**
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - CX) ** 2 + (yy - CY) ** 2)
    # 가운데를 더 넓게 눌러야 이름이 살 위에 안 얹힌다
    img *= (1 - 0.90 * np.clip(1 - d / (R * 0.74), 0, 1) ** 1.2)[..., None]

    # 고리 셋. 굵기를 달리해야 판화처럼 보인다 — 같으면 과녁이다
    ring(img, CX, CY, R, 3 * V, GOLD, 1.0)
    ring(img, CX, CY, R * 0.955, 1 * V, GOLD2, 1.0)
    ring(img, CX, CY, R * 0.760, 2 * V, GOLD2, 1.0)

    # 고리 위아래의 아치 글자
    arc_text(img, 'BLACKOUT CREW', CX, CY, R * 0.865, int(34 * V), GOLD, 1.0,
             top=True, track=0.22)
    arc_text(img, 'SEOUL  ·  2026', CX, CY, R * 0.865, int(28 * V), GOLD, 0.92,
             top=False, track=0.30)
    # 좌우의 마디 표시 — 고리가 끊긴 자리를 메운다
    for s in (-1, 1):
        cv2.circle(img, (int(CX + s * R * 0.865), int(CY)), max(2, int(5 * V)),
                   tuple(float(v) for v in GOLD), -1, cv2.LINE_AA)

    # 가운데 — 이름
    inner = R * 1.30
    ns = justify(EV.NAME, inner * 0.98, 0.08, cap=int(126 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), CX, CY - R * 0.17, color=PAPER, anchor='c')
    rule(img, CY - R * 0.045, CX - inner * 0.38, CX + inner * 0.38, GOLD, 0.85,
         max(1, int(2 * V)))
    paint(img, tmask(EV.FORMAT, BRAND, int(22 * V), 0.32), CX, CY + R * 0.035,
          color=GOLD, a=0.95, anchor='c')

    # 라인업 — 두 줄로 접는다. 한 줄이면 배지 안에서 너무 작아진다
    half = (len(EV.LINEUP) + 1) // 2
    for j, part in enumerate((EV.LINEUP[:half], EV.LINEUP[half:])):
        txt = '  ·  '.join(part)
        s = justify(txt, inner * 0.72, 0.12, cap=int(40 * V))
        paint(img, tmask(txt, BRAND, s, 0.12), CX, CY + R * (0.185 + j * 0.135),
              color=PAPER, a=0.88, anchor='c')

    # 아래 리본 — 날짜. 배지에서 날짜는 리본에 앉는다
    by = CY + R * 0.505
    bw, bh = inner * 0.62, 62 * V
    cv2.rectangle(img, (int(CX - bw / 2), int(by - bh / 2)),
                  (int(CX + bw / 2), int(by + bh / 2)),
                  tuple(float(v) for v in GOLD), -1, cv2.LINE_AA)
    for s in (-1, 1):                                  # 리본 꼬리
        pts = np.array([[CX + s * bw / 2, by - bh / 2],
                        [CX + s * (bw / 2 + bh * 0.62), by - bh / 2 - bh * 0.14],
                        [CX + s * (bw / 2 + bh * 0.62), by + bh / 2 + bh * 0.14],
                        [CX + s * bw / 2, by + bh / 2]], np.int32)
        cv2.fillPoly(img, [pts], tuple(float(v) for v in GOLD2), cv2.LINE_AA)
    paint(img, tmask(EV.DATE, KR, int(32 * V), 0.02), CX, by, color=INK, anchor='c')

    # ── 배지 밖 ──────────────────────────────────────────
    ty = H * (0.070 if story else 0.062)
    paint(img, tmask('AFTER SUNSET FESTIVAL', BRAND, int(18 * V), 0.44), CX, ty,
          color=GOLD2, a=0.9, anchor='c')

    fy = H * (0.870 if story else 0.862)
    paint(img, tmask(f'{EV.TIME}   ·   {EV.VENUE}', KR, int(23 * V), 0.02), CX, fy,
          color=PAPER, a=0.92, anchor='c')
    paint(img, tmask(EV.ADDR, KR, int(17 * V), 0.02), CX, fy + 34 * V,
          color=PAPER, a=0.55, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(13 * V), 0.30), CX, fy + 74 * V,
          color=GOLD2, a=0.75, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), CX, H * 0.958,
          color=GOLD, a=0.80, anchor='c')

    vignette(img, 0.38, 2.2)
    grain(img, 0.006, 8)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'crest_{k}')
        save(im, f'crest_{k}')
