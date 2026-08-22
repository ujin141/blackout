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
    # **표가 지나가는 구간을 한 번 더 떨어뜨린다.** 사진에서 밝은 데(피부·물)가
    # 표 한가운데를 지나가면 시간 글자가 그 줄에서만 흐려진다 — 줄마다 읽히는
    # 정도가 달라지는 게 제일 나쁘다. 띠를 두르지 않고 그라데이션으로 누른다.
    t0, t1 = (0.195, 0.800) if story else (0.180, 0.780)
    band = np.clip((yv - t0) / 0.05, 0, 1) * np.clip((t1 - yv) / 0.05, 0, 1)
    img *= (1 - 0.42 * band)

    M = int(W * 0.080)
    CWD = W - M * 2

    ty = H * (0.058 if story else 0.052)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.90)
    paint(img, tmask(EV.DATE, KR, int(20 * V), 0.02), W - M, ty, color=AQUA, anchor='r')
    # 표는 누가 언제 트는지를 말할 뿐, **문이 언제 열고 닫는지는 따로** 적는다
    paint(img, tmask(f'OPEN {EV.TIME_EN}', BRAND, int(16 * V), 0.24), W - M, ty + 30 * V,
          color=PAPER, a=0.88, anchor='r')

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
    # **이 판은 표가 주인공이라 병행 슬롯까지 다 보인다**(EV.BOARD, 열한 줄).
    # 다른 판은 여덟 줄 기준으로 자리를 잡아 놔서 EV.TIMETABLE 을 쓴다.
    rows = EV.BOARD
    step = (bot - top) / len(rows)
    rule(img, top - 26 * V, M, W - M, PAPER, 0.26, max(2, int(3 * V)))
    for i, (s, e, name, sub) in enumerate(rows):
        yb = top + step * i + step * 0.62
        prog = name in EV.PROGRAM
        if prog:
            # 프로그램 줄만 판을 깔아 갈라 둔다. DJ 가 아니라는 걸 색이 말한다
            box(img, M, yb - step * 0.60, W - M, yb + step * 0.22,
                np.float32([0.16, 0.05, 0.11]), 0.92)
            box(img, M, yb - step * 0.60, M + 6 * V, yb + step * 0.22, ROSE, 1.0)
        if sub:
            # 솔로파티 안에서 도는 세트. **들여쓰고 줄여야 하위로 읽힌다** —
            # 같은 크기로 놓으면 솔로파티가 끝나고 다시 시작하는 것처럼 보인다
            box(img, M + 26 * V, yb - step * 0.52, M + 30 * V, yb + step * 0.16,
                AQUA, 0.55)
        ind = 52 * V if sub else 22 * V
        paint_bl(img, tmask_bl(f'{s}–{e}', BRAND, int((19 if sub else 23) * V), 0.10),
                 M + ind, yb, color=AQUA if not prog else ROSE, a=0.80 if sub else 0.95)
        nsz = int((26 if sub else (40 if not prog else 32)) * V)
        paint_bl(img, tmask_bl(name, BRAND, nsz, 0.08),
                 M + CWD * (0.44 if sub else 0.38), yb,
                 color=PAPER if not prog else ROSE, a=0.86 if sub else 1.0)
        if not sub:
            rule(img, yb + step * 0.24, M, W - M, PAPER, 0.10, max(1, int(1 * V)))

    # ── 발 ───────────────────────────────────────────────
    fy = bot + 44 * V
    paint_bl(img, tmask_bl(f'{EV.VENUE}   {EV.ADDR}', KR, int(19 * V), 0.01), M, fy,
             color=PAPER, a=0.96)
    paint_bl(img, tmask_bl(EV.ENTRY, KR, int(18 * V), 0.01), M, fy + 36 * V,
             color=AQUA, a=0.95)
    paint_bl(img, tmask_bl(EV.AGE, KR, int(17 * V), 0.01), M, fy + 70 * V,
             color=PAPER, a=0.85)
    paint_bl(img, tmask_bl(f'AFTER PARTY   {EV.AFTER}', KR, int(17 * V), 0.01), M, fy + 104 * V,
             color=AQUA, a=0.92)
    paint_bl(img, tmask_bl(EV.RULES, KR, int(13 * V), 0.01), M, fy + 136 * V,
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
