"""
모집 현황 줄판 — 세 칸으로 그리드 한 줄을 채운다.

    │ 남은 자리 │ 차수 표 │ 정보 · 예약 │

**차수가 넘어갈 때마다 다시 올리는 줄이다.** `event.py` 의 WAVES 만 고치면
숫자·문구·막대가 다 따라온다 — 한 줄을 통째로 갈아 끼우면 그리드가 안 어긋난다.

칸마다 다른 사진을 쓴다. 한 장을 3.2:1 로 늘리면 인물이 가운데 칸에만 남고
양옆은 빈 물이 된다 — 4:5 는 세로 사진에 원래 맞는 비율이라 크롭도 안 아깝다.

**막대는 1칸에 둔다.** 제일 먼저 보이는 칸에 "얼마나 찼는지" 가 있어야
나머지 두 칸을 볼 이유가 생긴다. 표를 먼저 보여 주면 그냥 안내문이다.

이음새(x=1080, 2160)에는 아무것도 안 올린다. 올리는 순서는 3칸 → 2칸 → 1칸.

⚠ 브랜드 흑백 규칙 예외(컬러). 행사 모객용이고 포스터와 같은 톤을 쓴다.

python feed_wave.py  →  out/feed_event/wave_{1,2,3}.png · wave_full.png
"""
import os
import numpy as np
from PIL import Image
from poster_kit import (BRAND, HEROES, tmask, tmask_bl, fit, paint, paint_bl,
                        rule, box, duotone, grain)
from fest_kit import justify, vignette
from fonts import KR, KRB
import event as EV

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'feed_event')
os.makedirs(OUT, exist_ok=True)

TW, TH = 1080, 1350
W, H = TW * 3, TH
SAFE_T = 135
SEAM = 90

# 칸마다 다른 사진. 자리는 얼굴이 아니라 몸
TILES = [(HEROES[0][0], dict(focus=0.52, zoom=1.05)),
         (HEROES[1][0], dict(focus=0.50, zoom=1.05)),
         (HEROES[2][0], dict(focus=0.50, zoom=1.05))]

DEEP = np.float32([0.016, 0.034, 0.054])
LIT = np.float32([0.340, 0.520, 0.610])
PAPER = np.float32([0.98, 0.99, 1.00])
AQUA = np.float32([0.32, 0.92, 1.00])
CORAL = np.float32([1.00, 0.42, 0.38])
DIM = np.float32([0.58, 0.70, 0.78])


