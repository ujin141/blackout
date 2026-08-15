"""참여 이벤트 판 — **샴페인 한 병이 주인공이다.**

판매판(`poster_wave.py`)과 섞지 않는다. 무료로 받을 수 있다는 말과 자리가
얼마 안 남았다는 말이 한 판에 있으면 어느 쪽도 안 믿긴다.

병 사진이 그림의 전부라 판은 최대한 비웠다. **색은 병에서 뽑았다** — 라벨의
파랑과 금색. 배경을 다른 색으로 깔면 병이 오려 붙인 것처럼 뜬다.

조건 셋은 번호를 붙여 세로로 쌓는다. 한 줄에 몰아 쓰면 "다 해야 하는 줄
몰랐다" 는 말이 나온다 — 세는 판이라야 세 개인 걸 안 놓친다.

⚠ 병 원본이 299×500 이라 3배로 키운 누끼다. 판에서 세로 40% 를 넘기면
가장자리가 물러 보인다. 더 큰 원본이 생기면 `assets/img/stock/champagne.png`
만 갈아 끼우면 된다.

python poster_promo.py            → story · feed 두 판
"""
import os
import numpy as np
import cv2
from PIL import Image
from poster_kit import (BRAND, SIZES, STOCK, tmask, tmask_bl, fit, paint,
                        paint_bl, rule, logo, grain, save, status_tag)
from fonts import KR, KRB
import event as EV

INK = np.float32([0.014, 0.026, 0.052])          # 병 라벨의 남색에서 뽑았다
BLUE = np.float32([0.22, 0.58, 0.90])
GOLD = np.float32([0.92, 0.76, 0.38])
PAPER = np.float32([0.98, 0.99, 1.00])
DIM = np.float32([0.56, 0.63, 0.74])


