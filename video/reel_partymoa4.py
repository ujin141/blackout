"""
**파티모아 · 자리 한 줄.** 릴스 하나 + 피드 둘. 지금 남은 자리로.

    python reel_partymoa4.py   →  out/partymoa/K_자리.mp4   (릴스 12초, 곡 있음)
                                  out/partymoa/KC.jpg       (릴스 커버 1080×1920)
                                  out/partymoa/K1.jpg K2.jpg (피드 1080×1350)
                                  out/partymoa/_자리격자.jpg

## 숫자는 앱에서

정원 30 · 예매 6 · 남은 24 · 여 13 · 남 11 — 오늘(9.17) 파티모아 파티
화면에 있는 값 그대로. 올리기 전에 앱 잔여를 한 번 더 보고, 달라졌으면
아래 상수만 고쳐 다시 뽑는다. 숫자를 지어내지 않는다.

## 셋을 잇는 것

**자리 서른 개**가 세 칸을 가로지른다. 한 칸에 열 개. 찬 자리는 노랑,
빈 자리는 흰 테두리. 커버 칸에서 여섯이 차 있고 나머지 두 칸은 비어 있다 —
그게 "24자리 남았어요" 를 말보다 먼저 보여 준다.

    커버   24자리 남았어요        D-9 · 9.26 토
    K1     여 13 · 남 11          남녀 15:15 · 한쪽 차면 그쪽부터 마감
    K2     9,900원                웰컴샷 · 입금 24시간 · QR

올리는 순서 K2 → K1 → 릴스. 격자 새 글이 왼쪽 위.

## 릴스

"지금 24자리 남았어요" → 서른 칸 격자에 여섯이 하나씩 켜진다 → 24 →
여 13 / 남 11 막대 → 파티 정보 → 예매는 앱에서. 개러지 132.
"""
import os

import numpy as np
from PIL import Image, ImageDraw

from feed_partymoa import ACCENT, BRAND, DEEP, WHITE, font
from feed_partymoa9 import cta_plate, head
from fonts import KR, KRB
from qr import build as qr_build
from reel_partymoa import (FPS, H, NF, OUT, SAFE_TOP, SUB, U, W,
                           encode, end_card, fade, finish, fit_text, logo_rgba,
                           pop, purple_bg, put, symbol_bg, text)
from reel_somesoul import footer, logo_line

PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'
BGM = 'bgm_garage.wav'

# ── 앱 숫자 (9.17 기준). 바뀌면 여기만 ──
CAP = 30
BOOKED = 6
LEFT_F, LEFT_M = 13, 11
DDAY = 'D-9'
LEFT = CAP - BOOKED
assert LEFT == LEFT_F + LEFT_M, '남녀 잔여 합이 전체 잔여와 다르다'

PURPLE = np.float32(BRAND) / 255
DEEPC = np.float32(DEEP) / 255
FH = 1350
BAND_Y = (H - FH) // 2
LY = int(FH * 0.60)                  # 자리 줄. 앞 줄들의 노란 선 자리
M = 84


def seat(d, cx, cy, s, on):
    """자리 하나. 찬 건 노랑, 빈 건 흰 테두리."""
    box = [cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2]
    if on:
        d.rounded_rectangle(box, 12, fill=ACCENT)
    else:
        d.rounded_rectangle(box, 12, fill=WHITE + (38,), outline=WHITE + (230,), width=3)


def row_sheet():
    RW = W * 3
    yy = np.linspace(0, 1, FH, dtype=np.float32)[:, None, None]
    a = PURPLE * (1 - yy ** 1.4) + DEEPC * (yy ** 1.4)
    a = np.repeat(a, RW, axis=1)
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    d.line([(M, int(FH * 0.86)), (RW - M, int(FH * 0.86))], fill=WHITE + (110,), width=2)
    # 자리 서른 개. 칸마다 열 개, 세 칸을 잇는 가는 선 위에
    d.line([(0, LY), (RW, LY)], fill=WHITE + (90,), width=2)
    pitch = (W - M * 2) / 10
    for i in range(CAP):
        c, k = divmod(i, 10)
        cx = c * W + M + pitch * (k + 0.5)
        seat(d, cx, LY, 58, i < BOOKED)
    return pil


def legend(d, y):
    f = font(KR, 28)
    seat(d, M + 14, y + 16, 28, True)
    a = f'예매 {BOOKED}'
    d.text((M + 44, y), a, font=f, fill=WHITE + (220,))
    x = M + 44 + d.textlength(a, font=f) + 40
    seat(d, x + 14, y + 16, 28, False)
    d.text((x + 44, y), f'남은 자리 {LEFT}', font=f, fill=WHITE + (220,))


def bullets(d, y, lines):
    fs = font(KRB, 38)
    for k, line in enumerate(lines):
        yy = y + 24 + k * 54
        d.ellipse([M, yy + 12, M + 16, yy + 28], fill=ACCENT)
        d.text((M + 34, yy), line, font=fs, fill=WHITE)
    return yy + 44