def build():
    parts = [duotone(p, TW, H, DEEP, LIT, contrast=1.16, keep=0.22, **c) for p, c in TILES]
    img = np.concatenate(parts, axis=1)
    img *= 0.44
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    xx = np.arange(W, dtype=np.float32)[None, :, None]
    for c in range(3):
        img *= 1 - 0.44 * np.exp(-((xx - (c + 0.5) * TW) / (TW * 0.60)) ** 2)
    img *= 1 - 0.60 * np.clip((yy - 1050) / 130, 0, 1)      # 발치

    # ── 1칸 · 남은 자리 ───────────────────────────────────
    paint(img, tmask('BLACKOUT CREW  ·  SEOUL', BRAND, 18, 0.42), TW / 2, SAFE_T + 30,
          color=DIM, a=0.85, anchor='c')
    ns = fit(EV.NAME, BRAND, TW - SEAM * 2, 0.09)
    paint(img, tmask(EV.NAME, BRAND, min(64, ns), 0.09), TW / 2, 300, color=PAPER, anchor='c')

    head = (f'{EV.OPEN_WAVE[0]} {EV.OPEN_LEFT}자리' if EV.OPEN_WAVE else '사전예약 마감')
    paint(img, tmask(head, KRB, min(112, fit(head, KRB, TW - SEAM * 2, 0.02)), 0.02),
          TW / 2, 500, color=PAPER, anchor='c')
    paint(img, tmask('남았습니다' if EV.OPEN_WAVE else '', KRB, 40, 0.02), TW / 2, 590,
          color=PAPER, a=0.92, anchor='c')
    if EV.OPEN_WAVE:
        paint(img, tmask(f'{EV.OPEN_WAVE[0]} 마감  {EV.OPEN_WAVE[3]}', KRB, 30, 0.02),
              TW / 2, 672, color=CORAL, anchor='c')

    # 막대 — **제일 먼저 보이는 칸에 둔다**
    by, bh = 790, 20
    box(img, SEAM, by - bh / 2, TW - SEAM, by + bh / 2, PAPER, 0.14)
    done = (TW - SEAM * 2) * (EV.DONE / max(EV.CAP, 1))
    box(img, SEAM, by - bh / 2, SEAM + done, by + bh / 2, CORAL, 0.95)
    nm = tmask_bl(f'{EV.DONE} / {EV.CAP}', BRAND, 22, 0.16)
    paint_bl(img, nm, SEAM, by + 48, color=PAPER, a=0.95)
    paint_bl(img, tmask_bl('명 예약', KR, 18, 0.02), SEAM + nm[0].shape[1] + 12, by + 48,
             color=DIM, a=0.85)

    # ── 2칸 · 차수 표 ─────────────────────────────────────
    x0 = TW
    paint(img, tmask('사전예약 모집 차수', KRB, 40, 0.02), x0 + TW / 2, SAFE_T + 90,
          color=PAPER, anchor='c')
    y, step = 450, 130
    for name, cap, got, due in EV.WAVES:
        full = got >= cap
        opening = (not full) and got > 0
        col = DIM if full else PAPER
        acc = CORAL if opening else (DIM if full else AQUA)
        box(img, x0 + SEAM, y, x0 + SEAM + 7, y + 78, acc, 0.95 if opening else 0.45)
        paint_bl(img, tmask_bl(name, KRB, 38, 0.02), x0 + SEAM + 32, y + 46,
                 color=col, a=1.0 if not full else 0.60)
        paint_bl(img, tmask_bl(f'{got} / {cap}명', KR, 32, 0.02), x0 + TW * 0.34, y + 46,
                 color=col, a=1.0 if not full else 0.60)
        tag = '마감' if full else (f'{cap - got}자리' if opening else '오픈 예정')
        paint_bl(img, tmask_bl(tag, KRB, 28, 0.02), x0 + TW - SEAM, y + 46,
                 color=acc, a=0.75 if full else 1.0, anchor='r')
        paint_bl(img, tmask_bl(f'마감 {due}', KR, 21, 0.02), x0 + SEAM + 32, y + 84,
                 color=col, a=0.72 if not full else 0.45)
        rule(img, y + 106, x0 + SEAM, x0 + TW - SEAM, PAPER, 0.10, 1)
        y += step

    # ── 3칸 · 정보 · 예약 ─────────────────────────────────
    x0 = TW * 2
    paint(img, tmask(EV.LINEUP_STR, BRAND,
                     int(justify(EV.LINEUP_STR, TW - SEAM * 2, 0.12)), 0.12),
          x0 + TW / 2, SAFE_T + 60, color=PAPER, a=0.94, anchor='c')
    y = 400
    for k, v in (('DATE', EV.DATE_EN), ('OPEN', EV.TIME_EN), ('VENUE', EV.VENUE),
                 ('ENTRY', EV.ENTRY), ('AFTER', EV.AFTER), ('NOTICE', EV.AGE)):
        paint_bl(img, tmask_bl(k, BRAND, 16, 0.24), x0 + SEAM, y, color=AQUA, a=0.95)
        paint_bl(img, tmask_bl(v, BRAND if v.isascii() else KR, 20,
                               0.14 if v.isascii() else 0.01),
                 x0 + SEAM + 140, y, color=PAPER, a=0.98)
        y += 44
    paint_bl(img, tmask_bl(EV.ADDR, KR, 17, 0.01), x0 + SEAM + 140, y - 8,
             color=DIM, a=0.85)
    paint(img, tmask('예약 · 프로필 링크', KRB, 40, 0.02), x0 + TW / 2, 880,
          color=CORAL, anchor='c')
    paint(img, tmask('사전예매만 받습니다', KR, 24, 0.02), x0 + TW / 2, 936,
          color=PAPER, a=0.88, anchor='c')

    # ── 발치 — 칸마다 한 줄 ───────────────────────────────
    FY = 1130
    rule(img, FY - 44, SEAM, W - SEAM, PAPER, 0.14, 1)
    paint(img, tmask(EV.DATE_EN, BRAND, 30, 0.20), TW / 2, FY, color=PAPER, anchor='c')
    paint(img, tmask(EV.TAGLINE, KR, 24, 0.02), TW * 1.5, FY, color=PAPER, a=0.94, anchor='c')
    paint(img, tmask(EV.HANDLE, BRAND, 22, 0.24), TW * 2.5, FY, color=PAPER, a=0.92, anchor='c')
    paint(img, tmask(EV.PARTNERS_STR, BRAND,
                     min(13, fit(EV.PARTNERS_STR, BRAND, TW - SEAM * 2, 0.16)), 0.16),
          TW / 2, FY + 46, color=DIM, a=0.62, anchor='c')
    paint(img, tmask(EV.RULES, KR, 13, 0.01), TW * 1.5, FY + 46, color=DIM, a=0.62, anchor='c')
    paint(img, tmask(f'{EV.VENUE}  ·  {EV.ADDR}', KR, 17, 0.01), TW * 2.5, FY + 46,
          color=DIM, a=0.80, anchor='c')

    # **비네트는 칸마다 따로 건다.** 전체에 걸면 양 끝 칸 바깥만 그늘진다
    for c in range(3):
        vignette(img[:, c * TW:(c + 1) * TW], 0.22, 2.4)
    grain(img, 0.006, 41)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    full = Image.fromarray((build() * 255).astype(np.uint8))
    full.save(os.path.join(OUT, 'wave_full.png'), optimize=True)
    for i in range(3):
        p = os.path.join(OUT, f'wave_{i + 1}.png')
        full.crop((i * TW, 0, (i + 1) * TW, TH)).save(p, optimize=True)
        print(p)
    print('\n올리는 순서: 3칸 → 2칸 → 1칸')
