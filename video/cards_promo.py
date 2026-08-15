"""참여 이벤트 카드뉴스 — 표지 1장 + 내용 3장. 1080×1350.

    0 표지   병 한 장. 왜 넘겨야 하는지만
    1 조건    무엇을 해야 하나
    2 셈·행사  몇 팀 · 언제 · 어디서
    3 CTA     마지막 장은 시키는 말만 남긴다

**마지막 장은 정보를 안 담는다.** 캐러셀에서 마지막까지 넘긴 사람은 이미
살 마음이 있는 사람이다 — 거기서 정보를 또 주면 다시 재기 시작한다.
남길 건 무엇을 하면 끝나는지 한 줄뿐이다.

**한 장에 한 가지만 쓴다.** 캐러셀에서 두 가지를 한 장에 넣으면 둘 다
안 읽힌다 — 넘기는 손가락은 한 장에 1초를 안 준다.

표지에 조건을 안 적는다. 표지의 일은 넘기게 만드는 것 하나뿐이고, 조건을
먼저 보여 주면 "귀찮네" 하고 그냥 지나간다.

색은 병 라벨에서 뽑았다(`poster_promo`와 같은 판). 줄판(`feed_promo`)은
사진 위에 얹지만 카드뉴스는 사진을 안 쓴다 — 넘기면서 읽는 판이라
배경이 매번 바뀌면 읽는 자리가 흔들린다.

python cards_promo.py  →  out/cards_promo/promo_card_{0..3}.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import (BRAND, tmask, tmask_bl, fit, paint, paint_bl, rule, box,
                        logo, grain)
from fonts import KR, KRB
from poster_promo import INK, BLUE, GOLD, PAPER, DIM
import poster_promo as PP
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'cards_promo')
os.makedirs(OUT, exist_ok=True)

W, H = 1080, 1350
M = 96                                    # 좌우 여백
FY = H - 92                               # 발치 한 줄


def field(i):
    """장마다 빛의 자리만 조금씩 옮긴다. 완전히 같으면 안 넘긴 줄 알고,
    완전히 다르면 다른 게시물로 보인다 — 그 사이를 잡는다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = W * (0.50 + 0.10 * (i - 1.5) / 1.5)
    cy = H * (0.42 + 0.06 * i)
    img += np.exp(-(((xx - cx) / (W * 0.62)) ** 2
                    + ((yy - cy) / (H * 0.46)) ** 2))[..., None] * BLUE * 0.26
    return img


def foot(img, page):
    rule(img, FY - 40, M, W - M, PAPER, 0.14, 1)
    paint_bl(img, tmask_bl(f'{EV.DATE_EN}   {EV.VENUE}', KR, 20, 0.01), M, FY,
             color=PAPER, a=0.88)
    paint_bl(img, tmask_bl(f'{page} / 3', BRAND, 20, 0.20), W - M, FY,
             color=GOLD, a=0.85, anchor='r')


def cover():
    img = field(0)
    lg = logo(56)
    paint(img, lg, W / 2 - lg.shape[1] / 2, 128, color=PAPER, a=0.92)
    paint(img, tmask('FREE BOTTLE', BRAND, 20, 0.52), W / 2, 244, color=GOLD,
          a=0.92, anchor='c')
    # **표지는 상품만 말한다.** 조건을 여기 적으면 넘기기 전에 계산부터 한다
    head = '샴페인 한 병'
    paint(img, tmask(head, KRB, min(140, fit(head, KRB, W - M * 2, 0.0)), 0.0),
          W / 2, 336, color=PAPER, anchor='c')
    paint(img, tmask('그냥 드립니다', KRB, 62, 0.0), W / 2, 434, color=BLUE, anchor='c')
    PP.bottle(img, 798, 596, cx=W / 2, halo=0.32)
    paint(img, tmask('넘기세요  →', KRB, 34, 0.02), W / 2, FY - 96,
          color=GOLD, anchor='c')
    rule(img, FY - 40, M, W - M, PAPER, 0.14, 1)
    paint_bl(img, tmask_bl(f'{EV.DATE_EN}   {EV.VENUE}', KR, 20, 0.01), M, FY,
             color=PAPER, a=0.88)
    paint_bl(img, tmask_bl(EV.HANDLE, BRAND, 19, 0.22), W - M, FY,
             color=PAPER, a=0.85, anchor='r')
    return img


