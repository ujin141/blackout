"""웰컴드링크 쿠폰 — 90 × 50 mm 앞뒤.

    coupon_front.png       앞면. 무엇과 바꿔 주는지
    coupon_back.png        뒷면. 그날 밤이 여기서 안 끝난다는 것
    coupon_sheet_front.png A4 10칸 — 앞면
    coupon_sheet_back.png  A4 10칸 — 뒷면. **좌우가 뒤집혀 있다**

**밴드와 역할이 다릅니다.** 밴드는 차고 다니는 신분증이고, 쿠폰은 **한 번 쓰고
회수하는 물건**입니다. 그래서 쿠폰에는 밴드에 없는 게 들어갑니다 — 무엇과
바꿔 주는지, 조건이 무엇인지, 누가 확인했는지.

**왼쪽에 뜯는 쪽(스텁)을 둡니다.** 바텐더가 반을 뜯어 통에 넣으면 그날
몇 장이 나갔는지 세어집니다. 안 뜯고 도장만 찍으면 재사용이 됩니다.

**행사 이름도 날짜도 안 들어갑니다.** 처음엔 앞면에 행사명과 날짜를, 뒷면에
협업사 혜택을 깔았는데 그건 이 행사에서만 맞는 말입니다 — **남는 쿠폰이
다음 행사로 넘어가야 인쇄가 안 아깝습니다.** 바뀌는 건 앞면 조건 한 줄뿐이고,
그것도 `COND` 한 줄만 고치면 됩니다.

뒷면에 남긴 것 — 로고, 이름, 계정 QR. 셋뿐입니다.

⚠ 흑백입니다. 컬러 예외는 모객용 판에만 줍니다 — 쿠폰은 현장에서 쓰는
물건이라 크루 톤을 따르고, 종이도 싸게 갑니다.

**양면 인쇄에서 뒷면은 좌우를 뒤집습니다.**
긴 쪽을 축으로 뒤집어 찍으면(장변 제본) 종이가 좌우로 돌아갑니다 — 뒷면을
앞면과 같은 순서로 앉히면 1번 앞면 뒤에 2번 뒷면이 찍힙니다. 열 칸이 전부
어긋나는데 인쇄가 나온 뒤에야 보입니다.

인쇄
    · 두 시트를 같이 넘기고 **장변 제본(long-edge)** 양면으로 요청하세요.
    · 스텁 경계는 **미싱(퍼포레이션)** 을 요청하세요. 없으면 가위로 잘라도 됩니다.
    · 일련번호가 필요하면 인쇄소 넘버링으로. 여기서 그리면 전부 같은 번호입니다.

python coupon.py  →  out/coupon/
"""
import os
import numpy as np
from PIL import Image
from poster_kit import BRAND, tmask, tmask_bl, fit, paint, paint_bl, rule, box, logo, grain
from fonts import KR, KRB
import qr
import event as EV

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'coupon')
os.makedirs(OUT, exist_ok=True)

W, H = 1063, 591                       # 90 × 50 mm @300dpi
U = 18                                 # 여백 한 단위
STUB = int(W * 0.235)                  # 뜯는 쪽
HAIR = 3                               # 최소 획 0.25mm

INK = np.float32([0.05, 0.05, 0.06])
PAPER = np.float32([0.96, 0.96, 0.95])

# **판이 통째로 영문이다.** 밴드·협업 판과 같은 톤이라야 한 크루가 만든
# 물건으로 보인다. 조건 한 줄만 한글로 남긴다 — 현장에서 다투는 자리라
# 오해가 나면 돈이 든다.
HEAD = 'ON US'
GIVE = 'WELCOME DRINK 1+1'
# 조건 한 줄로는 가운데가 비고, 현장에서 물어보는 것도 못 덮는다.
# **세 줄로 나누면 여백이 채워지면서 다툴 거리가 같이 준다.**
TERMS = [('WHO',   '팔로우 화면을 보여주신 분'),
         ('WHEN',  '행사 당일 · 영업 종료 전까지'),
         ('LIMIT', '1인 1회 · 뜯긴 쿠폰만 유효'),
         ('NOTE',  '현장 교환만 · 현금 교환 불가')]
