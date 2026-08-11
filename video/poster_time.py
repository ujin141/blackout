"""
AD안 — **타임테이블이 주인공.** 사람들이 제일 궁금해하는 걸 제일 크게 씁니다.

포스터를 보고 실제로 하는 질문은 "몇 시에 누가 트냐"입니다.
다른 시안들은 그 답을 발치에 작게 넣었습니다. 이 판은 **그것만** 씁니다 —
여덟 줄을 두 칸으로 접지 않고 한 줄씩 크게 세웁니다.

**직접적이라는 건 정보를 크게 쓴다는 뜻입니다.** 컨셉을 도형으로 옮기는 대신
답을 그냥 보여 줍니다.

사진은 뒤에 아주 옅게 깔립니다 — 있으면 밤 행사인 게 보이고,
진하면 표를 읽는 데 방해가 됩니다.

python poster_time.py  →  out/poster/time_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, HERO, HERO_CROP, SIZES, tmask, tmask_bl, paint, paint_bl,
                        rule, box, duotone, grain, save)
from fest_kit import vignette, justify, night
from fonts import KR
import event as EV

DEEP  = np.float32([0.014, 0.030, 0.052])
LIT   = np.float32([0.40, 0.66, 0.82])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA  = np.float32([0.30, 0.92, 1.00])
ROSE  = np.float32([1.00, 0.36, 0.66])
DIM   = np.float32([0.58, 0.70, 0.78])


def build(W, H, story=False):
    V = W / 1080.0
    # 사진은 **아주 옅게.** 표를 읽는 게 목적이라 배경은 배경이어야 한다
    img = duotone(HERO, W, H, DEEP, LIT, contrast=1.10, keep=0.14, **HERO_CROP)
    img *= 0.56
    # 발치는 더 눌러 둔다. 표 아래 한글이 사진 위에 뜨면 흐릿하게 읽힌다
    yv = np.arange(H, dtype=np.float32)[:, None, None] / H
    img *= (1 - 0.72 * np.clip((yv - (0.790 if story else 0.770)) / 0.20, 0, 1))

    M = int(W * 0.080)
    CWD = W - M * 2

    ty = H * (0.058 if story else 0.052)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.90)
    paint(img, tmask(EV.DATE, KR, int(20 * V), 0.02), W - M, ty, color=AQUA, anchor='r')

    ny = H * (0.128 if story else 0.120)
    ns = justify(EV.NAME, CWD, 0.08, cap=int(124 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.08), M, ny, color=PAPER)
    paint(img, tmask(EV.FORMAT, BRAND, int(21 * V), 0.30), M, ny + ns * 0.82,
          color=AQUA)

    # ── 타임테이블 : 여덟 줄을 한 줄씩 ───────────────────
    top = ny + ns * 0.82 + 60 * V
    # 발치에 두 줄이 늘었다(애프터파티 · 복장 안내). 표를 그만큼 일찍 끝낸다
    # **줄이 늘면 간격도 같이 벌려야 한다.** 줄만 끼워 넣었더니 발치가
    # 작은 글자 덩어리 하나로 뭉쳐 보였다 — 아래에 자리는 남아 있었다.
    bot = H * (0.712 if story else 0.676)
    rows = EV.TIMETABLE
    step = (bot - top) / len(rows)
    rule(img, top - 26 * V, M, W - M, PAPER, 0.26, max(2, int(3 * V)))
    for i, (s, e, name) in enumerate(rows):
        yb = top + step * i + step * 0.62
        prog = name in EV.PROGRAM
        if prog:
            # 프로그램 줄만 판을 깔아 갈라 둔다. DJ 가 아니라는 걸 색이 말한다
            box(img, M, yb - step * 0.60, W - M, yb + step * 0.22,
                np.float32([0.16, 0.05, 0.11]), 0.92)
            box(img, M, yb - step * 0.60, M + 6 * V, yb + step * 0.22, ROSE, 1.0)
        paint_bl(img, tmask_bl(f'{s}–{e}', BRAND, int(23 * V), 0.10), M + 22 * V, yb,
                 color=AQUA if not prog else ROSE, a=0.95)
        paint_bl(img, tmask_bl(name, BRAND, int(40 * V) if not prog else int(32 * V), 0.08),
                 M + CWD * 0.38, yb, color=PAPER if not prog else ROSE)
        rule(img, yb + step * 0.24, M, W - M, PAPER, 0.10, max(1, int(1 * V)))

    # ── 발 ───────────────────────────────────────────────
    fy = bot + 44 * V
    paint_bl(img, tmask_bl(f'{EV.VENUE}   {EV.ADDR}', KR, int(19 * V), 0.01), M, fy,
             color=PAPER, a=0.96)
    paint_bl(img, tmask_bl(EV.ENTRY, KR, int(18 * V), 0.01), M, fy + 36 * V,
             color=AQUA, a=0.95)
    paint_bl(img, tmask_bl(EV.AGE, KR, int(17 * V), 0.01), M, fy + 70 * V,
             color=PAPER, a=0.85)
    paint_bl(img, tmask_bl(f'애프터파티  {EV.AFTER}', KR, int(17 * V), 0.01), M, fy + 104 * V,
             color=AQUA, a=0.92)
    paint_bl(img, tmask_bl(EV.DRESS, KR, int(13 * V), 0.01), M, fy + 136 * V,
             color=DIM, a=0.72)
    paint(img, tmask(EV.HANDLE, BRAND, int(18 * V), 0.24), M, fy + 176 * V,
          color=AQUA, a=0.98)
    paint(img, tmask(EV.RESERVE, KR, int(17 * V), 0.02), W - M, fy + 176 * V,
          color=AQUA, a=0.90, anchor='r')
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(12 * V), 0.30), M, fy + 208 * V,
          color=DIM, a=0.65)

    vignette(img, 0.26, 2.5)
    grain(img, 0.007, 50)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'time_{k}')
        save(im, f'time_{k}')
