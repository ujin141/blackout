"""
모집 현황 판 — 몇 차까지 찼는지 한 장으로.

사전예약제라 한 번에 다 열지 않고 나눠 받는다. **차수가 넘어갈 때마다 다시
뽑는 판**이라 `event.py` 의 WAVES 만 고치면 그림·숫자가 같이 따라온다.

이 판이 하는 일은 하나다 — **지금 움직일 이유를 숫자로 주는 것.**
그래서 제목이 "모집 현황" 이 아니라 "1차 2자리 남았습니다" 다. 현황은 게시판이고
남은 자리는 이유다. 마감은 끝난 얘기라 아무 행동도 안 만든다.

마감된 차수도 지우지 않는다. 앞 차수가 찼다는 사실이 다음 차수를 재촉하는
근거이고, 빈 판에 "2차 모집 중" 만 있으면 아무 힘이 없다.

**막대는 정원 전체를 한 줄로 그린다.** 차수마다 따로 그리면 각 차수가 얼마나
찼는지를 말하게 되는데, 그건 우리가 모르는 숫자다(예약이 들어오는 중이니까).
전체 중 어디까지 왔는지만 말한다 — 이건 확실히 아는 것이다.

⚠ 성비(RATIO)는 기본으로 안 넣는다. 예전에 성비 문구를 한 번 뺐다 —
   `event.SHOW_RATIO` 를 켜야 나온다.

python poster_wave.py  →  out/poster/wave_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, HERO, HERO_CROP, SIZES, tmask, tmask_bl, fit,
                        paint, paint_bl, rule, box, duotone, grain, save)
from fest_kit import vignette, justify, night
from fonts import KR, KRB
import event as EV

DEEP = np.float32([0.016, 0.034, 0.054])
LIT = np.float32([0.340, 0.520, 0.610])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA = np.float32([0.32, 0.92, 1.00])
CORAL = np.float32([1.00, 0.42, 0.38])
DIM = np.float32([0.58, 0.70, 0.78])


def build(W, H, story=False):
    V = W / 1080.0
    img = duotone(HERO, W, H, DEEP, LIT, contrast=1.16, keep=0.16, **HERO_CROP)
    img *= 0.42
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= 1 - 0.42 * np.exp(-((yy - H * 0.52) / (H * 0.34)) ** 2)

    M = int(W * 0.095)
    CWD = W - M * 2

    ty = H * (0.070 if story else 0.062)
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, int(17 * V), 0.42), M, ty,
          color=DIM, a=0.85)
    paint(img, tmask(EV.DATE_EN, BRAND, int(19 * V), 0.24), W - M, ty,
          color=AQUA, a=0.95, anchor='r')

    ny = H * (0.150 if story else 0.140)
    paint(img, tmask(EV.NAME, BRAND, justify(EV.NAME, CWD, 0.09, cap=int(96 * V)), 0.09),
          M, ny, color=PAPER)
    paint(img, tmask(EV.FORMAT, BRAND, int(20 * V), 0.32), M, ny + 52 * V, color=AQUA)

    # ── 막대 — 정원 전체에서 어디까지 왔는지 ───────────────
    # **블록을 통째로 가운데에 앉힌다.** 제목 자리를 비율로 박아 뒀더니 스토리에서
    # 가운데가 통째로 비었다 — 이름 아래와 발치 사이의 남는 높이에 맞춘다.
    step = 92 * V
    blkh = 78 * V + 56 * V + 96 * V + step * len(EV.WAVES)
    top = ny + 52 * V + 70 * V
    bot = H - (270 if story else 250) * V - 60 * V
    hy = top + max(0, (bot - top - blkh)) * 0.50
    # **제목이 '현황' 이면 게시판이고 '몇 자리 남음' 이면 이유가 된다.**
    # 마감은 끝난 얘기라 아무 행동도 안 만든다.
    head = (f'{EV.OPEN_WAVE[0]} {EV.OPEN_LEFT}자리 남았습니다'
            if EV.OPEN_WAVE else '사전예약 마감')
    paint(img, tmask(head, KRB, int(fit(head, KRB, CWD, 0.02)) if len(head) > 12
                     else int(56 * V), 0.02), M, hy, color=PAPER)

    by = hy + 78 * V
    bh = 22 * V
    box(img, M, by - bh / 2, W - M, by + bh / 2, PAPER, 0.14)
    done = CWD * (EV.DONE / max(EV.CAP, 1))
    box(img, M, by - bh / 2, M + done, by + bh / 2, CORAL, 0.95)
    # **숫자 폭을 재고 그 뒤에 붙인다.** 96V 로 박아 뒀더니 두 자리 수에서 겹쳤다
    nm = tmask_bl(f'{EV.DONE} / {EV.CAP}', BRAND, int(20 * V), 0.16)
    paint_bl(img, nm, M, by + 44 * V, color=PAPER, a=0.95)
    paint_bl(img, tmask_bl('명 예약', KR, int(17 * V), 0.02),
             M + nm[0].shape[1] + 12 * V, by + 44 * V, color=DIM, a=0.85)

    # ── 차수 ──────────────────────────────────────────────
    y = by + 96 * V
    for name, cap, got in EV.WAVES:
        # 세 상태가 다 다르게 읽혀야 한다 —
        #   마감      끝났다. 흐리게 두되 지우지는 않는다(1차가 찼다는 게 근거다)
        #   n자리 남음 지금 움직일 이유. 여기만 색을 준다
        #   오픈 예정  아직 안 열렸다. 존재만 알린다
        full = got >= cap
        openning = (not full) and got > 0
        col = DIM if full else PAPER
        acc = CORAL if openning else (DIM if full else AQUA)
        box(img, M, y, M + 6 * V, y + 58 * V, acc, 0.95 if openning else 0.45)
        paint_bl(img, tmask_bl(name, KRB, int(30 * V), 0.02), M + 28 * V, y + 42 * V,
                 color=col, a=1.0 if not full else 0.60)
        paint_bl(img, tmask_bl(f'{got} / {cap}명', KR, int(28 * V), 0.02),
                 M + CWD * 0.22, y + 42 * V, color=col, a=1.0 if not full else 0.60)
        tag = '마감' if full else (f'{cap - got}자리 남음' if openning else '오픈 예정')
        paint_bl(img, tmask_bl(tag, KRB, int(26 * V), 0.02), W - M, y + 42 * V,
                 color=acc, a=0.75 if full else 1.0, anchor='r')
        rule(img, y + 70 * V, M, W - M, PAPER, 0.10, max(1, int(1 * V)))
        y += step

    if EV.SHOW_RATIO:
        paint_bl(img, tmask_bl(EV.RATIO, KR, int(20 * V), 0.02), M, y + 34 * V,
                 color=AQUA, a=0.92)
        y += 44 * V

    # ── 발 ────────────────────────────────────────────────
    fy = H - (270 if story else 250) * V
    rule(img, fy - 34 * V, M, W - M, PAPER, 0.18, max(1, int(2 * V)))
    paint_bl(img, tmask_bl(f'{EV.VENUE}   {EV.ADDR}', KR, int(19 * V), 0.01), M, fy + 8 * V,
             color=PAPER, a=0.96)
    paint_bl(img, tmask_bl(f'OPEN {EV.TIME_EN}', BRAND, int(17 * V), 0.18), M, fy + 44 * V,
             color=DIM, a=0.92)
    paint_bl(img, tmask_bl(EV.ENTRY, KR, int(18 * V), 0.01), M, fy + 78 * V,
             color=AQUA, a=0.95)
    paint(img, tmask('예약 · 프로필 링크', KR, int(30 * V), 0.02), M, fy + 130 * V,
          color=CORAL)
    paint(img, tmask(EV.HANDLE, BRAND, int(17 * V), 0.24), W - M, fy + 130 * V,
          color=PAPER, a=0.88, anchor='r')
    paint(img, tmask(EV.PARTNERS_STR, BRAND,
                     min(int(12 * V), fit(EV.PARTNERS_STR, BRAND, CWD, 0.30)), 0.30),
          M, fy + 172 * V, color=DIM, a=0.60)

    vignette(img, 0.28, 2.3)
    grain(img, 0.007, 37)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    for k, (w, h, st) in SIZES.items():
        im = build(w, h, st)
        night(im, f'wave_{k}')
        save(im, f'wave_{k}')