STUB_WORD = 'DRINK'

_QR = None


def code(px):
    """인스타 계정 QR. **예약 폼이 아니다** — 이 쿠폰을 든 사람은 이미
    안에 있고, 다음에 필요한 건 예약이 아니라 계정이다."""
    global _QR
    if _QR is None:
        # **로고를 안 얹으니 정정을 'm' 으로 낮춘다.** 'h' 로 뽑으면 모듈이
        # 늘어나고, 11mm 짜리 QR 에서는 모듈 하나가 0.22mm 가 되어 안 읽힌다.
        _QR = qr.build(f'https://instagram.com/{EV.HANDLE.lstrip("@").lower()}',
                       900, [0.05, 0.05, 0.06], [0.96, 0.96, 0.95],
                       badge=False, error='m')
    return np.asarray(_QR.convert('RGB').resize((px, px), Image.NEAREST)
                      ).astype(np.float32) / 255


def perf(img, x):
    """미싱 자리. **점선으로 그린다** — 실선이면 재단선으로 오해받는다."""
    d, gap = 10, 12
    y = U
    while y < H - U:
        box(img, x - HAIR / 2, y, x + HAIR / 2, y + d, INK, 0.45)
        y += d + gap


def stub(img):
    """뜯는 쪽. **검은 띠 하나로 두면 로고만 뜬 빈 판이 된다.**

    안쪽에 실선 테두리를 하나 넣고, 아래에 번호 자리를 둔다 — 인쇄소
    넘버링을 쓰든 손으로 적든, 자리가 있어야 회수한 쿠폰을 셀 수 있다."""
    box(img, 0, 0, STUB, H, INK)
    m = U * 1.1
    for x0, y0, x1, y1 in ((m, m, STUB - m, m + HAIR),                 # 위
                           (m, H - m - HAIR, STUB - m, H - m),         # 아래
                           (m, m, m + HAIR, H - m),                    # 왼
                           (STUB - m - HAIR, m, STUB - m, H - m)):     # 오른
        box(img, x0, y0, x1, y1, PAPER, 0.22)

    lg = logo(int(U * 3.2))
    paint(img, lg, STUB / 2 - lg.shape[1] / 2, H * 0.22, color=PAPER, a=0.95)
    st = np.rot90(tmask(STUB_WORD, BRAND, int(U * 1.45), 0.34))
    paint(img, st, STUB / 2 - st.shape[1] / 2, H * 0.55, color=PAPER, a=0.85)

    # 번호 자리 — 회수한 쿠폰을 세려면 자리가 있어야 한다
    nw = STUB - U * 5
    box(img, U * 2.5, H - U * 3.6, U * 2.5 + nw, H - U * 3.6 + HAIR, PAPER, 0.30)
    paint_bl(img, tmask_bl('NO.', BRAND, int(U * 0.62), 0.24), U * 2.5, H - U * 2.2,
             color=PAPER, a=0.42)
    perf(img, STUB)


