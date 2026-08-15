"""팔로우 혜택 줄판 — 세 칸으로 그리드 한 줄을 채운다.

    │ 웰컴드링크 1+1 │ 팔로우만 │ 언제 · 어디서 · 예약 │
      ↑ 1칸은 릴스로 올린다. 커버(follow_1_cover.png)를 쓰면 제자리에 앉는다

**추첨 판(feed_promo)과 섞지 않는다.** 팔로우 하나면 되는 것과 공유·태그까지
해야 하는 것을 한 판에 놓으면 쉬운 쪽만 하고 끝난다. 이건 **모두에게** 주는
것이고 추첨은 셋만 뽑는 것이라 판을 갈라야 둘 다 산다.

**조건이 하나뿐이라 판이 비어 보인다.** 그래서 2칸은 글자를 크게 쓰고
"이게 전부다" 를 말한다 — 조건을 늘려 채우면 팔로우 혜택의 뜻이 사라진다.

이음새(x=1080, 2160)에는 아무것도 안 올린다. 올리는 순서는 3칸 → 2칸 → 1칸.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이다.

python feed_follow.py  →  out/feed_event/follow_{1,2,3}.png · follow_1_cover.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import (BRAND, tmask, tmask_bl, fit, paint, paint_bl, rule, box,
                        logo, grain)
from fest_kit import vignette
from fonts import KR, KRB
from feed_wave import cover
from cards_promo import field, scrim, GOLD, BLUE, PAPER, DIM
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_event')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T = 135
SEAM = 90


def build():
    # 칸마다 같은 배경을 쓰고 빛의 자리만 옮긴다 — 줄이 한 장면으로 읽힌다
    img = np.concatenate([field(i, TW, TH) for i in range(3)], axis=1)

    # ── 1칸 · 상품 ────────────────────────────────────────
    scrim(img[:, :TW], 150, 620, 0.62)
    scrim(img[:, :TW], 1080, TH, 0.80)
    lg = logo(52)
    paint(img, lg, TW / 2 - lg.shape[1] / 2, SAFE_T + 10, color=PAPER, a=0.92)
    paint(img, tmask('FOLLOW & GET', BRAND, 20, 0.48), TW / 2, 268, color=GOLD,
          a=0.92, anchor='c')
    paint(img, tmask('웰컴드링크', KRB, 104, 0.0), TW / 2, 356, color=PAPER, anchor='c')
    # **숫자가 상품이다.** '1+1' 은 설명이 필요 없는 말이라 제일 크게 쓴다
    paint(img, tmask('1 + 1', KRB, 190, 0.02), TW / 2, 500, color=GOLD, anchor='c')
    paint(img, tmask('오는 사람 전부', KR, 30, 0.02), TW / 2, 608, color=BLUE,
          a=0.96, anchor='c')

    # ── 2칸 · 조건 ────────────────────────────────────────
    x0 = TW
    scrim(img[:, x0:x0 + TW], 150, 900, 0.62)
    scrim(img[:, x0:x0 + TW], 1080, TH, 0.80)
    paint(img, tmask('조건은 하나입니다', KRB, 44, 0.02), x0 + TW / 2, SAFE_T + 90,
          color=PAPER, anchor='c')
    paint(img, tmask(EV.FOLLOW_DO, KRB,
                     min(88, fit(EV.FOLLOW_DO, KRB, TW - SEAM * 2, 0.0)), 0.0),
          x0 + TW / 2, 400, color=GOLD, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND,
                     min(40, fit(EV.HANDLE, BRAND, TW - SEAM * 2, 0.16)), 0.16),
          x0 + TW / 2, 500, color=PAPER, anchor='c')
    rule(img, 580, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.16, 1)
    paint(img, tmask(EV.FOLLOW_NOTE, KR,
                     min(28, fit(EV.FOLLOW_NOTE, KR, TW - SEAM * 2, 0.02)), 0.02),
          x0 + TW / 2, 654, color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(EV.FOLLOW_LIMIT, KR,
                     min(24, fit(EV.FOLLOW_LIMIT, KR, TW - SEAM * 2, 0.02)), 0.02),
          x0 + TW / 2, 706, color=DIM, a=0.92, anchor='c')
    # 더 큰 게 따로 있다는 것만 알린다. 조건은 여기 안 적는다 — 적으면 섞인다
    box(img, x0 + SEAM, 800, x0 + SEAM + 7, 890, GOLD, 0.80)
    paint_bl(img, tmask_bl('샴페인 추첨도 하고 있습니다', KRB, 32, 0.02),
             x0 + SEAM + 34, 846, color=PAPER)
    paint_bl(img, tmask_bl('조건은 지난 게시물에', KR, 22, 0.02),
             x0 + SEAM + 34, 884, color=DIM, a=0.90)

    # ── 3칸 · 언제 · 어디서 · 예약 ────────────────────────
    x0 = TW * 2
    scrim(img[:, x0:x0 + TW], 150, 1000, 0.62)
    scrim(img[:, x0:x0 + TW], 1080, TH, 0.80)
    paint(img, tmask(EV.NAME, BRAND,
                     min(76, fit(EV.NAME, BRAND, TW - SEAM * 2, 0.09)), 0.09),
          x0 + TW / 2, SAFE_T + 80, color=PAPER, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, 21, 0.34), x0 + TW / 2, SAFE_T + 136,
          color=BLUE, a=0.95, anchor='c')
    rule(img, 380, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.16, 1)
    y = 470
    for k, v in (('DATE', EV.DATE_EN), ('OPEN', EV.TIME_EN), ('VENUE', EV.VENUE),
                 ('AFTER', EV.AFTER)):
        paint_bl(img, tmask_bl(k, BRAND, 16, 0.24), x0 + SEAM, y, color=GOLD, a=0.92)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 22,
                               0.14 if v.isascii() else 0.01),
                 x0 + SEAM + 140, y, color=PAPER, a=0.98)
        y += 50
    paint_bl(img, tmask_bl(EV.ADDR, KR, 17, 0.01), x0 + SEAM + 140, y - 12,
             color=DIM, a=0.88)
    # **정원과 남은 차수를 여기서 말한다.** 혜택만 보고 온 사람에게 자리가
    # 무한하지 않다는 걸 한 번은 알려야 예약으로 넘어간다
    paint(img, tmask(f'정원 {EV.CAP}명  ·  {EV.LAST_FULL[0]} 마감', KRB, 30, 0.02),
          x0 + TW / 2, 780, color=GOLD, anchor='c')
    paint(img, tmask(EV.NEXT_OPEN, KR, 24, 0.02), x0 + TW / 2, 826,
          color=PAPER, a=0.92, anchor='c')
    paint(img, tmask('예약은 프로필 링크에서', KRB, 46, 0.02), x0 + TW / 2, 930,
          color=GOLD, anchor='c')
    paint(img, tmask('찍으면 바로 예약 폼이 열립니다', KR, 22, 0.02),
          x0 + TW / 2, 978, color=PAPER, a=0.88, anchor='c')

    # ── 발치 — 칸마다 한 줄 ───────────────────────────────
    FY = 1130
    rule(img, FY - 44, SEAM, W - SEAM, PAPER, 0.14, 1)
    paint(img, tmask(EV.DATE_EN, BRAND, 30, 0.20), TW / 2, FY, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}  ·  {EV.ADDR}', KR, 21, 0.01), TW * 1.5, FY,
          color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 22, 0.24), TW * 2.5, FY, color=PAPER, a=0.92,
          anchor='c')
    paint(img, tmask(EV.NAME, BRAND, min(20, fit(EV.NAME, BRAND, TW - SEAM * 2, 0.16)),
                     0.16), TW / 2, FY + 46, color=DIM, a=0.70, anchor='c')
    paint(img, tmask(EV.RULES, KR, 13, 0.01), TW * 1.5, FY + 46, color=DIM, a=0.62,
          anchor='c')
    paint(img, tmask(EV.AGE, KR, 15, 0.01), TW * 2.5, FY + 46, color=DIM, a=0.80,
          anchor='c')

    for c in range(3):
        vignette(img[:, c * TW:(c + 1) * TW], 0.20, 2.4)
    grain(img, 0.006, 47)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    full = Image.fromarray((build() * 255).astype(np.uint8))
    tiles = []
    for i in range(3):
        p = os.path.join(OUT, f'follow_{i + 1}.png')
        t = full.crop((i * TW, 0, (i + 1) * TW, TH))
        t.save(p, optimize=True)
        tiles.append(t)
        print(p)
    cp = os.path.join(OUT, 'follow_1_cover.png')
    cover(tiles[0]).save(cp, optimize=True)
    print(cp, '← 릴스 커버 (1080×1920, 1칸 자리)')
    print('\n올리는 순서: 3칸 → 2칸 → 1칸')
