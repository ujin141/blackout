"""
**AFTER MOON · 팔로우 쿠폰.** 두 계정 팔로우하면 웰컴드링크 1+1.

    python poster_follow.py   →  out/moon/follow_피드.jpg (1080×1350) · follow_스토리.jpg (1080×1920)

## 왜 쿠폰 모양인가

"팔로우하면 드려요" 는 광고다. **쿠폰은 내 것**이다. 절취선·톱니·바코드·
일련번호가 붙는 순간 저장하고 싶어지고, 저장하면 입장할 때 꺼낸다.

    위 칸    WELCOME DRINK · 1+1 (은색 크게) · 팔로우하면 한 잔 더
    절취선   톱니 두 개 + 점선
    아래 칸  @dip_houz @blackoutcrew_official · 바코드 · 일련번호 · 9.26 당일만

뒤는 딥하우즈 칵테일 컷을 흐려서 깐다. 카드는 검정에 은테. 색은 뒤 사진에만.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import night
from fonts import KR, KRB
from poster_hook import BRAND_FONT, DIM, FAINT, INK, U, font, hh, probe, silver_text, step
from poster_kit import bloom, grain
from poster_moon import CTA, CTA_KO, DATE, LOGO, OUT, TITLE, tracked, tracked_w
from reel_dh import still

HANDLES = ['@dip_houz', '@blackoutcrew_official']
BG = (1421, 3.0)
SILVER = (196, 199, 210, 255)
CARD = (12, 12, 18, 242)
SERIAL = 'NO. 0926-1+1'


def barcode(d, x, y, w, h, seed=926):
    rng = np.random.default_rng(seed)
    cx = x
    while cx < x + w:
        bw = int(rng.choice([2, 3, 4, 6, 8], p=[.3, .3, .2, .12, .08]))
        if rng.random() < 0.55:
            d.rectangle([cx, y, cx + bw - 1, y + h], fill=SILVER)
        cx += bw


def pill(d, x, y, text, f, pad=26):
    w = int(tracked_w(text, f, 0.06)) + pad * 2
    h = hh(text, f) + pad
    # RGBA 에 반투명으로 그리면 나중에 RGB 로 바꿀 때 알파가 버려져 흰 판이 된다. 불투명으로
    d.rounded_rectangle([x, y, x + w, y + h], h // 2, fill=(30, 30, 40, 255), outline=SILVER, width=2)
    tracked(d, (x + pad, y + pad // 2 - 2), text, f, 0.06, INK)
    return w, h


def build(W, H, top, bot, tag):
    M = int(W * 0.082)
    bg = still(*BG)
    if H != 1920:
        y0 = (1920 - H) // 2
        bg = bg[y0:y0 + H]
    bg = cv2.GaussianBlur(bg, (0, 0), 22) * 0.55
    pil = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).convert('RGBA')

    # ── 카드
    cx0, cx1 = M, W - M
    cy0, cy1 = top + U * 5, bot - U * 3
    card = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([cx0, cy0, cx1, cy1], 44, fill=CARD, outline=SILVER, width=3)
    # 절취선. 카드 높이의 58% 자리. 양옆 톱니는 배경이 보이게 뚫는다
    ty = cy0 + int((cy1 - cy0) * 0.54)
    for x in (cx0, cx1):
        d.ellipse([x - 26, ty - 26, x + 26, ty + 26], fill=(0, 0, 0, 0))
    pil.alpha_composite(card)
    d = ImageDraw.Draw(pil)
    for x in (cx0, cx1):
        d.arc([x - 26, ty - 26, x + 26, ty + 26], 0, 360, fill=SILVER, width=3)
    x = cx0 + 40
    while x < cx1 - 40:
        d.line([(x, ty), (x + 14, ty)], fill=(120, 124, 138, 255), width=2)
        x += 26
    # 톱니 밖 배경을 다시 덮어 원이 뚫린 것처럼
    hole = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    mask = Image.new('L', (W, H), 0)
    md = ImageDraw.Draw(mask)
    for x in (cx0, cx1):
        md.ellipse([x - 24, ty - 24, x + 24, ty + 24], fill=255)
    pil.paste(hole, (0, 0), mask)
    d = ImageDraw.Draw(pil)

    P = 56                                             # 카드 안쪽 여백
    # ── 위 칸
    fe = font(BRAND_FONT, step(-1))
    tracked(d, (cx0 + P, cy0 + P), 'WELCOME DRINK COUPON', fe, 0.36, DIM)
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.16)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    pil.alpha_composite(lg, (cx1 - P - lw, cy0 + P - 6))
    d = ImageDraw.Draw(pil)

    room = ty - (cy0 + P + hh('W', fe) + U * 2) - U * 4
    big = silver_text('1+1', font(KRB, 40), 0.0)
    for size in range(420, 60, -4):
        m = silver_text('1+1', font(KRB, size), -0.02)
        sub_h = hh('팔', font(KRB, step(3))) + U
        if m.shape[0] + sub_h + U * 3 <= room and m.shape[1] <= cx1 - cx0 - P * 2:
            big = m
            break
    y = cy0 + P + hh('W', fe) + U * 3
    pil.alpha_composite(Image.fromarray((np.clip(big, 0, 1) * 255).astype(np.uint8), 'RGBA'), (cx0 + P, y))
    d = ImageDraw.Draw(pil)
    y += big.shape[0] + U
    f3 = font(KRB, step(3))
    d.text((cx0 + P, y), '팔로우하면 웰컴드링크 한 잔 더', font=f3, fill=INK)
    y += hh('팔', f3) + U
    d.text((cx0 + P, y), '두 계정 다 팔로우하고 입장할 때 보여 주세요', font=font(KR, step(0)), fill=DIM)

    # ── 아래 칸
    y = ty + U * 4
    fp = font(BRAND_FONT, step(0))
    x = cx0 + P
    for hnd in HANDLES:
        w = int(tracked_w(hnd, fp, 0.06)) + 52
        if x + w > cx1 - P:
            x = cx0 + P
            y += hh(hnd, fp) + 26 + U
        _, h = pill(d, x, y, hnd, fp)
        x += w + U
    y += h + U * 3

    # 바코드 왼쪽, 정보 오른쪽
    bh = 88
    bw = int((cx1 - cx0 - P * 2) * 0.46)
    barcode(d, cx0 + P, y, bw, bh)
    fs = font(BRAND_FONT, step(-2))
    tracked(d, (cx0 + P, y + bh + U), SERIAL, fs, 0.20, FAINT)
    rx = cx0 + P + bw + U * 3
    fn, fd = font(BRAND_FONT, step(1)), font(BRAND_FONT, step(0))
    tracked(d, (rx, y), TITLE, fn, 0.16, INK)
    tracked(d, (rx, y + hh(TITLE, fn) + U), DATE, fd, 0.06, INK)
    d.text((rx, y + hh(TITLE, fn) + U + hh(DATE, fd) + U), '압구정 딥하우즈 · 22:00', font=font(KR, step(-1)), fill=DIM)
    y += bh + U + hh('0', fs) + U * 3

    # 맨 아래 한 줄. 당일만 · 예매
    fk = font(KR, step(-1))
    d.text((cx0 + P, cy1 - P - hh('9', fk)), '9.26 당일 · 1인 1회 · 웰컴샷과 별개', font=fk, fill=FAINT)
    fc, ff = font(BRAND_FONT, step(0)), font(KR, step(-2))
    wc = tracked_w(CTA, fc, 0.20)
    wk = probe.textlength(CTA_KO + ' ', font=ff)
    yy = cy1 - P - hh(CTA, fc)
    d.text((cx1 - P - wc - wk, yy + hh(CTA, fc) - hh(CTA_KO, ff)), CTA_KO, font=ff, fill=FAINT)
    tracked(d, (cx1 - P - wc, yy), CTA, fc, 0.20, SILVER)
    assert y < yy - U, (y, yy)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    bloom(out, 0.60, W * 0.020, 0.30)
    grain(out, 0.010)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(
        os.path.join(OUT, f'{tag}.jpg'), quality=94)
    night(out, tag)


def main():
    build(1080, 1350, 90, 1266, 'follow_피드')
    build(1080, 1920, 280, 1600, 'follow_스토리')
    print('완료:', OUT)


if __name__ == '__main__':
    main()