def field(W, H):
    """검정에 파란 빛 한 겹. 병 뒤가 제일 밝아야 병이 판에 앉는다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - W * 0.5) / (W * 0.46)) ** 2 + ((yy - H * 0.44) / (H * 0.30)) ** 2))
    img += g[..., None] * BLUE * 0.30
    img += np.exp(-(((xx - W * 0.5) / (W * 0.20)) ** 2
                    + ((yy - H * 0.44) / (H * 0.16)) ** 2))[..., None] * PAPER * 0.10
    return img


_CACHE = None


def art():
    """누끼 병을 한 번만 읽어 캐시한다.

    **원본이 299×500 JPG 라 목의 흰 포일에 압축 블록이 보인다.** 3배로 키운
    누끼라 그 블록도 3배가 됐다 — 가장자리를 살리는 필터로만 편다.
    가우시안으로 뭉개면 라벨 글자까지 같이 죽는다."""
    global _CACHE
    if _CACHE is None:
        p = os.path.join(STOCK, EV.PROMO_BOTTLE)
        if not os.path.exists(p):
            return None
        raw = np.asarray(Image.open(p).convert('RGBA'))
        rgb = cv2.bilateralFilter(raw[..., :3], 11, 46, 46)
        _CACHE = np.dstack([rgb, raw[..., 3]]).astype(np.float32) / 255
    return _CACHE


def bottle(img, cy, h, cx=None, halo=0.34):
    """누끼 병. **바닥에 그림자를 깔지 않는다** — 병이 서 있는 게 아니라 떠 있는
    판이라 그림자를 넣으면 어디에 선 건지 물어보게 된다.

    포스터·카드뉴스·피드 줄판이 다 이걸 쓴다. 판마다 따로 그리면 병 크기가
    조금씩 달라져서 같은 물건으로 안 보인다."""
    b = art()
    if b is None:
        return
    bh, bw = b.shape[:2]
    w = int(h * bw / bh)
    b = np.asarray(Image.fromarray((b * 255).astype(np.uint8)).resize(
        (w, int(h)), Image.LANCZOS)).astype(np.float32) / 255
    H, W = img.shape[:2]
    cx = W / 2 if cx is None else cx
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    x1, y1 = min(W, x0 + w), min(H, y0 + int(h))
    sx, sy = max(0, -x0), max(0, -y0)
    x0, y0 = max(0, x0), max(0, y0)
    sub = b[sy:sy + (y1 - y0), sx:sx + (x1 - x0)]
    a = sub[..., 3:4]
    # 병 뒤로 후광. 알파를 번지게 해서 판과 병 사이를 잇는다
    hal = np.zeros((H, W), np.float32)
    hal[y0:y1, x0:x1] = a[..., 0]
    hal = cv2.GaussianBlur(hal, (0, 0), 46)
    img += (hal / max(hal.max(), 1e-6))[..., None] * BLUE * halo
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a


def build(W, H, story):
    V = H / 1920
    img = field(W, H)
    cx = W / 2

    lg = logo(int(52 * V))
    paint(img, lg, cx - lg.shape[1] / 2, 108 * V, color=PAPER, a=0.92)

    # ── 상품이 제목이다. 조건이 아니라 ──────────────────
    y = 226 * V
    paint(img, tmask('FREE ENTRY  +  BOTTLE', BRAND, int(19 * V), 0.48), cx, y,
          color=GOLD, a=0.90, anchor='c')
    # **상품 둘을 한 줄로 붙이면 둘 다 작아진다.** 쌓아야 둘 다 크다
    for t in (EV.PROMO_GET_A, EV.PROMO_GET_B):
        y += 82 * V
        paint(img, tmask(t, KRB, min(int(112 * V), fit(t, KRB, W * 0.86, 0.00)), 0.00),
              cx, y, color=PAPER, anchor='c')
    y += 74 * V
    paint(img, tmask(f'조건 {EV.PROMO_N_KO}, 다 하면 드립니다', KR, int(31 * V), 0.02), cx, y,
          color=BLUE, a=0.95, anchor='c')

    # ── 병 ──────────────────────────────────────────────
    bh = H * (0.330 if story else 0.290)
    bottle(img, H * (0.510 if story else 0.512), bh)

    # ── 조건. 번호를 붙여야 몇 개인지 안 놓친다 ─────────
    y = H * (0.700 if story else 0.720)
    step = 66 * V * (1.0 if len(EV.PROMO_DO) > 2 else 1.24)
    xn = W * 0.255
    for i, d in enumerate(EV.PROMO_DO):
        paint_bl(img, tmask_bl(f'{i + 1}', BRAND, int(30 * V), 0.02), xn - 44 * V, y,
                 color=GOLD, a=0.95)
        paint_bl(img, tmask_bl(d, KRB, int(37 * V), 0.02), xn, y, color=PAPER)
        y += step
    rule(img, y - step * 0.42, W * 0.20, W * 0.80, PAPER, 0.16, max(1, int(V)))

    # ── 셈. 몇 팀 · 몇 명인지 여기서 못 박는다 ──────────
    y += 22 * V
    paint(img, tmask(EV.PROMO_NOTE, KRB, int(38 * V), 0.02), cx, y,
          color=GOLD, anchor='c')
    y += 46 * V
    paint(img, tmask(EV.PROMO_PUSH, KRB,
                     min(int(23 * V), fit(EV.PROMO_PUSH, KRB, W * 0.86, 0.02)), 0.02),
          cx, y, color=PAPER, a=0.92, anchor='c')
    y += 48 * V
    paint(img, tmask(f'{EV.DATE_EN}   {EV.VENUE}', KR,
                     min(int(26 * V), fit(f'{EV.DATE_EN}   {EV.VENUE}', KR, W * 0.86, 0.02)),
                     0.02), cx, y, color=PAPER, a=0.92, anchor='c')
    # **판의 마지막 줄은 시키는 말이다.** '인증은 DM 으로' 는 제도를 설명한
    # 문장이라 아무도 안 움직인다 — 동사를 앞에 놓고 보낼 것까지 적는다.
    y += 58 * V
    paint(img, tmask(EV.PROMO_CTA, KRB, int(52 * V), 0.02), cx, y,
          color=GOLD, anchor='c')
    y += 54 * V
    paint(img, tmask(EV.PROMO_CTA_SUB, KRB, int(30 * V), 0.02), cx, y,
          color=BLUE, anchor='c')

    status_tag(img, cx, H - 168 * V, int(30 * V), color=PAPER, accent=GOLD,
               width=W * 0.86, bar=0.26, anchor='c')
    paint(img, tmask(EV.RULES, KR, int(15 * V), 0.02), cx, H - 62 * V,
          color=DIM, a=0.78, anchor='c')
    grain(img, 0.008, 17)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for name, (W, H, story) in SIZES.items():
        save(build(W, H, story), f'promo_{name}')
