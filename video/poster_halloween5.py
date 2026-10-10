"""
**BLACKOUT HALLOWEEN @ ZSPOT LOUNGE — 주황판.** 피드 세 장(이어짐).

    python poster_halloween5.py   →  out/halloween/HO1.jpg HO2.jpg HO3.jpg · _할로윈주황격자.jpg

## 왜 주황인가

지금까지 판은 전부 어두웠다(달 · 묘지 · 네온). 피드에서 어두운 판은 다른 파티 포스터 사이에 묻힌다.
**주황 바탕에 검정** — 할로윈의 원래 두 색이다. 스크롤하다 멈추는 건 밝은 칸이다.
그림은 실루엣만 쓴다(호박 · 박쥐 · 흘러내리는 글자). 그리는 대신 오려 낸 모양이라 싸 보이지 않는다.

## 오게 만드는 말을 크게

    HO1   LADIES FREE           여자 무료 · 남자 10,000원
    HO2   검은 호박 · 박쥐        코스튬 파티
    HO3   WELCOME DRINK         생맥 or 데킬라 · ZSPOT LOUNGE
    셋    HALLOWEEN 아홉 자가 세 장을 지나고 아래로 흘러내린다 · 맨 아래 검정 띠 (날짜 · 시간 · 장소)

올리는 순서 HO3 → HO2 → HO1.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from poster_halloween import OUT, bat_points
from poster_halloween3 import ADDR, TIME, VENUE, cond, kr
from poster_kit import grain
from poster_moon import LOGO, fbm, tracked, tracked_w

W, H = 1080, 1350
RW = W * 3
M = 80
OR = (255, 106, 0)
OR_HI = (255, 150, 40)
BK = (14, 10, 12)
DATE = '10.30 FRI'
WORD = 'HALLOWEEN'


def background():
    yy, xx = np.mgrid[0:H, 0:RW].astype(np.float32)
    base = np.float32(OR) / 255
    hi = np.float32(OR_HI) / 255
    glow = np.exp(-((xx - RW / 2) / (RW * 0.45)) ** 2 - ((yy - H * 0.35) / (H * 0.55)) ** 2)
    img = base * (1 - glow[..., None]) + hi * glow[..., None]
    img *= (0.92 + 0.10 * fbm(H, RW, 5, seed=21, base=5))[..., None]
    # 하프톤 점. 아래 모서리에서 짙어진다 — 인쇄물 느낌
    dots = np.zeros((H, RW), np.float32)
    step = 18
    for y in range(0, H, step):
        for x in range((y // step) % 2 * step // 2, RW, step):
            k = np.clip((y / H - 0.55) / 0.45, 0, 1) * (0.5 + 0.5 * abs(np.sin(x / RW * np.pi * 3)))
            r = 1 + 6 * k
            if r > 1.3:
                cv2.circle(dots, (x, y), int(r), 1.0, -1, cv2.LINE_AA)
    img *= (1 - 0.16 * dots[..., None])
    return img


def black_logo(w):
    lg = Image.open(LOGO).convert('RGBA')
    lg = lg.resize((w, max(1, round(lg.height * w / lg.width))), Image.LANCZOS)
    a = lg.getchannel('A')
    out = Image.new('RGBA', lg.size, BK + (0,))
    out.putalpha(a)
    return out


def pumpkin(d, cx, cy, s):
    """검은 호박 실루엣. 얼굴은 주황으로 파낸다."""
    for dx, w, h in ((-0.32, 0.62, 0.86), (0.32, 0.62, 0.86), (-0.14, 0.62, 0.95), (0.14, 0.62, 0.95)):
        d.ellipse([cx + dx * s - w * s / 2, cy - h * s / 2, cx + dx * s + w * s / 2, cy + h * s / 2], fill=BK)
    d.polygon([(cx - s * 0.05, cy - s * 0.42), (cx + s * 0.07, cy - s * 0.42), (cx + s * 0.13, cy - s * 0.66),
               (cx + s * 0.04, cy - s * 0.68)], fill=BK)
    d.ellipse([cx + s * 0.08, cy - s * 0.62, cx + s * 0.34, cy - s * 0.50], fill=BK)
    face = [
        [(cx - s * 0.34, cy - s * 0.02), (cx - s * 0.08, cy - s * 0.02), (cx - s * 0.20, cy - s * 0.24)],
        [(cx + s * 0.34, cy - s * 0.02), (cx + s * 0.08, cy - s * 0.02), (cx + s * 0.20, cy - s * 0.24)],
        [(cx - s * 0.05, cy + s * 0.12), (cx + s * 0.05, cy + s * 0.12), (cx, cy + s * 0.03)],
        [(cx - s * 0.38, cy + s * 0.17)] + [(cx + x * s, cy + s * (0.22 + (0.07 if i % 2 else 0)))
                                           for i, x in enumerate(np.linspace(-0.28, 0.28, 9))]
        + [(cx + s * 0.38, cy + s * 0.17), (cx + s * 0.22, cy + s * 0.37), (cx - s * 0.22, cy + s * 0.37)],
    ]
    for p in face:
        d.polygon(p, fill=OR_HI)


def bats(d, spots):
    for x, y, s, r in spots:
        d.polygon(bat_points(x, y, s, r, 1.0), fill=BK)


def drippy_word(d, y, f, seed=5):
    """HALLOWEEN 아홉 자를 아홉 칸에. 글자 밑에서 검정이 흘러내린다."""
    rng = np.random.default_rng(seed)
    slot = RW / len(WORD)
    bottoms = []
    for i, ch in enumerate(WORD):
        b = d.textbbox((0, 0), ch, font=f)
        x = slot * i + (slot - (b[2] - b[0])) / 2 - b[0]
        d.text((x, y - b[1]), ch, font=f, fill=BK)
        x0, x1 = x + b[0], x + b[2]
        yb = y + (b[3] - b[1])
        bottoms.append(yb)
        for _ in range(int(rng.integers(1, 3))):
            dx = rng.uniform(x0 + 14, x1 - 14)
            L = rng.uniform(30, 105)
            w = rng.uniform(10, 18)
            d.rounded_rectangle([dx - w / 2, yb - 10, dx + w / 2, yb + L], int(w / 2), fill=BK)
            d.ellipse([dx - w * 0.75, yb + L - w * 0.6, dx + w * 0.75, yb + L + w * 0.9], fill=BK)
    return max(bottoms)


def main():
    img = background()
    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    # 머리
    fe = cond(26, 'SemiBold Condensed')
    lg = black_logo(int(W * 0.17))
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, 96), 'BLACKOUT CREW PRESENTS', fe, 0.40, BK)
        pil.alpha_composite(lg, (x0 + W - M - lg.width, 88))

    # HO1 — LADIES FREE
    f1 = cond(210, 'Bold Condensed')
    tracked(d, (M, 170), 'LADIES', f1, 0.02, BK)
    tracked(d, (M, 380), 'FREE', f1, 0.02, BK)
    # 'FREE' 옆 동그란 도장
    cx, cy, r = M + tracked_w('FREE', f1, 0.02) + 130, 520, 108
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BK)
    ft = kr(46)
    for i, line in enumerate(('여자', '무료')):
        tw_ = d.textlength(line, font=ft)
        d.text((cx - tw_ / 2, cy - 52 + i * 54), line, font=ft, fill=OR_HI)
    d.text((M, 640), '남자 10,000원', font=kr(54), fill=BK)

    # HO2 — 호박 · 박쥐 · 코스튬
    pumpkin(d, W + W // 2, 420, 470)
    bats(d, [(W + 150, 230, 66, -0.2), (W + 900, 200, 80, 0.15), (W + 960, 360, 46, 0.25),
             (W - 160, 300, 40, 0.1), (2 * W + 900, 520, 52, -0.15), (W + 90, 520, 34, 0.2)])
    fc = cond(70, 'Bold Condensed')
    t = 'COSTUME PARTY'
    tracked(d, (W + (W - tracked_w(t, fc, 0.10)) / 2, 660), t, fc, 0.10, BK)

    # HO3 — WELCOME DRINK
    x3 = 2 * W + M
    f3 = cond(150, 'Bold Condensed')
    tracked(d, (x3, 170), 'WELCOME', f3, 0.02, BK)
    tracked(d, (x3, 320), 'DRINK', f3, 0.02, BK)
    d.text((x3, 490), '생맥 or 데킬라', font=kr(64), fill=BK)
    d.text((x3, 580), '둘 중 하나 골라요', font=kr(38, bold=False), fill=BK)

    # HALLOWEEN
    slot = RW / len(WORD)
    for s in range(520, 60, -4):
        fw = cond(s, 'Bold Condensed')
        bb = d.textbbox((0, 0), 'H', font=fw)
        if max(d.textlength(ch, font=fw) for ch in WORD) <= slot * 0.78 and bb[3] - bb[1] <= 300:
            break
    yb = drippy_word(d, 740, fw)

    # 아래 띠
    by = H - 150
    d.rectangle([0, by, RW, H], fill=BK)
    fd = cond(88, 'Bold Condensed')
    tracked(d, (M, by + 30), DATE, fd, 0.04, OR_HI)
    tracked(d, (W + (W - tracked_w(TIME, fd, 0.04)) / 2, by + 30), TIME, fd, 0.04, OR_HI)
    fv = cond(64, 'Bold Condensed')
    tracked(d, (2 * W + W - M - tracked_w(VENUE + ' B1', fv, 0.04), by + 22), VENUE + ' B1', fv, 0.04, OR_HI)
    fa = kr(30, bold=False)
    a = ADDR.replace('B1 · ', '')
    d.text((2 * W + W - M - d.textlength(a, font=fa), by + 98), a, font=fa, fill=OR_HI)
    assert yb + 125 < by, (yb, by)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    grain(out, 0.018)
    big = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    tiles = []
    for c in range(3):
        t_ = big.crop((c * W, 0, (c + 1) * W, H))
        t_.save(os.path.join(OUT, f'HO{c + 1}.jpg'), quality=95)
        tiles.append(t_)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t_ in enumerate(tiles):
        g.paste(t_, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(os.path.join(OUT, '_할로윈주황격자.jpg'), quality=92)
    print('완료: HO1 HO2 HO3')


if __name__ == '__main__':
    main()
