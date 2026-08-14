"""
모집 현황 판 — 몇 차까지 찼는지 한 장으로.

사전예약제라 한 번에 다 열지 않고 나눠 받는다. **차수가 넘어갈 때마다 다시
뽑는 판**이라 `event.py` 의 WAVES 만 고치면 그림·숫자가 같이 따라온다.

이 판이 하는 일은 하나다 — **지금 움직일 이유를 주는 것.**
그래서 제목이 "모집 현황" 이 아니라 **지금 살 수 있는 것**이다.
개인 자리가 열려 있으면 "1차 2자리 남았습니다", 테이블만 남았으면
"현재 테이블만 예약 가능" — 자리 수를 크게 썼는데 개인 자리가 없으면
들어온 사람이 찾다가 그냥 나간다. 현황은 게시판이고
남은 자리는 이유다. 마감은 끝난 얘기라 아무 행동도 안 만든다.

마감된 차수도 지우지 않는다. 앞 차수가 찼다는 사실이 다음 차수를 재촉하는
근거이고, 빈 판에 "2차 모집 중" 만 있으면 아무 힘이 없다.

**막대는 정원 전체를 한 줄로 그린다.** 차수마다 따로 그리면 각 차수가 얼마나
찼는지를 말하게 되는데, 그건 우리가 모르는 숫자다(예약이 들어오는 중이니까).
전체 중 어디까지 왔는지만 말한다 — 이건 확실히 아는 것이다.

⚠ 성비(RATIO)는 기본으로 안 넣는다. 예전에 성비 문구를 한 번 뺐다 —
   `event.SHOW_RATIO` 를 켜야 나온다.

**마감은 정원이 차서가 아니라 날짜로 넘어간다.** 주 단위라 "몇 자리 남음" 과
"언제까지" 를 같이 말해야 움직인다 — 자리만 말하면 급할 이유가 없고,
날짜만 말하면 얼마나 급한지를 모른다.

python poster_wave.py  →  out/poster/wave_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, HEROES, SIZES, tmask, tmask_bl, fit,
                        paint, paint_bl, rule, box, duotone, grain, save)
from fest_kit import vignette, justify, night
from fonts import KR, KRB
import os
import event as EV

# 사진 번호. **기본은 3번** — 다른 판들이 1·2번을 쓰고 있어서, 현황 판까지
# 같은 사진이면 며칠마다 올리는 게시물이 전부 같은 그림이 된다.
# 파일명 뒤의 _h1 · _h2 는 poster_kit 의 save() 가 붙인다(여기서 또 붙이면 두 번 붙는다).
HERO_N = max(1, min(3, int(os.environ.get('BLACKOUT_HERO', '3'))))
# 자리는 **얼굴이 아니라 몸**. 세로 판이라 인물이 통째로 들어간다
CROPS = {1: dict(focus=0.52, zoom=1.06),
         2: dict(focus=0.46, zoom=1.30),
         3: dict(focus=0.50, zoom=1.06)}

DEEP = np.float32([0.016, 0.034, 0.054])
LIT = np.float32([0.340, 0.520, 0.610])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA = np.float32([0.32, 0.92, 1.00])
CORAL = np.float32([1.00, 0.42, 0.38])
DIM = np.float32([0.58, 0.70, 0.78])


def build(W, H, story=False):
    V = W / 1080.0
    # **다른 판과 다른 사진을 쓴다.** 현황 판은 며칠마다 다시 올리는 판이라
    # 포스터와 같은 사진이면 같은 게시물을 또 올린 것처럼 보인다.
    path, crop = HEROES[HERO_N - 1]
    img = duotone(path, W, H, DEEP, LIT, contrast=1.16, keep=0.18, **CROPS[HERO_N])
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
    blkh = 46 * V + 62 * V + 78 * V + 56 * V + 96 * V + step * len(EV.WAVES)
    top = ny + 52 * V + 70 * V
    bot = H - (270 if story else 250) * V - 60 * V
    hy = top + max(0, (bot - top - blkh)) * 0.50
    # **제목은 마감일이 아니라 지금 살 수 있는 것.** '몇 자리 남음' 은 개인 자리가
    # 열려 있을 때 얘기다. 테이블만 남았는데 자리 수를 크게 쓰면, 들어온 사람이
    # 개인 자리를 찾다가 없어서 그냥 나간다.
    if EV.SALE == 'table':
        # 방금 닫힌 차수를 말한다. 아직 안 열린 차수의 마감일을 쓰면
        # 이미 받는 중인 줄로 읽힌다
        head = EV.SALE_NOTE
        sub = f'{EV.LAST_FULL[0]} 마감' if EV.LAST_FULL else ''
    elif EV.OPEN_WAVE:
        head, sub = (f'{EV.OPEN_WAVE[0]} {EV.OPEN_LEFT}자리 남았습니다',
                     f'{EV.OPEN_WAVE[0]} 마감 {EV.OPEN_WAVE[3]}')
    else:
        head, sub = '사전예약 마감', ''
    # **상한 없이 fit 만 쓰면 짧은 문구가 판을 넘치고 아래 줄과 겹친다.**
    hs = min(int(54 * V), fit(head, KRB, CWD, 0.02))
    paint(img, tmask(head, KRB, hs, 0.02), M, hy, color=PAPER)
    if sub:
        # **몇 자리 남았는지와 언제까지인지는 붙어 있어야 한다.** 자리만 말하면
        # 급할 이유가 없고, 날짜만 말하면 얼마나 급한지를 모른다.
        paint(img, tmask(sub, KRB, int(26 * V), 0.02), M, hy + 54 * V, color=CORAL)
    if EV.NEXT_OPEN:
        # 다음 차수가 언제 열리는지. **닫는 말만 하면 그냥 끝난 행사로 읽힌다**
        paint(img, tmask(EV.NEXT_OPEN, KRB, int(24 * V), 0.02), M, hy + 100 * V,
              color=AQUA, a=0.95)

    by = hy + 186 * V
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
    for name, cap, got, due in EV.WAVES:
        # 세 상태가 다 다르게 읽혀야 한다 —
        #   마감      끝났다. 흐리게 두되 지우지는 않는다(앞 차수가 찼다는 게 근거다)
        #   n자리 남음 지금 움직일 이유. 여기만 색을 준다
        #   오픈 예정  아직 안 열렸다. 존재와 마감일만 알린다
        full = got >= cap
        openning = (not full) and got > 0
        col = DIM if full else PAPER
        acc = CORAL if openning else (DIM if full else AQUA)
        box(img, M, y, M + 6 * V, y + 58 * V, acc, 0.95 if openning else 0.45)
        paint_bl(img, tmask_bl(name, KRB, int(30 * V), 0.02), M + 28 * V, y + 42 * V,
                 color=col, a=1.0 if not full else 0.60)
        paint_bl(img, tmask_bl(f'{got} / {cap}명', KR, int(27 * V), 0.02),
                 M + CWD * 0.20, y + 42 * V, color=col, a=1.0 if not full else 0.60)
        # **마감일을 줄마다 적는다.** 주 단위로 넘어가니 어느 주에 걸린 건지가
        # 그 자체로 정보다 — 지금 안 하면 다음 주까지 기다린다는 뜻이다
        paint_bl(img, tmask_bl(f'~{due}', KR, int(21 * V), 0.02),
                 M + CWD * 0.48, y + 42 * V, color=col, a=0.80 if not full else 0.50)
        # **테이블만 파는 동안에는 개인 자리 수를 안 쓴다.** 2자리 남았다고 해 놓고
        # 개인 예약이 안 되면 들어온 사람이 속았다고 느낀다.
        if full:
            tag = '마감'
        elif openning:
            tag = '테이블만' if EV.SALE == 'table' else f'{cap - got}자리'
        else:
            tag = '오픈 예정'
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
