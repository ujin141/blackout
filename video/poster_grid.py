"""
풀파티 × 솔로파티 — 모듈 그리드 시안 (E안).

한 장의 사진 위에 글자를 얹는 대신, 판을 **칸으로 쪼개고 칸마다 성격을 다르게** 채웁니다.
사진 · 색면 · 타이포 · 명단이 각각 자기 칸을 갖습니다.
다섯 중 정보 밀도가 제일 높아서, 라인업까지 한눈에 보여야 할 때 이걸 씁니다.

칸 높이는 픽셀이 아니라 **비중(weight)** 으로 잡습니다.
피드(4:5)와 스토리(9:16)는 세로가 1.42배 차이 나는데,
픽셀로 박으면 스토리에서 아래가 남고 피드에서는 넘칩니다.
비중으로 잡으면 남는 세로가 칸에 비례해 분배됩니다.

색은 셋 — 검정 · 흰색 · 오렌지.
    A안 시안×마젠타 · B안 검정×레드 · C안 파랑 · D안 형광 초록

사진 둘 다 CC0. club 은 얼굴이 없는 위 34%만 쓴다 — CLUB_SAFE 를 그대로 쓸 것.

python poster_grid.py  →  out/poster/grid_{feed,story}.png
"""
import numpy as np
from poster_kit import (BRAND, POOL, CLUB, CLUB_SAFE, SIZES, tmask, fit, paint,
                        rule, box, duotone, logo, grain, save)
from fonts import KR

# ── 여기만 고치면 됨 ───────────────────────────────────────
# 행사 정보는 event.py 한 곳에서 온다. 여기서 고치지 말 것.
import event as EV
from poster_kit import timetable, partner_strip

CELLS  = [('DATE', EV.DATE), ('TIME', EV.TIME),
          ('VENUE', EV.VENUE), ('ENTRY', '사전 예약제 · 성비 1:1')]
FINE   = EV.ADDR
HANDLE = EV.HANDLE
NOTE   = EV.NOTE
# ──────────────────────────────────────────────────────────

INK    = np.array([0.04, 0.04, 0.05], np.float32)   # 칸 사이로 보이는 바탕
WHT    = np.array([0.97, 0.97, 0.96], np.float32)
ORANGE = np.array([1.00, 0.42, 0.05], np.float32)
BLK    = np.array([0.06, 0.05, 0.05], np.float32)

# (이름, 비중) — 세로를 이 비율로 나눈다
ROWS = [('head', 0.55), ('pool', 1.45), ('pair', 2.10), ('solo', 1.45),
        ('mix', 2.55), ('info', 1.80), ('foot', 0.55)]
# 로고 칸은 파일이 있을 때만 넣는다. 비워 두면 빈 흰 칸이 남는다.
if EV.partner_paths():
    ROWS.insert(-1, ('partners', 0.75))


