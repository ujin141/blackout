"""
풀파티 × 솔로파티 — 티켓 시안 (C안).

다섯 시안 중 **유일하게 밝은 판**입니다. 인스타 피드는 대부분 어두운 사진이라
흰 종이 한 장이 스크롤에서 제일 먼저 걸립니다. 그게 이 안의 전부입니다.

입장권처럼 읽히게 하는 장치 — 이 넷이 다 있어야 티켓으로 읽힙니다.
    · 절취선(점선)과 양 끝 반원 홈
    · ADMIT ONE · 일련번호
    · 점선 리더로 이은 라벨/값 (영수증 조판)
    · 바코드 띠

⚠ 바코드는 **장식입니다.** 실제로 읽히는 코드가 아니고, 아무 정보도 담고 있지 않습니다.
   진짜 코드가 필요하면 발권 쪽에서 받아 이미지로 갈아 끼우세요.

색은 셋 — 종이 · 잉크 · 전기 파랑. 다른 시안과 겹치지 않게 파랑을 씁니다.
    A안 시안×마젠타 · B안 검정×레드 · D안 형광 초록 · E안 오렌지

python poster_ticket.py  →  out/poster/ticket_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import (BRAND, POOL, SIZES, tmask, fit, paint, rule, vrule, box,
                        duotone, logo, grain, save)
from fonts import KR

# ── 여기만 고치면 됨 ───────────────────────────────────────
# 행사 정보는 event.py 한 곳에서 온다. 여기서 고치지 말 것.
import event as EV
from poster_kit import timetable, partner_strip

SERIAL = 'NO. 0001'
ROWS   = [('DATE', EV.DATE), ('TIME', EV.TIME), ('VENUE', EV.VENUE),
          ('ADDRESS', EV.ADDR), ('ENTRY', EV.ENTRY)]
HANDLE = EV.HANDLE
NOTE   = EV.NOTE
# ──────────────────────────────────────────────────────────

BG    = np.array([0.07, 0.07, 0.08], np.float32)   # 카드 바깥. 홈이 보이려면 있어야 한다
PAPER = np.array([0.95, 0.94, 0.92], np.float32)
INK   = np.array([0.07, 0.07, 0.09], np.float32)
BLUE  = np.array([0.09, 0.29, 1.00], np.float32)


def dots(img, y, x0, x1, color, a, V, gap=9):
    """점선 리더. 영수증 조판에서 라벨과 값을 잇는 선."""
    step, r = int(gap * V), max(1, int(1.6 * V))
    for x in range(int(x0), int(x1), step):
        cv2.circle(img, (x, int(y)), r, tuple(float(v) for v in color * a + img[int(y), x] * (1 - a)), -1, cv2.LINE_AA)


def perforate(img, y, x0, x1, color, V):
    """절취선 — 긴 파선."""
    dash, gap = int(16 * V), int(11 * V)
    x = int(x0)
    while x < x1:
        rule(img, y, x, min(x + dash, x1), color, 0.55, max(1, int(2 * V)))
        x += dash + gap


def barcode(img, x0, x1, y0, y1, color, V, seed=5):
    """장식용 바코드. 읽히는 코드가 아니다."""
    rng = np.random.default_rng(seed)
    x = int(x0)
    while x < x1 - 2:
        w = int(rng.integers(2, 7) * V)
        if rng.random() < 0.62:
            box(img, x, y0, min(x + w, x1), y1, color, 0.92)
        x += w + int(rng.integers(2, 5) * V)


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0
    img = np.zeros((H, W, 3), np.float32) + BG

    # ── 종이 카드 ─────────────────────────────────────────
    cx0, cx1 = int(W * 0.048), int(W - W * 0.048)
    cy0, cy1 = int(H * 0.040), int(H - H * 0.040)
    box(img, cx0, cy0, cx1, cy1, PAPER)

    M = cx0 + int(W * 0.052)                        # 카드 안쪽 기준선
    Mx = cx1 - int(W * 0.052)
    iw = Mx - M

    # ── 머리 ──────────────────────────────────────────────
    hy = cy0 + 64 * U
    paint(img, logo(int(34 * V)), M, hy, color=INK)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(14 * V), 0.30),
          M + int(34 * V) + int(14 * V), hy, color=INK, a=0.85)
    paint(img, tmask('ADMIT ONE', BRAND, int(14 * V), 0.30), Mx, hy, color=BLUE, anchor='r')
    rule(img, hy + 34 * U, M, Mx, INK, 0.35, max(1, int(1 * V)))

    # ── 타이틀 두 줄. 사이에 파란 × ────────────────────────
    # 두 줄이 안쪽 폭을 꽉 채우므로 × 를 넣을 자리가 옆에 없다.
    # 줄 사이에 칸을 만들어 거기에 놓는다. 좌표를 눈대중으로 박으면
    # 글자 높이가 바뀔 때 × 가 글자 위로 올라탄다 — 실제 높이에서 계산할 것.
    t1 = tmask('POOL PARTY', BRAND, fit('POOL PARTY', BRAND, iw, 0.02), 0.02)
    t2 = tmask('SOLO PARTY', BRAND, fit('SOLO PARTY', BRAND, iw, 0.02), 0.02)
    ty = H * (0.108 if story else 0.105)
    paint(img, t1, M, ty, color=INK, valign='t')
    my = ty + t1.shape[0] + 34 * U
    rule(img, my, M, Mx - int(74 * V), INK, 0.30, max(1, int(1 * V)))
    paint(img, tmask('×', BRAND, int(46 * V)), Mx, my, color=BLUE, anchor='r')
    paint(img, t2, M, my + 34 * U, color=INK, valign='t')

    # ── 사진 창 — 신문처럼 잉크 한 색으로 ──────────────────
    py0 = int(H * 0.300)
    py1 = int(H * 0.395)
    ph = py1 - py0
    win = duotone(POOL, iw, ph, INK, PAPER, contrast=1.35, keep=0.0, focus=0.62, zoom=1.25)
    img[py0:py1, M:M + iw] = win
    rule(img, py1 + 16 * U, M, Mx, INK, 0.35, max(1, int(1 * V)))
    paint(img, tmask('SEOUL  ·  DAY TO NIGHT', BRAND, int(13 * V), 0.30),
          M, py1 + 40 * U, color=INK, a=0.6)
    paint(img, tmask(SERIAL, BRAND, int(13 * V), 0.30), Mx, py1 + 40 * U, color=INK, a=0.6, anchor='r')

    # 협업 브랜드는 위 스텁에 둔다 — 아래는 바코드가 차지해 자리가 안 난다
    ps = EV.partner_paths()
    if ps:
        py = H * 0.450
        paint(img, tmask('WITH', BRAND, int(13 * V), 0.30), M, py, color=BLUE, a=0.9)
        partner_strip(img, ps, M + int(90 * V), Mx, py, H * 0.032, INK, a=0.8, align='l',
                      names=EV.PARTNER_NAMES, name_font=KR)

    # ── 절취선 + 양 끝 홈 ─────────────────────────────────
    ny = int(H * 0.490)
    perforate(img, ny, M - int(24 * V), Mx + int(24 * V), INK, V)
    r = int(W * 0.028)
    cv2.circle(img, (cx0, ny), r, tuple(float(v) for v in BG), -1, cv2.LINE_AA)
    cv2.circle(img, (cx1, ny), r, tuple(float(v) for v in BG), -1, cv2.LINE_AA)

    # ── 정보 — 라벨 … 값 (영수증 조판) ─────────────────────
    y0 = H * 0.525
    step = H * 0.034
    for i, (k, v) in enumerate(ROWS):
        y = y0 + step * i
        lm = tmask(k, BRAND, int(14 * V), 0.24)
        paint(img, lm, M, y, color=BLUE, a=0.95)
        vm = tmask(v, KR, min(int(25 * V), fit(v, KR, iw * 0.62)), 0.01)
        paint(img, vm, Mx, y, color=INK, anchor='r')
        dots(img, y + 4 * U, M + lm.shape[1] + int(16 * V), Mx - vm.shape[1] - int(16 * V), INK, 0.42, V)

    # ── 타임테이블 ────────────────────────────────────────
    ty = H * 0.700
    rule(img, ty - 24 * U, M, Mx, INK, 0.30, max(1, int(1 * V)))
    paint(img, tmask('TIME TABLE', BRAND, int(14 * V), 0.24), M, ty, color=BLUE, a=0.95)
    timetable(img, EV.TIMETABLE, M, Mx, ty + H * 0.034, H * 0.030, V,
              BLUE, INK, cols=2, ksize=13, vsize=17)

    # ── 바코드 + 발 ───────────────────────────────────────
    by0 = int(H * 0.850)
    barcode(img, M, Mx - int(230 * V), by0, by0 + int(44 * U), INK, V)
    paint(img, tmask(NOTE, KR, int(19 * V), 0.02), Mx, by0 + 22 * U, color=BLUE, anchor='r')
    rule(img, cy1 - 74 * U, M, Mx, INK, 0.35, max(1, int(1 * V)))
    paint(img, tmask(HANDLE, BRAND, int(16 * V), 0.16), M, cy1 - 44 * U, color=INK, a=0.85)
    paint(img, tmask('BLACKOUTSOUND.COM', BRAND, int(16 * V), 0.16), Mx, cy1 - 44 * U,
          color=INK, a=0.85, anchor='r')

    grain(img, 0.010, 6)
    return np.clip(img, 0, 1)


# import 만 해도 렌더가 도는 걸 막는다 — poster_motion.py 가 build() 를 가져다 쓴다
if __name__ == '__main__':
    for tag, (W, H, story) in SIZES.items():
        save(build(W, H, story), f'ticket_{tag}')