def feeds():
    sheet = row_sheet()
    tiles = {}
    cta_y = int(FH * 0.86) - 92 - 48

    # ── 커버 (칸 0)
    b = sheet.crop((0, 0, W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, [f'{LEFT}자리', '남았어요'], f'AFTER MOON · 9.26 토 · {DDAY}', 140, 240)
    assert y + 40 < LY - 40
    d.polygon([(M, LY + 60), (M, LY + 112), (M + 44, LY + 86)], fill=ACCENT)
    d.text((M + 64, LY + 64), '릴스 · 12초', font=font(KR, 34), fill=WHITE + (220,))
    cta_plate(d, '예매 → 프로필 링크', cta_y)
    footer(d, 0)
    full = Image.new('RGB', (W, H), DEEP)
    full.paste(b.convert('RGB'), (0, BAND_Y))
    full.save(os.path.join(OUT, 'KC.jpg'), quality=94)
    tiles['KC'] = b.convert('RGB')

    # ── K1 (칸 1). 남녀
    b = sheet.crop((W, 0, 2 * W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, [f'여 {LEFT_F}자리', f'남 {LEFT_M}자리'], '남녀 15 : 15 · 한쪽 차면 그쪽부터 마감', 140, 240)
    yb = bullets(d, y, ('9.26 토 22:00 – 02:10', '압구정 딥하우즈', 'BHO · LYNN · LII · AROS · TS'))
    assert yb < LY - 40, (yb, LY)
    legend(d, LY + 64)
    cta_plate(d, '잔여 보기 → 프로필 링크', cta_y)
    footer(d, 0)
    b.convert('RGB').save(os.path.join(OUT, 'K1.jpg'), quality=94)
    tiles['K1'] = b.convert('RGB')

    # ── K2 (칸 2). 값 + QR
    b = sheet.crop((2 * W, 0, 3 * W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, ['9,900원'], '웰컴샷 포함 · 남녀 같은 값', 150, 300)
    yb = bullets(d, y, ('신청하고 24시간 안에 입금', '안 하면 자리는 자동으로 풀려요', '혼자 와도 돼요 · 1인 참여 환영'))
    assert yb < LY - 40, (yb, LY)
    qs, pad = 150, 12
    q = qr_build(PARTY_URL, 150, [0.08, 0.04, 0.24], [1.0, 1.0, 1.0], badge=False, error='m')
    q = q.resize((qs, qs), Image.NEAREST).convert('RGBA')
    box = Image.new('RGBA', (qs + pad * 2, qs + pad * 2), (255, 255, 255, 255))
    box.paste(q, (pad, pad))
    qy = 1090 - qs - pad * 2 - U * 2
    assert qy > LY + 40
    b.alpha_composite(box, (W - M - qs - pad * 2, qy))
    cap = '카메라로 찍으면 예매'
    d.text((W - M - qs - pad * 2 - 12 - d.textlength(cap, font=font(KR, 26)),
            qy + pad + qs / 2 - 16), cap, font=font(KR, 26), fill=WHITE)
    cta_plate(d, 'App Store · 파티모아', cta_y)
    footer(d, 0)
    b.convert('RGB').save(os.path.join(OUT, 'K2.jpg'), quality=94)
    tiles['K2'] = b.convert('RGB')

    g = Image.new('RGB', (W * 3 + 16, FH * 2 + 8), (255, 255, 255))
    for i, k in enumerate(('KC', 'K1', 'K2')):
        g.paste(tiles[k], (i * (W + 8), 0))
    for i, k in enumerate(('TC', 'T1', 'T2')):
        p = os.path.join(OUT, f'{k}.jpg')
        if os.path.exists(p):
            im = Image.open(p)
            if im.height == H:
                im = im.crop((0, BAND_Y, W, BAND_Y + FH))
            g.paste(im, (i * (W + 8), FH + 8))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_자리격자.jpg'), quality=92)
    print('피드 완료: KC K1 K2')


# ── 릴스 ──────────────────────────────────────────────

GRID_ON = [2, 7, 13, 16, 22, 27]        # 격자에서 켜지는 자리. 흩어져 보이게
COLS, ROWS, SS, GAP = 6, 5, 104, 30


def grid_rgba(n_on, k_last=1.0):
    """6×5 자리 격자. n_on 개가 켜져 있고 마지막 하나는 k_last 로 커지는 중."""
    gw = COLS * SS + (COLS - 1) * GAP
    gh = ROWS * SS + (ROWS - 1) * GAP
    im = Image.new('RGBA', (gw + 40, gh + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    on = set(GRID_ON[:n_on])
    for i in range(CAP):
        r, c = divmod(i, COLS)
        cx = 20 + c * (SS + GAP) + SS / 2
        cy = 20 + r * (SS + GAP) + SS / 2
        s = SS
        if n_on and i == GRID_ON[n_on - 1]:
            s = SS * (1.25 - 0.25 * k_last)
        seat(d, cx, cy, s, i in on)
    return np.asarray(im, np.float32) / 255.0


def bar_rgba(label, left, cap, w=W - M * 2):
    """남녀 막대. 남은 만큼 노랑."""
    im = Image.new('RGBA', (w, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, 0), label, font=font(KRB, 44), fill=WHITE)
    r = f'{left}자리 남음'
    d.text((w - d.textlength(r, font=font(KR, 36)), 6), r, font=font(KR, 36), fill=WHITE + (220,))
    d.rounded_rectangle([0, 80, w, 130], 25, fill=WHITE + (50,))
    d.rounded_rectangle([0, 80, w * left / cap, 130], 25, fill=ACCENT)
    return np.asarray(im, np.float32) / 255.0


def reel():
    bg = purple_bg()
    symbol_bg(bg, 0.06, 0.45, 1.0)
    lg = logo_rgba(36)
    t_grid, t_split, t_info, t_end = 1.9, 6.2, 8.5, 10.4
    step = 0.28
    t_full = t_grid + BOOKED * step + 0.3
    h1 = fit_text('지금', KRB, W - M * 2, 150)
    h2 = fit_text(f'{LEFT}자리', KRB, W - M * 2, 190, ACCENT + (255,))
    h3 = fit_text('남았어요', KRB, W - M * 2, 150)
    cnt = [text(f'{n} / {CAP}', KRB, 64) for n in range(BOOKED + 1)]
    left_big = text(str(LEFT), KRB, 300, ACCENT + (255,))
    left_sub = text('자리 남았어요', KRB, 60)
    sp1 = fit_text('남녀 따로 세요', KRB, W - M * 2, 110)
    sp2 = text('한쪽 차면 그쪽부터 마감', KR, 40, SUB)
    bf = bar_rgba(f'여 {LEFT_F}', LEFT_F, 15)
    bm = bar_rgba(f'남 {LEFT_M}', LEFT_M, 15)
    n1 = fit_text('AFTER MOON', KRB, W - M * 2, 130)
    n2 = text('9.26 토 22:00 – 02:10 · 압구정 딥하우즈', KRB, 44)
    n3 = text('9,900원 · 웰컴샷 · 1인 참여 환영', KR, 38, SUB)
    n4 = text(DDAY, KRB, 120, ACCENT + (255,))

    def frames():
        for i in range(NF):
            t = i / FPS
            img = bg.copy()
            if t < t_grid:
                pop(img, h1, W / 2, H * 0.40, t, 0.0, 0.3)
                pop(img, h2, W / 2, H * 0.40 + 170, t, 0.25, 0.35)
                pop(img, h3, W / 2, H * 0.40 + 330, t, 0.5, 0.3)
            elif t < t_split:
                tt = t - t_grid
                n_on = min(BOOKED, int(tt / step) + 1)
                k_last = min(1.0, (tt - (n_on - 1) * step) / step)
                g = grid_rgba(n_on, k_last)
                put(img, g, (W - g.shape[1]) / 2, H * 0.30, fade(t, t_grid, 0.3))
                c = cnt[n_on]
                put(img, c, (W - c.shape[1]) / 2, H * 0.30 + g.shape[0] + 40, fade(t, t_grid, 0.3))
                if t >= t_full:
                    img *= 1 - 0.55 * fade(t, t_full, 0.3)
                    pop(img, left_big, W / 2, H * 0.46, t, t_full, 0.4)
                    put(img, left_sub, (W - left_sub.shape[1]) / 2, H * 0.46 + 170, fade(t, t_full + 0.15))
            elif t < t_info:
                pop(img, sp1, W / 2, H * 0.30, t, t_split, 0.35)
                put(img, sp2, (W - sp2.shape[1]) / 2, H * 0.30 + 90, fade(t, t_split + 0.2))
                put(img, bf, M, H * 0.46, fade(t, t_split + 0.3))
                put(img, bm, M, H * 0.46 + 200, fade(t, t_split + 0.55))
            else:
                if t < t_end:
                    pop(img, n4, W / 2, H * 0.30, t, t_info, 0.35)
                    pop(img, n1, W / 2, H * 0.30 + 150, t, t_info + 0.1, 0.35)
                    put(img, n2, (W - n2.shape[1]) / 2, H * 0.30 + 250, fade(t, t_info + 0.3))
                    put(img, n3, (W - n3.shape[1]) / 2, H * 0.30 + 320, fade(t, t_info + 0.45))
            put(img, lg, M, SAFE_TOP + U * 4)
            end_card(img, t, t_end)
            yield finish(img)

    encode('K_자리', frames(), BGM)


if __name__ == '__main__':
    feeds()
    reel()
