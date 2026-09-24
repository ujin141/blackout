"""
**AFTER MOON 포스터 · 팔로우 이벤트.** 두 계정 팔로우하면 웰컴드링크 1+1.

    python poster_follow.py   →  out/moon/follow_피드.jpg (1080×1350) · follow_스토리.jpg (1080×1920)

## 판

    팔로우하면 / 웰컴드링크 1+1     은색 큰 글. 후크
    @dip_houz  @blackoutcrew_official   두 알약. 이게 할 일이다
    AFTER MOON · 09.26 SAT · 조건 한 줄 · 예매 PARTYMOA

뒤는 딥하우즈 촬영본의 칵테일 컷. 어둡게 눌러 글이 앞에 선다.
색은 사진에만. 글은 검정·은색·흰색.
"""
import os

import numpy as np
from PIL import Image, ImageDraw

from fest_kit import night
from fonts import KR, KRB
from poster_hook import BRAND_FONT, DIM, FAINT, INK, RULE, STRIP, U, font, hh, probe, silver_text, step
from poster_kit import bloom, grain
from poster_moon import ARC_BOT, CTA, CTA_KO, DATE, LEAD, LOGO, OUT, TITLE, tracked, tracked_w
from reel_dh import still

HANDLES = ['@dip_houz', '@blackoutcrew_official']
BG = (1421, 3.0)                    # 칵테일. 빨간 조명에 잔 두 개


def pill(d, x, y, text, f, pad=28):
    w = int(tracked_w(text, f, 0.06)) + pad * 2
    h = hh(text, f) + pad
    d.rounded_rectangle([x, y, x + w, y + h], h // 2, fill=(14, 14, 20, 200), outline=(190, 193, 204, 255), width=2)
    tracked(d, (x + pad, y + pad // 2 - 2), text, f, 0.06, INK)
    return w, h


def build(W, H, top, bot, tag):
    M = int(W * 0.082)
    bg = still(*BG)                                    # 1080×1920
    if H != 1920:
        y0 = (1920 - H) // 2
        bg = bg[y0:y0 + H]
    bg = bg * 0.55
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    bg *= 0.35 + 0.65 * np.exp(-((yy - 0.42) / 0.30) ** 2)     # 위아래는 더 어둡게
    pil = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    fe = font(BRAND_FONT, step(-2))
    tracked(d, (M, top + U * 2), 'BLACKOUT CREW  ×  DIP HOUZ', fe, 0.40, FAINT)
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.17)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    pil.alpha_composite(lg, (W - M - lw, top + U))

    # 아래 정보 높이
    fname, fdate, flead = font(BRAND_FONT, step(1)), font(BRAND_FONT, step(2)), font(KR, step(-1))
    fstrip, fcta, ffoot, fgen = font(KR, step(-1)), font(BRAND_FONT, step(0)), font(KR, step(-2)), font(BRAND_FONT, step(-2))
    lower = (hh(TITLE, fname) + U * 2 + hh(DATE, fdate) + U + hh(LEAD, flead) + U * 4 + 2 + U * 3
             + hh(STRIP, fstrip) + U * 3 + 2 + U * 3 + hh(CTA, fcta))

    # 후크
    col = W - M * 2
    lines = ['팔로우하면', '웰컴드링크', '1+1']
    # 폭과 높이를 같이 잰다. 폭만 맞추면 세 줄이 아래 정보를 덮는다
    fs = font(KR, step(1))
    fp = font(BRAND_FONT, step(1))
    tail = U * 3 + hh('두', fs) + U * 3 + (hh('@', fp) + 28) * 2 + U + U * 3
    avail = (bot - lower - U * 2) - (top + U * 8) - tail
    fh = font(KRB, 40)
    for size in range(300, 40, -2):
        f = font(KRB, size)
        if all(tracked_w(t, f, 0.0) <= col for t in lines) and            sum(hh(t, f) for t in lines) + int(U * 0.4) * 2 <= avail:
            fh = f
            break
    y = top + U * 8
    for t in lines:
        m = silver_text(t, fh, 0.0)
        pil.alpha_composite(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), 'RGBA'), (M, y))
        y += m.shape[0] + int(U * 0.4)
    y += U * 3
    d.text((M, y), '두 계정 팔로우하고 입장할 때 보여 주세요', font=fs, fill=INK)
    y += hh('두', fs) + U * 3

    # 알약 둘. 한 줄에 안 들어가면 두 줄
    x = M
    for hnd in HANDLES:
        w = int(tracked_w(hnd, fp, 0.06)) + 56
        if x + w > W - M:
            x = M
            y += hh(hnd, fp) + 28 + U
        _, h = pill(d, x, y, hnd, fp)
        x += w + U * 2
    y += h + U * 3
    assert y < bot - lower - U * 2, (y, bot - lower)

    # 아래 정보
    y = bot - lower
    tracked(d, (M, y), TITLE, fname, 0.20, INK)
    y += hh(TITLE, fname) + U * 2
    tracked(d, (M, y), DATE, fdate, 0.04, INK)
    y += hh(DATE, fdate) + U
    d.text((M, y), LEAD, font=flead, fill=FAINT)
    y += hh(LEAD, flead) + U * 4
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    d.text((M, y), STRIP, font=fstrip, fill=DIM)
    y += hh(STRIP, fstrip) + U * 3
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    d.text((M, y + (hh(CTA, fcta) - hh(ARC_BOT, fgen)) // 2), ARC_BOT, font=fgen, fill=FAINT)
    wc = tracked_w(CTA, fcta, 0.20)
    wk = probe.textlength(CTA_KO + ' ', font=ffoot)
    d.text((W - M - wc - wk, y + hh(CTA, fcta) - hh(CTA_KO, ffoot)), CTA_KO, font=ffoot, fill=FAINT)
    tracked(d, (W - M - wc, y), CTA, fcta, 0.20, (214, 217, 226, 255))

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