def front():
    img = np.repeat(np.repeat(PAPER[None, None, :], H, 0), W, 1).copy()
    stub(img)

    x, right = STUB + U * 2.6, W - U * 2.6

    # ── 머리 ──────────────────────────────────────────────
    paint_bl(img, tmask_bl(HEAD, BRAND, int(U * 1.0), 0.40), x, U * 3.6,
             color=INK, a=0.50)
    gs = min(int(U * 2.5), fit(GIVE, BRAND, right - x, 0.05))
    paint_bl(img, tmask_bl(GIVE, BRAND, gs, 0.05), x, U * 7.2, color=INK)
    rule(img, U * 9.4, x, right, INK, 0.28, HAIR)

    # ── 조건 세 줄. **여백은 늘려서 메우는 게 아니라 정보로 채운다** ──
    ly = U * 12.4
    lx = x + U * 4.6                                   # 라벨 칸
    for i, (k, v) in enumerate(TERMS):
        if i:                                          # 줄 사이 아주 옅은 괘선
            rule(img, ly - U * 1.9, x, right, INK, 0.07, HAIR)
        paint_bl(img, tmask_bl(k, BRAND, int(U * 0.66), 0.22), x, ly,
                 color=INK, a=0.38)
        paint_bl(img, tmask_bl(v, KR, int(U * 0.92), 0.01), lx, ly, color=INK, a=0.72)
        ly += U * 3.2

    # ── 발치 ──────────────────────────────────────────────
    fy = H - U * 2.6
    rule(img, fy - U * 2.0, x, right, INK, 0.14, HAIR)
    # **행사 이름과 날짜를 안 적는다.** 적는 순간 그날에만 쓰는 물건이 된다 —
    # 남는 쿠폰이 다음 행사로 넘어가야 인쇄가 안 아깝다
    paint_bl(img, tmask_bl('BLACKOUT CREW', BRAND, int(U * 0.82), 0.24),
             x, fy, color=INK, a=0.55)
    # **누가 확인했는지 적을 자리.** 없으면 바텐더가 볼펜으로 아무 데나 긋는다
    bw = int(U * 5.0)
    box(img, right - bw, fy - U * 1.4, right, fy - U * 1.4 + HAIR, INK, 0.35)
    paint_bl(img, tmask_bl('CHECK', BRAND, int(U * 0.62), 0.24), right - bw, fy,
             color=INK, a=0.38)

    grain(img, 0.004, 11)
    return np.clip(img, 0, 1)


def back():
    """뒷면 — **크루만.**

    처음엔 협업사 혜택과 애프터파티를 깔았는데, 그건 이 행사에서만 맞는
    말이라 다음 행사에 쓰면 거짓이 된다. **쿠폰은 한 번 쓰고 버리는
    물건이지만 원고는 아니다** — 행사 이름도 날짜도 빼면 다음에도 그대로
    쓰고, 바뀌는 건 앞면 조건 한 줄뿐이다.

    남긴 것 — 로고, 이름, 계정 QR. 셋뿐이다."""
    img = np.repeat(np.repeat(INK[None, None, :], H, 0), W, 1).copy()

    # 왼쪽 — 로고와 이름. 세로 가운데
    x = U * 3.2
    lg = logo(int(U * 4.6))
    paint(img, lg, x, H * 0.42, color=PAPER, a=0.95)
    nx = x + lg.shape[1] + U * 2.2
    ns = min(int(U * 2.3), fit('BLACKOUT', BRAND, W * 0.44, 0.16))
    nm = tmask_bl('BLACKOUT', BRAND, ns, 0.16)
    paint_bl(img, nm, nx, H * 0.42 + nm[0].shape[0] / 2, color=PAPER)
    paint_bl(img, tmask_bl('SEOUL  ·  DJ CREW', BRAND, int(U * 0.78), 0.34),
             nx, H * 0.42 + nm[0].shape[0] / 2 + U * 2.1, color=PAPER, a=0.45)

    # 오른쪽 — 계정 QR. 세로선으로 두 덩어리를 가른다
    # 17mm. 모듈 0.46mm 라 어두운 실내에서도 잡힌다 — 더 줄이면 안 읽힌다
    qs = int(U * 11.4)
    qx = int(W - U * 2.4 - qs)
    qy = int((H - (qs + U * 3.4)) / 2)
    box(img, qx - U * 2.0, U * 2.4, qx - U * 2.0 + HAIR, H - U * 2.4, PAPER, 0.16)
    # QR 받침. **여백(quiet zone)이 있어야 읽힌다**
    box(img, qx - U * 0.55, qy - U * 0.55, qx + qs + U * 0.55, qy + qs + U * 0.55,
        PAPER, 0.96)
    img[qy:qy + qs, qx:qx + qs] = code(qs)
    hs = min(int(U * 0.76), fit(EV.HANDLE, BRAND, qs + U * 0.8, 0.06))
    paint_bl(img, tmask_bl(EV.HANDLE, BRAND, hs, 0.06), qx, qy + qs + U * 2.2,
             color=PAPER, a=0.88)

    grain(img, 0.004, 13)
    return np.clip(img, 0, 1)