def page_do():
    img = field(1)
    paint(img, tmask('조건은 셋입니다', KRB, 64, 0.02), W / 2, 214, color=PAPER, anchor='c')
    paint(img, tmask('셋 다 해야 인정됩니다', KR, 27, 0.02), W / 2, 288,
          color=BLUE, a=0.95, anchor='c')
    y, step = 430, 178
    for i, d in enumerate(EV.PROMO_DO):
        box(img, M, y - 6, M + 8, y + 96, GOLD, 0.85)
        paint_bl(img, tmask_bl(f'{i + 1}', BRAND, 32, 0.02), M + 38, y + 44,
                 color=GOLD, a=0.95)
        paint_bl(img, tmask_bl(d, KRB, 58, 0.02), M + 96, y + 48, color=PAPER)
        rule(img, y + 122, M, W - M, PAPER, 0.11, 1)
        y += step
    # 조건을 다 보여 준 자리에서 바로 첫 동작을 시킨다. 셋 다 하라고 하면
    # 크게 느껴지지만 "댓글부터" 는 3초짜리다 — 하나만 하면 나머지도 한다
    paint(img, tmask('지금 댓글부터 다세요', KRB, 40, 0.02), W / 2, FY - 100,
          color=GOLD, anchor='c')
    foot(img, 1)
    return img


def page_count():
    img = field(2)
    paint(img, tmask('몇 팀 드리나요', KRB, 52, 0.02), W / 2, 196, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.PROMO_TEAMS}팀', KRB, 210, 0.0), W / 2, 384,
          color=GOLD, anchor='c')
    paint(img, tmask(f'팀당 {EV.PROMO_PER}명  ·  팀당 샴페인 1병', KR, 27, 0.02),
          W / 2, 520, color=PAPER, a=0.94, anchor='c')
    rule(img, 594, M, W - M, PAPER, 0.14, 1)
    y = 672
    for k, v in (('DATE', EV.DATE_EN), ('OPEN', EV.TIME_EN), ('VENUE', EV.VENUE),
                 ('AFTER', EV.AFTER)):
        paint_bl(img, tmask_bl(k, BRAND, 16, 0.24), M, y, color=BLUE, a=0.95)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 22,
                               0.14 if v.isascii() else 0.01), M + 140, y,
                 color=PAPER, a=0.98)
        y += 50
    paint_bl(img, tmask_bl(EV.ADDR, KR, 17, 0.01), M + 140, y - 12, color=DIM, a=0.85)
    # **선착순만으로는 안 움직인다.** 먼저 보낸 쪽이 가져간다고 못 박아야
    # 지금 할 이유가 생긴다
    paint(img, tmask(EV.PROMO_PUSH, KRB, 36, 0.02), W / 2, FY - 100,
          color=GOLD, anchor='c')
    foot(img, 2)
    return img


def page_cta():
    """마지막 장 — **시키는 말만 남긴다.** 여기까지 넘긴 사람에게 정보를 더 주면
    다시 재기 시작한다. 남길 건 무엇을 보내면 끝나는지 한 줄이다."""
    img = field(3)
    lg = logo(52)
    paint(img, lg, W / 2 - lg.shape[1] / 2, 150, color=PAPER, a=0.88)
    paint(img, tmask('조건 다 하셨으면', KR, 30, 0.02), W / 2, 330,
          color=PAPER, a=0.92, anchor='c')
    cta = EV.PROMO_CTA
    paint(img, tmask(cta, KRB, min(126, fit(cta, KRB, W - M * 2, 0.0)), 0.0),
          W / 2, 440, color=GOLD, anchor='c')
    paint(img, tmask(EV.PROMO_CTA_SUB, KRB, 46, 0.02), W / 2, 546,
          color=PAPER, anchor='c')
    box(img, M, 640, W - M, 646, PAPER, 0.16)
    paint(img, tmask(EV.HANDLE, BRAND,
                     min(46, fit(EV.HANDLE, BRAND, W - M * 2, 0.16)), 0.16),
          W / 2, 736, color=PAPER, anchor='c')
    paint(img, tmask('프로필 → 메시지', KR, 24, 0.02), W / 2, 800,
          color=BLUE, a=0.95, anchor='c')
    paint(img, tmask(EV.PROMO_PUSH, KRB, 34, 0.02), W / 2, 908,
          color=GOLD, a=0.96, anchor='c')
    paint(img, tmask(f'{EV.NAME}   {EV.DATE_EN}', BRAND,
                     min(26, fit(f'{EV.NAME}   {EV.DATE_EN}', BRAND, W - M * 2, 0.14)),
                     0.14), W / 2, 1000, color=PAPER, a=0.88, anchor='c')
    paint(img, tmask(EV.RULES, KR, 14, 0.01), W / 2, FY - 92, color=DIM, a=0.72,
          anchor='c')
    foot(img, 3)
    return img


if __name__ == '__main__':
    for i, fn in enumerate((cover, page_do, page_count, page_cta)):
        a = np.clip(fn(), 0, 1)
        grain(a, 0.008, 17 + i)
        p = os.path.join(OUT, f'promo_card_{i}.png')
        Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
        print(p)
    print('\n캐러셀 순서: 0 → 1 → 2 → 3')
