"""
AE안 — **한글 헤드라인.** 한국 사람이 보는 포스터라 한국어가 제일 큽니다.

앞선 시안은 전부 영문 이름(AFTER SUNSET)이 제일 컸습니다. 브랜드로는 맞는데,
**처음 보는 사람에게는 영문 이름이 정보가 아닙니다** — 무슨 행사인지 모릅니다.
이 판은 순서를 뒤집습니다.

    루프탑 풀파티          ← 무슨 행사인지
    8월 29일 토요일        ← 언제
    AFTER SUNSET          ← 이름은 그다음

**큰 제목은 제목용 굵기를 씁니다.** 본문 굵기를 그대로 키우면 획이 가늘어
크기만 큰 글자가 됩니다. 다만 **자간을 벌려야** 합니다 — 굵은 한글을 붙여 쓰면
전단지가 됩니다(A안 첫 판에서 반려된 이유 중 하나).

python poster_ko.py  →  out/poster/ko_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, SIZES, tmask, paint, rule, grain, save, info_block)
from scene_kit import photoscene
from fest_kit import vignette, justify, night
from fonts import KR, KRD
import event as EV

DEEP  = np.float32([0.016, 0.038, 0.062])
LIT   = np.float32([0.30, 0.48, 0.60])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA  = np.float32([0.32, 0.92, 1.00])
DIM   = np.float32([0.64, 0.74, 0.82])

HEAD = '루프탑 풀파티'
# "혼자 와도 됩니다" 는 예전에 반려된 문구다(`poster_solo.py`). 다시 쓰지 않는다 —
# 행사 형식을 한글로 옮기기만 한다. **없는 말을 지어내지 않는다.**
SUB  = '풀파티 × 솔로파티'


def build(W, H, story=False):
    V = W / 1080.0
    # **도형을 빼고 사진 + 글자만 남긴다.** 네온 원·물결·번호표는 컨셉을 상징으로
    # 옮긴 것이라 계속 "추상적" 이라는 지적을 받았다. 배경도 같은 사진 한 장으로
    # 통일해 판마다 장소가 달라 보이지 않게 한다.
    img = photoscene(W, H, story)

    # 위에서 아래로 눌러 글자 자리를 만든다. 위쪽이 헤드라인 자리다
    yy = np.arange(H, dtype=np.float32)[:, None, None] / H
    img *= (1 - 0.82 * np.clip((0.640 - yy) / 0.64, 0, 1) ** 0.85)
    img *= (1 - 0.88 * np.clip((yy - (0.680 if story else 0.660)) / 0.26, 0, 1) ** 1.0)

    M = int(W * 0.085)
    CWD = W - M * 2

    ty = H * (0.070 if story else 0.062)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=PAPER, a=0.90)

    # ── 한글 헤드라인이 제일 크다 ────────────────────────
    hy = H * (0.190 if story else 0.180)
    hs = justify(HEAD, CWD, 0.08, path=KRD, cap=int(120 * V))
    paint(img, tmask(HEAD, KRD, hs, 0.08), M, hy, color=PAPER)
    paint(img, tmask(SUB, KR, int(26 * V), 0.10), M, hy + hs * 0.86, color=AQUA, a=0.98)

    # 날짜 — 두 번째로 크다
    dy = hy + hs * 0.86 + 76 * V
    ds = justify(EV.DATE, CWD * 0.86, 0.05, path=KRD, cap=int(72 * V))
    paint(img, tmask(EV.DATE, KRD, ds, 0.05), M, dy, color=PAPER)
    paint(img, tmask(EV.TIME, KR, int(28 * V), 0.04), M, dy + ds * 0.86,
          color=PAPER, a=0.90)

    # 이름은 그다음. 브랜드지만 정보는 아니다
    ny = dy + ds * 0.86 + 68 * V
    rule(img, ny - 34 * V, M, W - M, PAPER, 0.24, max(1, int(2 * V)))
    ns = justify(EV.NAME, CWD * 0.80, 0.10, cap=int(58 * V))
    paint(img, tmask(EV.NAME, BRAND, ns, 0.10), M, ny, color=AQUA)
    paint(img, tmask(EV.FORMAT, BRAND, int(18 * V), 0.30), M, ny + 38 * V,
          color=PAPER, a=0.80)

    # ── 발 ──────────────────────────────────────────────
    # 여섯 줄을 32px 씩 쌓았더니 붙어 보였다. **정보는 한 블록으로** 묶는다
    fy = H - 322 * V
    img *= (1 - 0.70 * np.clip((yy * H - (fy - 30 * V)) / (60 * V), 0, 1))
    rule(img, fy, M, W - M, PAPER, 0.20, max(1, int(2 * V)))
    paint(img, tmask(EV.LINEUP_STR, BRAND, int(justify(EV.LINEUP_STR, CWD, 0.12)), 0.12),
          M, fy - 44 * V, color=PAPER, a=0.96)
    yb = info_block(img, M, fy + 42 * V, CWD, V, AQUA, PAPER, step=42 * V)
    paint(img, tmask(EV.PARTNERS_STR, BRAND, int(12 * V), 0.30), M, yb + 30 * V,
          color=DIM, a=0.62)
    paint(img, tmask(EV.HANDLE, BRAND, int(15 * V), 0.26), M, yb + 64 * V,
          color=AQUA, a=0.92)

    vignette(img, 0.30, 2.3)
    grain(img, 0.007, 52)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'ko_{k}')
        save(im, f'ko_{k}')
