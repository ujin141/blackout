"""쿠폰 인쇄 원고 — 90 × 50 mm.

    coupon_drink.png    웰컴드링크 1+1   — 팔로우 확인하고 입구에서 준다
    coupon_bottle.png   샴페인 1병       — 추첨 당첨 팀에게
    coupon_next.png     다음 행사 할인    — 그날 밤을 다음 행사로 잇는다
    coupon_sheet_a4.png A4 한 장에 10칸  — 인쇄소에 이거 하나만 넘기면 된다

**밴드와 역할이 다릅니다.** 밴드는 차고 다니는 신분증이고, 쿠폰은 **한 번 쓰고
회수하는 물건**입니다. 그래서 쿠폰에는 밴드에 없는 게 들어갑니다 — 무엇과
바꿔 주는지, 언제까지인지, 누가 확인했는지.

**왼쪽에 뜯는 쪽(스텁)을 둡니다.** 바텐더가 반을 뜯어 통에 넣으면 그날
몇 장이 나갔는지 세어집니다. 안 뜯고 도장만 찍으면 재사용이 됩니다.

**한 장에 한 가지만.** 드링크와 샴페인을 한 장에 묶으면 하나만 쓰고
나머지를 우기는 일이 생깁니다.

⚠ 흑백입니다. 컬러 예외는 모객용 판에만 줍니다 — 쿠폰은 현장에서 쓰는
물건이라 크루 톤을 따릅니다. 종이도 싸게 갑니다.

인쇄
    · A4 시트를 그대로 넘기세요. 10칸 = 2열 × 5행, 재단선 포함입니다.
    · 스텁 경계는 **미싱(퍼포레이션)** 을 요청하세요. 없으면 가위로 잘라도 됩니다.
    · 일련번호가 필요하면 인쇄소 넘버링으로. 여기서 그리면 전부 같은 번호입니다.

python coupon.py  →  out/coupon/
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask, tmask_bl, fit, paint, paint_bl, rule, box, logo, grain
from fonts import KR, KRB
import event as EV

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'coupon')
os.makedirs(OUT, exist_ok=True)

W, H = 1063, 591                       # 90 × 50 mm @300dpi
U = 18                                 # 여백 한 단위
STUB = int(W * 0.235)                  # 뜯는 쪽
HAIR = 3                               # 최소 획 0.25mm

INK = np.float32([0.05, 0.05, 0.06])
PAPER = np.float32([0.96, 0.96, 0.95])

# (파일명, 영문 머리, 무엇을 주는지, 조건 한 줄, 스텁 글자)
KINDS = [
    ('drink',  'WELCOME DRINK', EV.FOLLOW_GET, '팔로우 화면 확인 후 · 1인 1회', 'DRINK'),
    ('bottle', 'FREE BOTTLE',   '샴페인 1병',  f'추첨 당첨 팀 · 팀당 1병 · 팀당 {EV.PROMO_PER}명', 'BOTTLE'),
    ('next',   'NEXT PARTY',    '다음 행사 할인', '다음 BLACKOUT 행사에서 · 1인 1회', 'NEXT'),
]


def perf(img, x):
    """미싱 자리. **점선으로 그린다** — 실선이면 재단선으로 오해받는다."""
    d, gap = 10, 12
    y = U
    while y < H - U:
        box(img, x - HAIR / 2, y, x + HAIR / 2, y + d, INK, 0.45)
        y += d + gap


def build(head, give, cond, stub):
    img = np.repeat(np.repeat(PAPER[None, None, :], H, 0), W, 1).copy()

    # ── 뜯는 쪽 ───────────────────────────────────────────
    box(img, 0, 0, STUB, H, INK)
    lg = logo(int(U * 3.4))
    paint(img, lg, STUB / 2 - lg.shape[1] / 2, H * 0.24, color=PAPER, a=0.95)
    # 세로로 세운 글자. 가로로 두면 스텁이 좁아 두 줄이 된다
    st = tmask(stub, BRAND, int(U * 1.5), 0.30)
    st = np.rot90(st)
    paint(img, st, STUB / 2 - st.shape[1] / 2, H * 0.60, color=PAPER, a=0.85)
    perf(img, STUB)

    # ── 본판 ──────────────────────────────────────────────
    x = STUB + U * 2.4
    right = W - U * 2.4
    # **덩어리를 세로 가운데로 모은다.** 위에 붙여 두면 아래가 휑하게 비고,
    # 쿠폰은 손바닥만 해서 그 빈자리가 그대로 보인다.
    # 주는 것이 이 판의 전부라 제일 크게 쓴다 — 조건은 그 밑에 조용히.
    paint_bl(img, tmask_bl(head, BRAND, int(U * 1.15), 0.34), x, H * 0.26,
             color=INK, a=0.55)

    gs = min(int(U * 4.3), fit(give, KRB, right - x, 0.0))
    paint_bl(img, tmask_bl(give, KRB, gs, 0.0), x, H * 0.50, color=INK)

    rule(img, H * 0.60, x, right, INK, 0.22, HAIR)
    paint_bl(img, tmask_bl(cond, KR, int(U * 1.0), 0.01), x, H * 0.71,
             color=INK, a=0.62)

    # ── 발치 — 언제·어디서, 그리고 확인란 ─────────────────
    fy = H - U * 3.2
    paint_bl(img, tmask_bl(f'{EV.NAME}   {EV.DATE_EN}', BRAND,
                           int(U * 0.85), 0.18), x, fy, color=INK, a=0.55)
    # **누가 확인했는지 적을 자리.** 없으면 바텐더가 밴드에 볼펜으로 긋는다
    bw = int(U * 5.2)
    rule(img, fy, right - bw, right, INK, 0.35, HAIR)
    paint_bl(img, tmask_bl('CHECK', BRAND, int(U * 0.72), 0.24), right - bw, fy + U * 1.5,
             color=INK, a=0.40)

    grain(img, 0.004, 11)
    return np.clip(img, 0, 1)


def sheet(tiles):
    """A4 300dpi 에 10칸. **재단선을 칸 밖에 둔다** — 안쪽에 그으면 잘린
    쿠폰마다 선이 남는다."""
    A4W, A4H = 2480, 3508
    cols, rows = 2, 5
    mx = (A4W - cols * W) // (cols + 1)
    my = (A4H - rows * H) // (rows + 1)
    s = np.ones((A4H, A4W, 3), np.float32)
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        x = mx + c * (W + mx)
        y = my + r * (H + my)
        s[y:y + H, x:x + W] = tiles[i % len(tiles)]
        for xx in (x, x + W):                       # 재단 표시 — 칸 바깥에만
            box(s, xx - HAIR / 2, y - 26, xx + HAIR / 2, y - 8, INK, 0.5)
            box(s, xx - HAIR / 2, y + H + 8, xx + HAIR / 2, y + H + 26, INK, 0.5)
        for yy in (y, y + H):
            box(s, x - 26, yy - HAIR / 2, x - 8, yy + HAIR / 2, INK, 0.5)
            box(s, x + W + 8, yy - HAIR / 2, x + W + 26, yy + HAIR / 2, INK, 0.5)
    return s


if __name__ == '__main__':
    made = []
    for key, head, give, cond, stub in KINDS:
        a = build(head, give, cond, stub)
        p = os.path.join(OUT, f'coupon_{key}.png')
        Image.fromarray((a * 255).astype(np.uint8)).save(p, optimize=True)
        made.append(a)
        print(f'{p}  {W}×{H}px = 90×50mm@300dpi')
    # 시트는 드링크 쿠폰으로 채운다 — 제일 많이 쓴다
    p = os.path.join(OUT, 'coupon_sheet_a4.png')
    Image.fromarray((np.clip(sheet([made[0]]), 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(f'{p}  A4 300dpi · 10칸 (웰컴드링크)')
    print('\n스텁 경계는 미싱(퍼포레이션)으로 요청하세요. 반을 뜯어 모으면 그날 몇 장이 나갔는지 세어집니다.')
