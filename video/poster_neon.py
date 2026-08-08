"""
풀파티 × 솔로파티 — 네온 사인 시안 (D안).

글자를 채우지 않고 **속을 비운 테두리(튜브)** 로 그린 뒤 빛을 더합니다.
클럽 간판을 그대로 옮긴 판이라 다섯 중 밤 느낌이 제일 셉니다.

튜브가 튜브처럼 보이려면 세 겹이 필요합니다 — 하나라도 빠지면 그냥 외곽선입니다.
    1. 넓고 옅은 후광 (반경 26V)   유리관 밖으로 새는 빛
    2. 좁고 진한 후광 (반경 9V)    관 바로 옆이 타는 느낌
    3. 흰빛에 가까운 심 (테두리)    관 안쪽 필라멘트

바닥 반사도 넣습니다. 위아래로 뒤집어 흐린 복사본을 아주 옅게 깔면
간판이 공중에 뜬 게 아니라 어딘가에 걸린 것처럼 읽힙니다.

색은 셋 — 검정 · 형광 초록 · 흰색.
    A안 시안×마젠타 · B안 검정×레드 · C안 파랑 · E안 오렌지

사진 club-cc0.jpg (CC0). 얼굴이 없는 위 34%만 쓴다 — CLUB_SAFE 를 그대로 쓸 것.

python poster_neon.py  →  out/poster/neon_{feed,story}.png
"""
import numpy as np
import cv2
from poster_kit import (BRAND, CLUB, CLUB_SAFE, SIZES, tmask, fit, paint, rule,
                        duotone, outline, glow, logo, grain, save)
from fonts import KR

# ── 여기만 고치면 됨 ───────────────────────────────────────
ROWS   = [('DATE',    '일정 공개 예정'),           # 예: '8월 23일 토요일'
          ('TIME',    '오후 2시 — 밤 10시'),
          ('VENUE',   '장소 추후 공지'),           # 예: '서울 강남'
          ('LINE UP', 'DEMIC · V · LYNN · AROS · TS'),
          ('ENTRY',   '스탠딩 00,000원 · 성비 1:1 · 웰컴드링크 1잔')]
HANDLE = '@BLACKOUTCREW_OFFICIAL'
NOTE   = '예약 · 문의는 DM'
# ──────────────────────────────────────────────────────────

INK  = np.array([0.02, 0.03, 0.03], np.float32)
LIME = np.array([0.55, 1.00, 0.22], np.float32)
CORE = np.array([0.90, 1.00, 0.80], np.float32)   # 관 안쪽. 형광색 그대로 쓰면 안 밝아 보인다
WHT  = np.array([1.00, 1.00, 1.00], np.float32)


def neon(img, m, x, y, V, anchor='l', valign='c', th=None, mirror=None):
    """세 겹으로 튜브를 만든다. mirror 를 주면 그 y 아래로 바닥 반사를 깐다."""
    th = th or max(2, int(3.2 * V))
    o = outline(m, th)
    if mirror is not None:
        f = cv2.GaussianBlur(np.flipud(o).astype(np.float32) / 255.0, (0, 0), 9 * V)
        f = (f * 255).astype(np.uint8)
        h = o.shape[0]
        glow(img, f, x, mirror + h * 0.55, LIME, 0.16, 14 * V, anchor, 'c')
    glow(img, o, x, y, LIME, 0.50, 26 * V, anchor, valign)
    glow(img, o, x, y, LIME, 0.75, 9 * V, anchor, valign)
    paint(img, o, x, y, color=CORE, a=1.0, anchor=anchor, valign=valign)
    return o


def build(W, H, story=False):
    U = H / 1350.0
    V = W / 1080.0
    M = int(W * 0.085)
    iw = W - M * 2

    # 배경 — 사진을 거의 검정까지 눌러 질감만 남긴다
    img = duotone(CLUB, W, H, INK, np.array([0.19, 0.29, 0.21], np.float32),
                  contrast=1.5, keep=0.06, **CLUB_SAFE)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx / W - 0.5) / 0.62) ** 2 + ((yy / H - 0.44) / 0.62) ** 2)
    vig = np.clip(r - 0.35, 0, 1) ** 1.2
    img = img * (1 - vig[..., None] * 0.92) + INK * (vig[..., None] * 0.92)
    img = img * 0.62 + INK * 0.38

    # ── 상단 ──────────────────────────────────────────────
    hy = H * 0.070
    paint(img, logo(int(42 * V)), M, hy, a=0.85)
    paint(img, tmask('BLACKOUT CREW', BRAND, int(16 * V), 0.30),
          M + int(42 * V) + int(16 * V), hy, a=0.75)
    paint(img, tmask('SEOUL', BRAND, int(16 * V), 0.30), W - M, hy, color=LIME, a=0.8, anchor='r')

    # ── 네온 간판 ─────────────────────────────────────────
    t1 = tmask('POOL PARTY', BRAND, fit('POOL PARTY', BRAND, iw, 0.02), 0.02)
    t2 = tmask('SOLO PARTY', BRAND, fit('SOLO PARTY', BRAND, iw, 0.02), 0.02)
    y1 = H * (0.235 if story else 0.250)
    neon(img, t1, M, y1, V, mirror=y1 + t1.shape[0] * 0.62)

    my = y1 + t1.shape[0] / 2 + 96 * U
    xm = tmask('×', BRAND, int(84 * V))
    neon(img, xm, W - M, my, V, anchor='r')
    rule(img, my, M, W - M - xm.shape[1] - int(46 * V), LIME, 0.42, max(1, int(2 * V)))

    y2 = my + t2.shape[0] / 2 + 96 * U
    neon(img, t2, M, y2, V, mirror=y2 + t2.shape[0] * 0.62)

    # ── 정보 — 간판 아래 작게. 여기서 빛나면 간판이 죽는다 ──
    y0 = H * (0.640 if story else 0.660)
    step = H * (0.048 if story else 0.052)
    lx = M + int(W * 0.200)
    for i, (k, v) in enumerate(ROWS):
        y = y0 + step * i
        paint(img, tmask(k, BRAND, int(14 * V), 0.24), M, y, color=LIME, a=0.85)
        paint(img, tmask(v, KR, min(int(24 * V), fit(v, KR, W - M - lx)), 0.01), lx, y, color=WHT, a=0.92)

    # ── 하단 ──────────────────────────────────────────────
    by = H * 0.945
    rule(img, by - 42 * U, M, W - M, LIME, 0.30, max(1, int(1 * V)))
    paint(img, tmask(HANDLE, BRAND, int(17 * V), 0.16), M, by, a=0.88)
    paint(img, tmask(NOTE, KR, int(19 * V), 0.02), W - M, by, color=LIME, a=0.9, anchor='r')

    grain(img, 0.012, 8)
    return np.clip(img, 0, 1)


# import 만 해도 렌더가 도는 걸 막는다 — poster_motion.py 가 build() 를 가져다 쓴다
if __name__ == '__main__':
    for tag, (W, H, story) in SIZES.items():
        save(build(W, H, story), f'neon_{tag}')
