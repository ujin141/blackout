"""
**BLACKOUT HALLOWEEN 스토리 — 다시 그린 판.**

    python poster_halloween6.py   →  out/halloween/HO_스토리.jpg (1080×1920)

## 앞 판이 싸 보인 이유

주황 한 장에 검은 실루엣 — 깊이가 없었다. 앞뒤가 없으니 스티커를 붙인 종이로 보였다.
이 판은 겹을 쌓는다.

    하늘      위는 보라 밤, 아래로 갈수록 노을 주황. 피드의 주황과 이어진다
    달        크고 밝은 보름달. 박쥐가 그 앞을 지난다 — 실루엣은 밝은 데 앞에서만 산다
    호박      입체로 칠한다. 골마다 명암, 위에 반사, 테두리는 어둡게.
              얼굴은 **안에서 불이 켜진 것처럼** — 파낸 테두리는 어둡고, 안쪽은 노랗게 타고, 빛이 번진다
    바닥      묘지 실루엣과 안개. 인스타 답장 바가 덮는 자리라 글은 두지 않는다

값은 안 쓴다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import sky
from poster_halloween import OUT, bat_points
from poster_halloween3 import ADDR, TIME, VENUE, cond, kr
from poster_kit import bloom, grain
from poster_moon import LOGO, fbm, tracked, tracked_w

W, H = 1080, 1920
M = 80
TOP, BOT = 250, 1620
BK = (12, 6, 8)
OR_TXT = (255, 150, 40)
CREAM = (255, 244, 225)
WORD = 'HALLOWEEN'


def grid():
    return np.mgrid[0:H, 0:W].astype(np.float32)


def poly(polys, ellipses=()):
    m = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon(p, fill=255)
    for e in ellipses:
        d.ellipse(e, fill=255)
    return np.asarray(m, np.float32) / 255.0


def over(img, col, m):
    img[...] = img * (1 - m[..., None]) + col * m[..., None]


# ── 달 ────────────────────────────────────────────────
def moon(img, cx, cy, r):
    yy, xx = grid()
    d = np.hypot(xx - cx, yy - cy)
    img += np.exp(-((d / (r * 1.6)) ** 2))[..., None] * np.float32([0.30, 0.16, 0.10])
    img += np.exp(-((d / (r * 3.2)) ** 2))[..., None] * np.float32([0.10, 0.04, 0.06])
    m = np.clip(r - d + 1, 0, 1)
    tex = fbm(H, W, 6, seed=31, base=5)
    shade = 0.86 + 0.14 * tex - 0.10 * np.clip((xx - cx + yy - cy) / (2 * r), 0, 1)
    col = np.float32([1.0, 0.90, 0.68])[None, None, :] * shade[..., None]
    over(img, col, m)


# ── 호박 ──────────────────────────────────────────────
def pumpkin(img, cx, cy, s):
    """입체 호박. 반환: 얼굴 빛 마스크 (블룸용)."""
    yy, xx = grid()
    lobes = [(-0.36, 0.50, 0.78, 0.66), (0.36, 0.50, 0.78, 0.66),
             (-0.19, 0.52, 0.90, 0.84), (0.19, 0.52, 0.90, 0.84), (0.0, 0.50, 0.96, 1.0)]
    body = np.zeros((H, W), np.float32)
    for dx, rw, rh, br in lobes:
        lx, rx, ry = cx + dx * s, rw * s / 2, rh * s / 2
        dd = ((xx - lx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        m = np.clip((1 - dd) * min(rx, ry) * 0.5, 0, 1)
        u = (xx - lx) / rx
        v = (yy - cy) / ry
        shade = np.clip((1 - 0.60 * u ** 2) * (0.80 - 0.30 * v), 0.15, 1.2) * br
        col = np.float32([1.0, 0.44, 0.04])[None, None, :] * shade[..., None]
        col *= (1 - 0.55 * np.clip(dd, 0, 1) ** 4)[..., None]          # 골 · 테두리 어둡게
        over(img, col, m)
        body = np.maximum(body, m)
    # 위쪽 반사
    spec = np.exp(-(((xx - (cx - 0.10 * s)) / (0.07 * s)) ** 2 + ((yy - (cy - 0.30 * s)) / (0.10 * s)) ** 2))
    img += (spec * body)[..., None] * np.float32([0.35, 0.28, 0.18])
    # 테두리 한 줄 — 노을 바탕에서 몸통을 뗀다
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    rim = np.clip(body - cv2.erode(body, k), 0, 1)
    over(img, np.float32([0.18, 0.04, 0.02]), rim * 0.9)
    # 꼭지
    st = poly([[(cx - 0.045 * s, cy - 0.44 * s), (cx + 0.05 * s, cy - 0.44 * s),
                (cx + 0.10 * s, cy - 0.64 * s), (cx + 0.02 * s, cy - 0.67 * s)]])
    over(img, np.float32([0.20, 0.17, 0.07]) * (0.7 + 0.3 * np.clip((cx - xx) / (0.05 * s) + 0.5, 0, 1))[..., None], st)
    # 얼굴
    face = poly([
        [(cx - 0.34 * s, cy - 0.02 * s), (cx - 0.07 * s, cy - 0.02 * s), (cx - 0.21 * s, cy - 0.26 * s)],
        [(cx + 0.34 * s, cy - 0.02 * s), (cx + 0.07 * s, cy - 0.02 * s), (cx + 0.21 * s, cy - 0.26 * s)],
        [(cx - 0.05 * s, cy + 0.12 * s), (cx + 0.05 * s, cy + 0.12 * s), (cx, cy + 0.02 * s)],
        [(cx - 0.38 * s, cy + 0.17 * s)] + [(cx + x * s, cy + s * (0.22 + (0.08 if i % 2 else 0)))
                                           for i, x in enumerate(np.linspace(-0.28, 0.28, 9))]
        + [(cx + 0.38 * s, cy + 0.17 * s), (cx + 0.22 * s, cy + 0.38 * s), (cx - 0.22 * s, cy + 0.38 * s)],
    ])
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(s * 0.03) | 1, int(s * 0.03) | 1))
    inner = cv2.erode(face, k2)
    wall = np.clip(face - inner, 0, 1)
    over(img, np.float32([0.40, 0.10, 0.02]), wall)                 # 파낸 두께
    dist = cv2.distanceTransform((inner > 0.5).astype(np.uint8), cv2.DIST_L2, 5)
    hot = np.clip(dist / (s * 0.05), 0, 1)
    fire = np.float32([1.0, 0.55, 0.10])[None, None, :] * (1 - hot[..., None]) + \
        np.float32([1.0, 0.92, 0.62])[None, None, :] * hot[..., None]
    over(img, fire, inner)
    # 몸통 안으로 번지는 빛
    glow = cv2.GaussianBlur(face, (0, 0), s * 0.06)
    img += (glow * body)[..., None] * np.float32([0.9, 0.45, 0.10]) * 0.8
    return inner


# ── 박쥐 · 바닥 ───────────────────────────────────────
def bats(img, spots, col=(0.03, 0.01, 0.03), blur=0.0):
    m = poly([bat_points(x, y, s, r, f) for x, y, s, r, f in spots])
    if blur:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    over(img, np.float32(col), m)


def graveyard(img, y0):
    yy, xx = grid()
    ground = (yy > y0 + 40 * np.sin(xx / W * np.pi * 1.6 + 0.4) + 20).astype(np.float32)
    stones = []
    rng = np.random.default_rng(4)
    for x in (110, 250, 420, 680, 840, 980):
        h = rng.uniform(60, 105)
        w = h * 0.6
        b = y0 + 40 * np.sin(x / W * np.pi * 1.6 + 0.4) + 30
        if rng.random() < 0.4:
            t = w * 0.25
            stones.append([(x - t / 2, b), (x - t / 2, b - h * 0.6), (x - w / 2, b - h * 0.6), (x - w / 2, b - h * 0.6 - t),
                           (x - t / 2, b - h * 0.6 - t), (x - t / 2, b - h), (x + t / 2, b - h), (x + t / 2, b - h * 0.6 - t),
                           (x + w / 2, b - h * 0.6 - t), (x + w / 2, b - h * 0.6), (x + t / 2, b - h * 0.6), (x + t / 2, b)])
        else:
            pts = [(x - w / 2, b), (x - w / 2, b - h + w / 2)]
            pts += [(x + np.cos(a) * w / 2, b - h + w / 2 - np.sin(a) * w / 2) for a in np.linspace(np.pi, 0, 12)]
            pts += [(x + w / 2, b - h + w / 2), (x + w / 2, b)]
            stones.append(pts)
    m = np.maximum(ground, poly(stones))
    over(img, np.float32([0.05, 0.015, 0.03]), m)
    # 안개
    n = fbm(H, W, 5, seed=8, base=3)
    n = cv2.GaussianBlur(n, (0, 0), sigmaX=60, sigmaY=12)
    band = np.exp(-((yy - (y0 + 30)) / 120) ** 2)
    img += (n * band)[..., None] * np.float32([0.55, 0.30, 0.25]) * 0.35


def drips(d, x0, x1, yb, n, seed, col):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        dx = rng.uniform(x0 + 20, x1 - 20)
        L, w = rng.uniform(20, 58), rng.uniform(9, 14)
        d.rounded_rectangle([dx - w / 2, yb - 8, dx + w / 2, yb + L], int(w / 2), fill=col)
        d.ellipse([dx - w * 0.75, yb + L - w * 0.6, dx + w * 0.75, yb + L + w * 0.9], fill=col)


def main():
    img = sky(W, H, [(0.0, (0.035, 0.015, 0.06)), (0.28, (0.10, 0.03, 0.12)), (0.46, (0.42, 0.08, 0.06)),
                     (0.58, (0.90, 0.34, 0.04)), (0.80, (1.0, 0.52, 0.08)), (1.0, (0.92, 0.40, 0.05))])
    # 별 (위쪽만)
    rng = np.random.default_rng(3)
    for _ in range(160):
        x, y = rng.integers(0, W), rng.integers(0, 700)
        v = rng.random() ** 3
        cv2.circle(img, (int(x), int(y)), 1, (0.6 + v, 0.55 + v, 0.6 + v), -1, cv2.LINE_AA)

    moon(img, 540, 585, 255)
    bats(img, [(430, 450, 52, -0.15, 0.9), (610, 490, 38, 0.2, 1.1), (520, 410, 28, 0.05, 0.8),
               (700, 560, 30, -0.1, 1.0), (380, 560, 24, 0.15, 0.9)])
    face = pumpkin(img, 540, 770, 480)
    bats(img, [(140, 470, 110, -0.25, 1.0), (950, 420, 96, 0.2, 0.9)], blur=1.6)     # 가까운 둘
    bats(img, [(220, 700, 46, 0.1, 1.0), (880, 660, 40, -0.15, 1.1)])
    graveyard(img, 1790)

    # 빛 마감
    fglow = cv2.GaussianBlur(face, (0, 0), 30) * 1.4 + cv2.GaussianBlur(face, (0, 0), 90) * 2.0
    img += fglow[..., None] * np.float32([1.0, 0.55, 0.12]) * 0.35
    bloom(img, 0.75, W * 0.012, 0.35)

    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    tracked(d, (M, TOP + 8), 'BLACKOUT CREW PRESENTS', cond(30, 'SemiBold Condensed'), 0.40, CREAM + (230,))
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.19)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    pil.alpha_composite(lg, (W - M - lw, TOP))
    d = ImageDraw.Draw(pil)

    # COSTUME PARTY 표
    ft = cond(52, 'Bold Condensed')
    t = 'COSTUME PARTY'
    tw = tracked_w(t, ft, 0.12)
    y = 1035
    d.rounded_rectangle([(W - tw) / 2 - 28, y - 8, (W + tw) / 2 + 28, y + 62], 31, fill=BK + (255,))
    tracked(d, ((W - tw) / 2, y), t, ft, 0.12, OR_TXT)

    # HALLOWEEN
    for s in range(320, 60, -4):
        fw = cond(s, 'Bold Condensed')
        if d.textlength(WORD, font=fw) <= W - M * 2:
            break
    b = d.textbbox((0, 0), WORD, font=fw)
    x = (W - (b[2] - b[0])) / 2 - b[0]
    y = 1122
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((x + 8, y - b[1] + 10), WORD, font=fw, fill=(90, 15, 5, 150))
    pil.alpha_composite(Image.fromarray(cv2.GaussianBlur(np.asarray(sh), (0, 0), 6)))
    d = ImageDraw.Draw(pil)
    d.text((x, y - b[1]), WORD, font=fw, fill=BK)
    yb = y + (b[3] - b[1])
    drips(d, x + b[0], x + b[2], yb, 9, 9, BK)

    # 날짜 · 시간
    y = yb + 96
    fd = cond(70, 'Bold Condensed')
    t = f'10.30 FRI   {TIME}'
    tracked(d, ((W - tracked_w(t, fd, 0.04)) / 2, y), t, fd, 0.04, BK)
    y += 80
    fv = cond(60, 'Bold Condensed')
    t = VENUE + ' B1'
    vw = tracked_w(t, fv, 0.06)
    d.rectangle([(W - vw) / 2 - 26, y - 6, (W + vw) / 2 + 26, y + 70], fill=BK)
    tracked(d, ((W - vw) / 2, y), t, fv, 0.06, OR_TXT)
    y += 82
    fa = kr(32)
    t = ADDR.replace('B1 · ', '') + '  ·  웰컴드링크 생맥 or 데킬라'
    d.text(((W - d.textlength(t, font=fa)) / 2, y), t, font=fa, fill=BK)
    y += 44
    assert y < BOT, y

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    yy, xx = grid()
    v = ((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2
    out *= np.clip(1 - 0.30 * v, 0.5, 1)[..., None]
    grain(out, 0.016)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'HO_스토리.jpg'), quality=95)
    print('완료: HO_스토리')


if __name__ == '__main__':
    main()
