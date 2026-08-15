"""참여 이벤트 줄판 — 세 칸으로 그리드 한 줄을 채운다.

    │ 병 · 상품 │ 조건 │ 셈 · 인증 │
      ↑ 1칸은 릴스로 올린다. 커버(promo_1_cover.png)를 쓰면 그리드에서 제자리에 앉는다

**세 칸이 이어져 보이게 하는 건 사진이 아니라 빛이다.** 칸마다 다른 사진을
쓰면서도 파란 빛 한 줄기가 1칸의 병에서 시작해 3칸까지 흐르게 깔았다 —
그리드에서 봤을 때 세 칸이 한 장면으로 읽힌다.

이음새(x=1080, 2160)에는 아무것도 안 올린다. 올리는 순서는 3칸 → 2칸 → 1칸.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이고 병 라벨의 색을 따라간다.

python feed_promo.py  →  out/feed_event/promo_{1,2,3}.png · promo_1_cover.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import (BRAND, status_tag, HEROES, tmask, tmask_bl, fit, paint, paint_bl,
                        rule, box, duotone, grain)
from fest_kit import vignette
from fonts import KR, KRB
from feed_wave import cover
import poster_promo as PP
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_event')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T = 135
SEAM = 90

DEEP = np.float32([0.012, 0.024, 0.048])
LIT = np.float32([0.24, 0.44, 0.66])
PAPER = np.float32([0.98, 0.99, 1.00])
BLUE = np.float32([0.24, 0.60, 0.92])
GOLD = np.float32([0.94, 0.78, 0.40])
DIM = np.float32([0.56, 0.64, 0.76])


def build():
    parts = [duotone(p, TW, H, DEEP, LIT, contrast=1.14, keep=0.16,
                     focus=0.50, zoom=1.05) for p, _ in HEROES[:3]]
    img = np.concatenate(parts, axis=1)
    # **사진을 거의 죽인다.** 주인공은 병이고, 사진이 살아 있으면 병이
    # 오려 붙인 것처럼 뜬다 — 여기서 사진은 바닥 재질까지다.
    img *= 0.22

    # **줄을 잇는 건 이 빛이다.** 1칸의 병 자리에서 시작해 3칸까지 번지는 띠 하나 —
    # 칸을 따로 그려도 그리드에서 한 장면으로 읽힌다.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    beam = np.exp(-((yy - H * 0.50) / (H * 0.42)) ** 2) * np.clip(1 - xx / W * 0.72, 0, 1)
    img += beam[..., None] * BLUE * 0.30
    img *= (1 - 0.55 * np.clip((yy - 1080) / 150, 0, 1))[..., None]   # 발치

    # ── 1칸 · 상품 ────────────────────────────────────────
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, 18, 0.42), TW / 2, SAFE_T + 30,
          color=DIM, a=0.85, anchor='c')
    paint(img, tmask('FREE ENTRY  +  BOTTLE', BRAND, 19, 0.48), TW / 2, 254,
          color=GOLD, a=0.92, anchor='c')
    # **상품 둘을 한 줄로 붙이면 둘 다 작아진다.** 쌓아야 둘 다 크다
    for i, t in enumerate((EV.PROMO_GET_A, EV.PROMO_GET_B)):
        paint(img, tmask(t, KRB, min(96, fit(t, KRB, TW - SEAM * 2, 0.0)), 0.0),
              TW / 2, 336 + i * 86, color=PAPER, anchor='c')
    paint(img, tmask(f'조건 {EV.PROMO_N_KO}, 다 하면 드립니다', KR, 27, 0.02), TW / 2, 500,
          color=BLUE, a=0.96, anchor='c')
    # 발치 줄이 y=1086 이다. 병이 그 아래로 내려가면 글자를 밟는다
    PP.bottle(img, 800, 484, cx=TW / 2, halo=0.30)

    # ── 2칸 · 조건 ────────────────────────────────────────
    x0 = TW
    paint(img, tmask('이렇게 하시면 됩니다', KRB, 42, 0.02), x0 + TW / 2, SAFE_T + 90,
          color=PAPER, anchor='c')
    y, step = (400, 172) if len(EV.PROMO_DO) > 2 else (452, 232)
    for i, d in enumerate(EV.PROMO_DO):
        box(img, x0 + SEAM, y - 4, x0 + SEAM + 7, y + 96, GOLD, 0.85)
        paint_bl(img, tmask_bl(f'{i + 1}', BRAND, 30, 0.02), x0 + SEAM + 34, y + 42,
                 color=GOLD, a=0.95)
        paint_bl(img, tmask_bl(d, KRB, 52, 0.02), x0 + SEAM + 86, y + 46, color=PAPER)
        rule(img, y + 118, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.12, 1)
        y += step
    paint(img, tmask('지금 댓글부터 다세요', KRB, 44, 0.02), x0 + TW / 2, 990,
          color=GOLD, anchor='c')

    # ── 3칸 · 셈 · 인증 ───────────────────────────────────
    x0 = TW * 2
    paint(img, tmask('몇 팀 드리나요', KRB, 42, 0.02), x0 + TW / 2, SAFE_T + 90,
          color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.PROMO_TEAMS}팀', KRB, 190, 0.0), x0 + TW / 2, 400,
          color=GOLD, anchor='c')
    paint(img, tmask(f'추첨 · 팀당 {EV.PROMO_PER}명 입장 무료 · 샴페인 1병', KR, 26, 0.02),
          x0 + TW / 2, 530, color=PAPER, a=0.94, anchor='c')
    rule(img, 600, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.14, 1)
    y = 672
    for k, v in (('DATE', EV.DATE_EN), ('OPEN', EV.TIME_EN), ('VENUE', EV.VENUE),
                 ('AFTER', EV.AFTER)):
        paint_bl(img, tmask_bl(k, BRAND, 16, 0.24), x0 + SEAM, y, color=BLUE, a=0.95)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 22,
                               0.14 if v.isascii() else 0.01),
                 x0 + SEAM + 140, y, color=PAPER, a=0.98)
        y += 48
    # 줄판의 마지막 칸은 시키는 칸이다. 설명은 앞 두 칸에서 다 했다
    paint(img, tmask(EV.PROMO_CTA, KRB, 60, 0.02), x0 + TW / 2, 906,
          color=GOLD, anchor='c')
    paint(img, tmask(EV.PROMO_CTA_SUB, KRB, 32, 0.02), x0 + TW / 2, 966,
          color=PAPER, anchor='c')
    paint(img, tmask(EV.PROMO_PUSH, KRB,
                     min(26, fit(EV.PROMO_PUSH, KRB, TW - SEAM * 2, 0.02)), 0.02),
          x0 + TW / 2, 1010, color=BLUE, anchor='c')

    # **상태는 마지막 칸에 한 번.** 세 칸에 다 넣으면 줄이 잔소리가 된다
    status_tag(img, x0 + SEAM, 1024, 30, color=PAPER, accent=GOLD,
               width=TW - SEAM * 2, bar=0.34)

    # ── 발치 — 칸마다 한 줄 ───────────────────────────────
    FY = 1130
    rule(img, FY - 44, SEAM, W - SEAM, PAPER, 0.14, 1)
    paint(img, tmask(EV.DATE_EN, BRAND, 30, 0.20), TW / 2, FY, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}  ·  {EV.ADDR}', KR, 21, 0.01), TW * 1.5, FY,
          color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 22, 0.24), TW * 2.5, FY, color=PAPER, a=0.92,
          anchor='c')
    paint(img, tmask(EV.NAME, BRAND, min(20, fit(EV.NAME, BRAND, TW - SEAM * 2, 0.16)), 0.16),
          TW / 2, FY + 46, color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.RULES, KR, 13, 0.01), TW * 1.5, FY + 46, color=DIM, a=0.62, anchor='c')
    paint(img, tmask(EV.AGE, KR, 15, 0.01), TW * 2.5, FY + 46, color=DIM, a=0.80, anchor='c')

    for c in range(3):
        vignette(img[:, c * TW:(c + 1) * TW], 0.20, 2.4)
    grain(img, 0.006, 43)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    full = Image.fromarray((build() * 255).astype(np.uint8))
    tiles = []
    for i in range(3):
        p = os.path.join(OUT, f'promo_{i + 1}.png')
        t = full.crop((i * TW, 0, (i + 1) * TW, TH))
        t.save(p, optimize=True)
        tiles.append(t)
        print(p)
    cp = os.path.join(OUT, 'promo_1_cover.png')
    cover(tiles[0]).save(cp, optimize=True)
    print(cp, '← 릴스 커버 (1080×1920, 1칸 자리)')
    print('\n올리는 순서: 3칸 → 2칸 → 1칸')