def layout(W, H):
    """칸 자리를 돌려준다. poster_motion.py 가 칸을 하나씩 움직일 때 같은 값을 써야
    한 픽셀도 안 어긋난다 — 그래서 build() 안에 두지 않고 밖으로 뺐다."""
    M = int(W * 0.052)
    G = int(W * 0.020)                              # 칸 사이 홈
    cw = (W - M * 2 - G) // 2                       # 두 칸짜리 열 너비
    avail = H - M * 2 - G * (len(ROWS) - 1)
    tot = sum(w for _, w in ROWS)
    ys, y = {}, M
    for name, w in ROWS:
        h = avail * w / tot
        ys[name] = (y, y + h)
        y += h + G
    return M, G, cw, ys


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0
    M, G, cw, ys = layout(W, H)
    iw = W - M * 2

    img = np.zeros((H, W, 3), np.float32) + INK

    def tw(text, path, box_w, track=0.02, cap=None):
        s = fit(text, path, box_w, track)
        return tmask(text, path, min(s, cap) if cap else s, track)

    # ── 머리 ──────────────────────────────────────────────
    y0, y1 = ys['head']
    cy = (y0 + y1) / 2
    paint(img, logo(int(38 * V)), M, cy, color=WHT)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(15 * V), 0.30),
          M + int(38 * V) + int(14 * V), cy, color=WHT, a=0.9)
    paint(img, tmask('SEOUL  ·  2026', BRAND, int(15 * V), 0.30), W - M, cy,
          color=ORANGE, anchor='r')

    # ── POOL PARTY — 흰 칸에 검은 글자 ─────────────────────
    y0, y1 = ys['pool']
    box(img, M, y0, W - M, y1, WHT)
    paint(img, tw('POOL PARTY', BRAND, iw - int(52 * V)), M + int(26 * V), (y0 + y1) / 2,
          color=BLK)

    # ── 사진 두 칸 ────────────────────────────────────────
    y0, y1 = ys['pair']
    h = int(y1) - int(y0)
    img[int(y0):int(y0) + h, M:M + cw] = duotone(
        POOL, cw, h, BLK, WHT, contrast=1.32, keep=0.0, focus=0.62, zoom=1.35)
    img[int(y0):int(y0) + h, M + cw + G:M + cw + G + cw] = duotone(
        CLUB, cw, h, BLK, ORANGE, contrast=1.40, keep=0.10, **CLUB_SAFE)

    # ── SOLO PARTY — 오렌지 칸 ────────────────────────────
    y0, y1 = ys['solo']
    box(img, M, y0, W - M, y1, ORANGE)
    paint(img, tw('SOLO PARTY', BRAND, iw - int(150 * V)), M + int(26 * V), (y0 + y1) / 2,
          color=BLK)
    # × 는 라인업 칸이 타임테이블로 바뀌면서 갈 곳이 없어졌다. 여기 오른쪽 끝에 둔다.
    paint(img, tmask('×', BRAND, int((y1 - y0) * 0.42)), W - M - int(26 * V), (y0 + y1) / 2,
          color=BLK, anchor='r')

    # ── 타임테이블 칸 — 여덟 줄이라 칸 하나를 통째로 쓴다 ───
    y0, y1 = ys['mix']
    box(img, M, y0, W - M, y1, BLK)
    px = int(26 * V)
    paint(img, tmask('TIME TABLE', BRAND, int(14 * V), 0.26), M + px, y0 + 32 * U,
          color=ORANGE)
    timetable(img, EV.TIMETABLE, M + px, W - M - px, y0 + 76 * U,
              (y1 - y0 - 96 * U) / 4, V, ORANGE, WHT, cols=2, ksize=13, vsize=18)

    # ── 정보 칸 — 2×2 ─────────────────────────────────────
    y0, y1 = ys['info']
    box(img, M, y0, W - M, y1, WHT)
    px = int(26 * V)
    for i, (k, v) in enumerate(CELLS):
        bx = M + px + (cw + G) * (i % 2)
        by = y0 + (y1 - y0) * (0.22 if i < 2 else 0.56)
        paint(img, tmask(k, BRAND, int(13 * V), 0.26), bx, by, color=ORANGE)
        paint(img, tmask(v, KR, min(int(22 * V), fit(v, KR, cw - px * 2)), 0.01),
              bx, by + 32 * U, color=BLK)
    rule(img, y0 + (y1 - y0) * 0.48, M + px, W - M - px, BLK, 0.15)
    paint(img, tmask(FINE, KR, int(15 * V), 0.01), M + px, y1 - 22 * U, color=BLK, a=0.55)

    # ── 협업 브랜드 칸 ────────────────────────────────────
    if 'partners' in ys:
        y0, y1 = ys['partners']
        box(img, M, y0, W - M, y1, WHT)
        cy = (y0 + y1) / 2
        lb = tmask('PARTNERS', BRAND, int(13 * V), 0.26)
        paint(img, lb, M + px, cy, color=ORANGE)
        partner_strip(img, EV.partner_paths(), M + px + lb.shape[1] + int(34 * V),
                      W - M - px, cy, (y1 - y0) * 0.66, BLK, a=0.85, align='l',
                      names=EV.PARTNER_NAMES, name_font=KR)

    # ── 발 ────────────────────────────────────────────────
    y0, y1 = ys['foot']
    cy = (y0 + y1) / 2
    paint(img, tmask(HANDLE, BRAND, int(16 * V), 0.16), M, cy, color=WHT, a=0.9)
    paint(img, tmask(NOTE, KR, int(18 * V), 0.02), W - M, cy, color=ORANGE, anchor='r')

    grain(img, 0.009, 4)
    return np.clip(img, 0, 1)


# import 만 해도 렌더가 도는 걸 막는다 — poster_motion.py 가 build() 를 가져다 쓴다
if __name__ == '__main__':
    for tag, (W, H, story) in SIZES.items():
        save(build(W, H, story), f'grid_{tag}')