def sheet(tile, mirror=False):
    """A4 300dpi 에 10칸.

    `mirror` 는 뒷면용. **장변 제본으로 뒤집어 찍으면 종이가 좌우로 돌아간다** —
    뒷면을 같은 순서로 앉히면 1번 앞면 뒤에 2번 뒷면이 찍힌다.
    열 순서를 뒤집어야 짝이 맞는다.

    재단 표시는 칸 바깥에만 둔다 — 안쪽에 그으면 잘린 쿠폰마다 선이 남는다."""
    A4W, A4H = 2480, 3508
    cols, rows = 2, 5
    mx = (A4W - cols * W) // (cols + 1)
    my = (A4H - rows * H) // (rows + 1)
    s = np.ones((A4H, A4W, 3), np.float32)
    for i in range(cols * rows):
        c, r = i % cols, i // cols
        if mirror:
            c = cols - 1 - c
        x, y = mx + c * (W + mx), my + r * (H + my)
        s[y:y + H, x:x + W] = tile
        for xx in (x, x + W):
            box(s, xx - HAIR / 2, y - 26, xx + HAIR / 2, y - 8, INK, 0.5)
            box(s, xx - HAIR / 2, y + H + 8, xx + HAIR / 2, y + H + 26, INK, 0.5)
        for yy in (y, y + H):
            box(s, x - 26, yy - HAIR / 2, x - 8, yy + HAIR / 2, INK, 0.5)
            box(s, x + W + 8, yy - HAIR / 2, x + W + 26, yy + HAIR / 2, INK, 0.5)
    return s


def save(a, name, note=''):
    p = os.path.join(OUT, f'{name}.png')
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(p, optimize=True)
    print(f'{p}  {a.shape[1]}×{a.shape[0]}px{note}')


if __name__ == '__main__':
    f, b = front(), back()
    save(f, 'coupon_front', '  = 90×50mm@300dpi')
    save(b, 'coupon_back', '  = 90×50mm@300dpi')
    save(sheet(f), 'coupon_sheet_front', '  A4 · 10칸')
    save(sheet(b, mirror=True), 'coupon_sheet_back', '  A4 · 10칸 · 좌우 뒤집힘')

    # **뽑았다고 읽히는 게 아니다** — 뒷면 QR 을 재 본다.
    # 카드를 통째로 줄여서 재면 안 된다(QR 도 같이 줄어 실제보다 가혹하다) —
    # **조각만 잘라 인쇄 크기(17mm)를 폰 카메라 해상도로 흉내 낸다.**
    import cv2
    qs = int(U * 11.4)
    qx, qy = int(W - U * 2.2 - qs), int((H - (qs + U * 4.4)) / 2)
    pad = int(U * 0.6)
    crop = np.asarray(Image.fromarray((b * 255).astype(np.uint8)))[
        qy - pad:qy + qs + pad, qx - pad:qx + qs + pad]
    t = cv2.resize(crop, (150, 150), interpolation=cv2.INTER_AREA)   # 17mm ≈ 150px
    got, *_ = cv2.QRCodeDetector().detectAndDecode(cv2.cvtColor(t, cv2.COLOR_RGB2BGR))
    assert got, 'QR 이 안 읽힙니다 — qs 를 키우세요'
    print('\n뒷면 QR:', got)
    print('양면은 장변 제본(long-edge)으로 요청하세요. 뒷면 시트는 이미 좌우를 뒤집어 뒀습니다.')
