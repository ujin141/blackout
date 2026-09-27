"""
**BLACKOUT HALLOWEEN · 10.31 SAT — 영화 포스터 판.**

    python poster_halloween2.py   →  out/halloween/HW1.jpg HW2.jpg HW3.jpg · _할로윈격자.jpg · HW_스토리.jpg

## 앞 판에서 바꾼 것

앞 판은 할로윈 **소품을 모아 놓은** 판이었다 — 호박 · 울타리 · 거미줄이 따로 놀아서
클립아트로 읽혔다. 이 판은 **공포 영화 포스터의 문법**으로 간다.

    주인공 하나   핏빛 보름달. 그 안에서 호박 얼굴이 **달 속에서 웃는다**
                  호박을 따로 그리지 않는다 — 달이 호박이다
    글자         HALLOWEEN 을 세리프(Noto Serif KR Black)로. 영화 제목은 세리프다
                 은색 금속에 핏빛 테. 아홉 칸에 한 자씩 (HAL / LOW / EEN)
    깊이         먼 숲 → 안개 → 가까운 숲 · 묘지 · 예배당. 세 겹이라 공간이 생긴다
    박쥐         달에서 흘러나와 양옆 장으로 퍼진다. 멀어질수록(= 가까워질수록) 커진다
    크레딧       맨 아래 좁은 글씨 한 줄. 영화 포스터 끝의 그 줄
    색           핏빛 빨강 + 달 속 불빛(주황) 둘. 나머지는 검정 · 은색

올리는 순서 HW3 → HW2 → HW1.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fest_kit import night, sky, vignette
from poster_halloween import (OUT, blood_moon, bat_points, fog, logo_img, paste, _bez)
from poster_hook import silver_text
from poster_kit import bloom, grain
from poster_moon import LOGO, over, starfield, tracked, tracked_w

SERIF = 'C:/Windows/Fonts/NotoSerifKR-VF.ttf'
COND = 'C:/Windows/Fonts/bahnschrift.ttf'

WORD = 'HALLOWEEN'
DATE = '10.31 SAT'
PERK = '분장하고 오면 술 한 잔 서비스'
TBA = '장소 · 라인업 곧 공개'
TAG = ['10월의 마지막 밤,', '가면을 쓰고 오세요']

BONE = (232, 228, 222, 255)
DIM = (170, 160, 160, 255)
FAINT = (120, 108, 110, 255)
RED = (150, 18, 22, 255)
FAR = (34, 12, 15, 255)
NEAR = (6, 4, 6, 255)
FIRE = np.float32([1.0, 0.46, 0.10])


def serif(size, w='Black'):
    f = ImageFont.truetype(SERIF, size)
    f.set_variation_by_name(w)
    return f


def cond(size, w='Condensed'):
    f = ImageFont.truetype(COND, size)
    f.set_variation_by_name(w)
    return f


def hh(t, f):
    return ImageDraw.Draw(Image.new('L', (8, 8))).textbbox((0, 0), t, font=f)[3]


def tw(t, f, track=0.0):
    return tracked_w(t, f, track)


# ── 달 속 얼굴 ────────────────────────────────────────
def grinning_moon(R):
    """
    핏빛 달 안에서 호박 얼굴이 웃는다.

    얼굴을 달 위에 그리면 스티커다. **달 표면을 파낸 것처럼** — 둘레를 먼저
    어둡게 누르고, 그 안에서 불빛이 새어 나오게 한다. 가장자리는 흐리게.
    """
    mf = blood_moon(R)
    S = 2 * R
    m = Image.new('L', (S, S), 0)
    g = ImageDraw.Draw(m)
    c = R
    # 눈 — 위로 찢어진 삼각
    for sgn in (-1, 1):
        g.polygon([(c + sgn * R * 0.46, c - R * 0.02), (c + sgn * R * 0.12, c - R * 0.06),
                   (c + sgn * R * 0.36, c - R * 0.40)], fill=255)
    # 코
    g.polygon([(c - R * 0.07, c + R * 0.14), (c + R * 0.07, c + R * 0.14), (c, c + R * 0.02)], fill=255)
    # 입 — 이빨 사이로 파인 긴 웃음
    top = [(c + x * R, c + R * (0.26 + 0.10 * x * x)) for x in np.linspace(-0.62, 0.62, 13)]
    teeth = []
    for i, (x, y) in enumerate(top):
        teeth.append((x, y + (R * 0.07 if i % 2 else 0)))
    bot = [(c + x * R, c + R * (0.44 + 0.05 * x * x) - R * 0.26 * (1 - x * x / 0.40)) for x in np.linspace(0.62, -0.62, 13)]
    bot = [(x, max(y, c + R * 0.42)) for x, y in bot]
    bot = [(c + x * R, c + R * (0.58 - 0.30 * x * x)) for x in np.linspace(0.62, -0.62, 13)]
    g.polygon(teeth + bot, fill=255)
    a = np.asarray(m, np.float32) / 255.0
    edge = cv2.GaussianBlur(a, (0, 0), R * 0.035)
    core = cv2.GaussianBlur(a, (0, 0), R * 0.012)
    carve = cv2.GaussianBlur(a, (0, 0), R * 0.08)
    rgb = mf[..., :3]
    rgb *= (1 - carve[..., None] * 0.45)                       # 파낸 둘레의 그늘
    rgb += edge[..., None] * FIRE * 0.55                        # 새어 나오는 불
    rgb += core[..., None] * np.float32([1.0, 0.80, 0.45]) * 0.55
    mf[..., :3] = np.clip(rgb, 0, 1.2)
    return mf, a


def moon_light(img, cx, cy, R):
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dd = (xx - cx) ** 2 + (yy - cy) ** 2
    img += np.exp(-dd / (2 * (R * 1.35) ** 2))[..., None] * np.float32([0.30, 0.035, 0.040])
    img += np.exp(-dd / (2 * (R * 3.6) ** 2))[..., None] * np.float32([0.09, 0.012, 0.016])
    # 달에서 내려오는 빛기둥. 안개에 걸린다
    ang = np.arctan2(yy - cy, xx - cx)
    rng = np.random.default_rng(4)
    prof = cv2.GaussianBlur(rng.random(720).astype(np.float32)[None, :], (0, 0), 10)[0]
    prof = (prof - prof.min()) / max(float(np.ptp(prof)), 1e-6)
    beam = prof[((ang + np.pi) / (2 * np.pi) * 719).astype(np.int32)] ** 3
    dist = np.sqrt(dd)
    fall = np.clip((dist - R) / (R * 0.8), 0, 1) * np.exp(-((dist - R) / (R * 2.6)) ** 2)
    down = np.clip((yy - cy) / (R * 0.5), 0, 1)
    img += cv2.GaussianBlur(beam * fall * down, (0, 0), 8)[..., None] * np.float32([0.22, 0.05, 0.05])


# ── 숲 · 묘지 · 예배당 ────────────────────────────────
def branch(d, x, y, ang, length, width, depth, rng, col):
    x2 = x + np.cos(ang) * length
    y2 = y - np.sin(ang) * length
    d.line([(x, y), (x2, y2)], fill=col, width=max(1, int(width)))
    d.ellipse([x2 - width / 2, y2 - width / 2, x2 + width / 2, y2 + width / 2], fill=col)
    if depth == 0 or width < 1.1:
        return
    for k in range(2 if depth > 3 else int(rng.integers(2, 4))):
        da = rng.uniform(0.22, 0.7) * (1 if k % 2 else -1)
        branch(d, x2, y2, ang + da + rng.normal(0, 0.14), length * rng.uniform(0.6, 0.8),
               width * 0.64, depth - 1, rng, col)


def forest(d, W, base, seed, spots, col):
    """spots: (x, 높이, 굵기). 가지가 옆으로 벌어진 맨 나무."""
    rng = np.random.default_rng(seed)
    for x, h, w in spots:
        branch(d, x, base, np.deg2rad(90 + rng.normal(0, 5)), h * 0.42, w, 7, rng, col)


def cross(d, x, base, h, col, lean=0.0):
    t = max(4, h * 0.13)
    arm = h * 0.62
    pts = [(x - t / 2, base), (x - t / 2, base - arm), (x - h * 0.32, base - arm), (x - h * 0.32, base - arm - t),
           (x - t / 2, base - arm - t), (x - t / 2, base - h), (x + t / 2, base - h), (x + t / 2, base - arm - t),
           (x + h * 0.32, base - arm - t), (x + h * 0.32, base - arm), (x + t / 2, base - arm), (x + t / 2, base)]
    c, s = np.cos(lean), np.sin(lean)
    d.polygon([(x + (px - x) * c - (py - base) * s, base + (px - x) * s + (py - base) * c) for px, py in pts], fill=col)


def stone(d, x, base, w, h, col, lean=0.0):
    pts = [(x - w / 2, base), (x - w / 2, base - h + w / 2)]
    pts += [(x + np.cos(a) * w / 2, base - h + w / 2 - np.sin(a) * w / 2) for a in np.linspace(np.pi, 0, 14)]
    pts += [(x + w / 2, base - h + w / 2), (x + w / 2, base)]
    c, s = np.cos(lean), np.sin(lean)
    d.polygon([(x + (px - x) * c - (py - base) * s, base + (px - x) * s + (py - base) * c) for px, py in pts], fill=col)


def chapel(d, lit, x, base, s, col):
    """버려진 예배당. 창 하나에만 불이 켜져 있다."""
    bw, bh = s * 0.9, s * 0.8
    d.rectangle([x - bw / 2, base - bh, x + bw / 2, base], fill=col)
    d.polygon([(x - bw / 2 - 8, base - bh), (x, base - bh - s * 0.45), (x + bw / 2 + 8, base - bh)], fill=col)
    tx = x + bw * 0.28
    d.rectangle([tx - s * 0.12, base - bh - s * 0.55, tx + s * 0.12, base - bh + 4], fill=col)
    d.polygon([(tx - s * 0.16, base - bh - s * 0.55), (tx, base - bh - s * 1.25), (tx + s * 0.16, base - bh - s * 0.55)], fill=col)
    cross(d, tx, base - bh - s * 1.24, s * 0.22, col)
    g = ImageDraw.Draw(lit)
    wx, wy, ww, wh = x - bw * 0.12, base - bh * 0.62, s * 0.13, s * 0.26
    g.rectangle([wx - ww / 2, wy, wx + ww / 2, wy + wh], fill=255)
    g.ellipse([wx - ww / 2, wy - ww / 2, wx + ww / 2, wy + ww / 2], fill=255)


def glow_on(img, mask, color, core_col, r1, r2, k):
    m = np.asarray(mask, np.float32) / 255.0
    core = cv2.GaussianBlur(m, (0, 0), 0.9)
    halo = cv2.GaussianBlur(m, (0, 0), r1) * 3.0 + cv2.GaussianBlur(m, (0, 0), r2) * 5.0
    img[...] = img * (1 - core[..., None]) + np.float32(core_col) * core[..., None]
    img += halo[..., None] * np.float32(color) * k


# ── 박쥐 떼 ───────────────────────────────────────────
def bat_stream(d, cx, cy, R, dirx, length, n, seed, keep, rise=0.35, smax=78):
    """달에서 흘러나와 한쪽으로 퍼진다. 달에서 멀수록 가깝다 — 커진다."""
    rng = np.random.default_rng(seed)
    for i in range(n):
        t = (i + rng.random()) / n
        x = cx + dirx * (R * 0.4 + t * length) + rng.normal(0, 30 + t * 90)
        y = cy - R * 0.2 - np.sin(t * np.pi * 0.9) * length * rise + rng.normal(0, 25 + t * 70)
        if not keep(x, y):
            continue
        s = 12 + (smax - 12) * t ** 1.5 * rng.uniform(0.7, 1.1)
        d.polygon(bat_points(x, y, s, rng.normal(0, 0.2) - dirx * 0.1, rng.uniform(0.7, 1.15)), fill=NEAR)


def red_eyes(mask, spots):
    g = ImageDraw.Draw(mask)
    for x, y, s in spots:
        for dx in (-s * 1.7, s * 1.7):
            g.ellipse([x + dx - s, y - s * 0.42, x + dx + s, y + s * 0.42], fill=255)


def title(ch_or_word, size, track=0.0):
    """세리프 은색 금속 + 핏빛 테. 테는 글자 모양을 넓혀 흐린 빨강."""
    f = serif(size)
    m = silver_text(ch_or_word, f, track)
    a = m[..., 3]
    pad = 24
    big = np.zeros((a.shape[0] + pad * 2, a.shape[1] + pad * 2, 4), np.float32)
    rim = cv2.GaussianBlur(np.pad(a, pad), (0, 0), 9) * 1.6
    big[..., :3] = np.float32([0.62, 0.04, 0.05]) * np.clip(rim, 0, 1)[..., None]
    big[..., 3] = np.clip(rim, 0, 0.85)
    inner = np.pad(m, ((pad, pad), (pad, pad), (0, 0)))
    ia = inner[..., 3:4]
    # 금속을 뼈 빛으로 살짝 데운다
    inner[..., :3] = inner[..., :3] * np.float32([1.0, 0.97, 0.93])
    big[..., :3] = big[..., :3] * (1 - ia) + inner[..., :3] * ia
    big[..., 3] = np.maximum(big[..., 3], inner[..., 3])
    return big, pad


def sky_base(W, H):
    return sky(W, H, [(0.0, (0.006, 0.004, 0.006)), (0.45, (0.030, 0.008, 0.012)),
                      (0.82, (0.070, 0.016, 0.020)), (1.0, (0.012, 0.004, 0.006))])


def to_pil(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')


def to_np(p):
    return np.asarray(p.convert('RGB'), np.float32) / 255.0



# ══════════════════════════════════════════════════════════
#  파티 — 오고 싶게
# ══════════════════════════════════════════════════════════
#
# 무서운 판은 멋있지만 **가고 싶지는 않다.** 포스터가 할 일은 오게 만드는 것.
# 그래서 아래 절반을 파티로 채운다 — 부스 · 레이저 · 손 든 사람들.
# 사람들 머리에 마녀 모자 · 고양이 귀 · 뿔 · 토끼 귀를 씌운다. 코스튬 파티라는 걸
# 말보다 먼저 보여 주고, "분장하고 오면 술 한 잔" 이 왜 있는지가 그림으로 이어진다.

HOOK = ['분장하고 오면', '술 한 잔 서비스']
from fonts import KRD


def krd(size):
    return ImageFont.truetype(KRD, size)


def person(d, x, base, s, hat, arms, rng, col=NEAR):
    """사람 하나. 머리 · 어깨 · 팔. hat 은 머리 장식."""
    hr = s * 0.13
    hy = base - s * 0.86
    d.ellipse([x - hr, hy - hr, x + hr, hy + hr], fill=col)
    d.polygon([(x - s * 0.30, base), (x - s * 0.24, hy + hr * 1.6), (x - s * 0.08, hy + hr * 0.9),
               (x + s * 0.08, hy + hr * 0.9), (x + s * 0.24, hy + hr * 1.6), (x + s * 0.30, base)], fill=col)
    sh = hy + hr * 1.7
    for side, up in arms:
        sx = x + side * s * 0.22
        ang = np.deg2rad(90 + side * (-10 + (1 - up) * 70) + rng.normal(0, 6))
        ex, ey = sx + np.cos(ang) * s * 0.30, sh - np.sin(ang) * s * 0.30
        ang2 = ang + side * rng.uniform(-0.3, 0.2)
        hx, hy2 = ex + np.cos(ang2) * s * 0.28, ey - np.sin(ang2) * s * 0.28
        d.line([(sx, sh), (ex, ey), (hx, hy2)], fill=col, width=max(3, int(s * 0.075)), joint='curve')
        d.ellipse([hx - s * 0.045, hy2 - s * 0.045, hx + s * 0.045, hy2 + s * 0.045], fill=col)
    top = hy - hr
    if hat == 'witch':
        d.ellipse([x - hr * 2.0, top + hr * 0.2, x + hr * 2.0, top + hr * 0.75], fill=col)
        d.polygon([(x - hr * 1.0, top + hr * 0.45), (x + hr * 0.3, top - hr * 3.2), (x + hr * 1.6, top - hr * 2.6),
                   (x + hr * 0.6, top - hr * 2.4), (x + hr * 1.0, top + hr * 0.45)], fill=col)
    elif hat == 'cat':
        for sg in (-1, 1):
            d.polygon([(x + sg * hr * 0.25, top + hr * 0.3), (x + sg * hr * 1.05, top - hr * 1.1),
                       (x + sg * hr * 1.0, top + hr * 0.6)], fill=col)
    elif hat == 'horns':
        for sg in (-1, 1):
            d.polygon([(x + sg * hr * 0.35, top + hr * 0.4), (x + sg * hr * 0.95, top - hr * 1.2),
                       (x + sg * hr * 0.85, top + hr * 0.6)], fill=col)
    elif hat == 'bunny':
        for sg in (-1, 1):
            cx = x + sg * hr * 0.45
            d.ellipse([cx - hr * 0.28, top - hr * 2.3, cx + hr * 0.28, top + hr * 0.3], fill=col)
    elif hat == 'pumpkin':
        d.ellipse([x - hr * 1.5, hy - hr * 1.3, x + hr * 1.5, hy + hr * 1.2], fill=col)


def crowd(d, W, base, seed, n, smin, smax, avoid=(), col=NEAR):
    rng = np.random.default_rng(seed)
    hats = ['witch', 'cat', 'horns', 'bunny', None, None, 'pumpkin', 'cat', 'horns', 'witch']
    xs = np.linspace(-20, W + 20, n) + rng.normal(0, W / n * 0.3, n)
    for x in xs:
        if any(a0 < x < a1 for a0, a1 in avoid):
            continue
        s = rng.uniform(smin, smax)
        r = rng.random()
        arms = [(-1, 1.0), (1, 1.0)] if r < 0.45 else [(int(rng.choice([-1, 1])), 1.0)] if r < 0.8 else [(-1, 0.3), (1, 0.3)]
        person(d, x, base + rng.uniform(0, s * 0.12), s, hats[int(rng.integers(0, len(hats)))], arms, rng, col)


def rim_light(img, before, after, color, k=0.9):
    """앞 사람들 윗면에 무대 빛. 실루엣이 검정 판에 묻히지 않게."""
    a = (np.abs(to_np(after) - to_np(before)).sum(-1) > 0.02).astype(np.float32)
    up = np.clip(a - np.roll(a, 4, axis=0), 0, 1)
    side = np.clip(a - np.roll(a, 3, axis=1), 0, 1) + np.clip(a - np.roll(a, -3, axis=1), 0, 1)
    rim = cv2.GaussianBlur(up + side * 0.4, (0, 0), 1.2)
    img += rim[..., None] * np.float32(color) * k


def booth(d, x, base, w, col):
    """디제이 부스와 디제이. 헤드폰, 한 손은 위로."""
    d.rectangle([x - w / 2, base - w * 0.28, x + w / 2, base + 2000], fill=col)
    s = w * 0.62
    hy = base - w * 0.28 - s * 0.62
    hr = s * 0.13
    d.ellipse([x - hr, hy - hr, x + hr, hy + hr], fill=col)
    d.arc([x - hr * 1.35, hy - hr * 1.45, x + hr * 1.35, hy + hr * 0.9], 180, 360, fill=col, width=max(3, int(hr * 0.35)))
    for sg in (-1, 1):
        d.ellipse([x + sg * hr * 1.25 - hr * 0.35, hy - hr * 0.35, x + sg * hr * 1.25 + hr * 0.35, hy + hr * 0.45], fill=col)
    d.polygon([(x - s * 0.32, base - w * 0.28), (x - s * 0.22, hy + hr * 1.5), (x + s * 0.22, hy + hr * 1.5),
               (x + s * 0.32, base - w * 0.28)], fill=col)
    d.line([(x + s * 0.2, hy + hr * 1.8), (x + s * 0.42, hy - hr * 0.4), (x + s * 0.50, hy - hr * 2.4)],
           fill=col, width=max(4, int(s * 0.08)), joint='curve')


def lasers(img, ox, oy, angles, length, color, k=1.0):
    H, W = img.shape[:2]
    m = np.zeros((H, W), np.float32)
    for a in angles:
        ex, ey = ox + np.cos(a) * length, oy - np.sin(a) * length
        cv2.line(m, (int(ox), int(oy)), (int(ex), int(ey)), 1.0, 2, cv2.LINE_AA)
    fade_ = np.clip(1 - np.hypot(*np.mgrid[0:H, 0:W][::-1].astype(np.float32) - np.float32([ox, oy])[:, None, None]) / length, 0, 1)
    core = m * fade_
    glow = cv2.GaussianBlur(core, (0, 0), 6) * 2.5 + cv2.GaussianBlur(core, (0, 0), 22) * 3.0
    img += core[..., None] * np.float32([1.0, 0.85, 0.80]) * 0.7 * k
    img += glow[..., None] * np.float32(color) * 0.5 * k


def stage_glow(img, cx, cy, rx, ry, color, k):
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-((xx - cx) / rx) ** 2 - ((yy - cy) / ry) ** 2)[..., None] * np.float32(color) * k


# ══════════════════════════════════════════════════════════
#  피드 세 장
# ══════════════════════════════════════════════════════════

def feed():
    W, H = 1080, 1350
    RW = W * 3
    M = 88
    TOP = 90
    img = sky_base(RW, H)
    starfield(img, 30, 560, 200, seed=51)
    mcx, mcy, MR = W + W // 2, 330, 230
    moon_light(img, mcx, mcy, MR)
    mf, _ = grinning_moon(MR)
    over(img, mf, mcx - MR, mcy - MR)

    # 무대 쪽 빛과 레이저. 부스는 가운데 장 바닥
    bx, by = mcx, H - 150
    stage_glow(img, bx, H - 60, RW * 0.40, 300, [0.34, 0.06, 0.05], 1.0)
    stage_glow(img, bx, H - 40, 360, 160, [0.60, 0.26, 0.08], 0.6)
    rng = np.random.default_rng(5)
    angs = np.deg2rad(np.concatenate([np.linspace(12, 70, 7), np.linspace(110, 168, 7)]) + rng.normal(0, 2, 14))
    lasers(img, bx, by - 70, angs, 2400, [1.0, 0.10, 0.08], 0.9)
    lasers(img, bx, by - 70, np.deg2rad([28, 52, 128, 152]), 2400, [1.0, 0.55, 0.20], 0.6)

    pil = to_pil(img)
    d = ImageDraw.Draw(pil)
    forest(d, RW, H + 10, 14, [(20, 820, 30), (RW - 30, 800, 30)], NEAR)
    free = lambda x, y: (y < 560 or 900 < y < 1000) and y > 60
    bat_stream(d, mcx, mcy, MR, -1, 1350, 22, 71, free, rise=0.25)
    bat_stream(d, mcx, mcy, MR, 1, 1350, 22, 72, free, rise=0.25)
    booth(d, bx, by + 20, 260, NEAR)
    crowd(d, RW, H - 20, 90, 34, 170, 220, avoid=((bx - 150, bx + 150),), col=(44, 12, 14, 255))
    before = pil.copy()
    crowd(d, RW, H + 70, 92, 18, 300, 380, avoid=((bx - 190, bx + 190),))
    img = to_np(pil)
    rim_light(img, before, pil, [1.0, 0.36, 0.14], 0.85)
    fog(img, H - 360, H - 100, seed=62, a=0.12)

    # 글자
    pil = to_pil(img)
    d = ImageDraw.Draw(pil)
    lg = logo_img(int(W * 0.17))
    fe = cond(26, 'SemiLight Condensed')
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, TOP + 22), 'BLACKOUT CREW PRESENTS', fe, 0.42, FAINT)
        pil.alpha_composite(lg, (x0 + W - M - lg.width, TOP + 14))

    # 첫 장 후크 — 이 판에서 제일 큰 한국어
    fh = krd(96)
    y = TOP + 96
    for line in HOOK:
        d.text((M, y), line, font=fh, fill=BONE)
        y += hh(line, fh) + 10
    d.text((M, y + 10), '마녀 · 고양이 · 좀비, 뭐든 좋아요', font=serif(34, 'Medium'), fill=DIM)

    # 셋째 장 — 코스튬 파티
    x3 = 2 * W + M
    y = TOP + 100
    tracked(d, (x3, y), 'COSTUME', cond(120, 'Bold Condensed'), 0.06, BONE)
    y += 128
    tracked(d, (x3, y), 'PARTY', cond(120, 'Bold Condensed'), 0.06, (200, 30, 34, 255))
    y += 140
    d.text((x3, y), '할로윈 당일 밤, 같이 놀아요', font=serif(34, 'Medium'), fill=DIM)

    # HALLOWEEN
    slot = RW / len(WORD)
    size = 60
    for s in range(460, 60, -4):
        f = serif(s)
        if max(ImageDraw.Draw(Image.new('L', (8, 8))).textlength(ch, font=f) for ch in WORD) <= slot * 0.74:
            size = s
            break
    ly = 620
    lh = 0
    for i, ch in enumerate(WORD):
        m, pad = title(ch, size)
        paste(pil, m, slot * i + (slot - m.shape[1]) / 2, ly - pad)
        lh = max(lh, m.shape[0] - pad * 2)
    d = ImageDraw.Draw(pil)
    ry = ly + lh + 26
    d.line([(M, ry), (RW - M, ry)], fill=RED, width=2)
    y = ry + 22
    fd = serif(58, 'Bold')
    tracked(d, (W + (W - tw(DATE, fd, 0.08)) / 2, y), DATE, fd, 0.08, BONE)
    fk = serif(32, 'SemiBold')
    d.text((M, y + 8), '블랙아웃 할로윈 파티', font=fk, fill=BONE)
    d.text((x3, y + 8), TBA, font=fk, fill=BONE)

    out = to_np(pil)
    bloom(out, 0.55, W * 0.012, 0.42)
    vignette(out, 0.36, 1.8)
    grain(out, 0.016)
    big = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    tiles = []
    for c in range(3):
        t = big.crop((c * W, 0, (c + 1) * W, H))
        t.save(os.path.join(OUT, f'HW{c + 1}.jpg'), quality=94)
        tiles.append(t)
        night(np.asarray(t, np.float32) / 255.0, f'HW{c + 1}')
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(os.path.join(OUT, '_할로윈격자.jpg'), quality=92)
    print('피드 완료')


# ══════════════════════════════════════════════════════════
#  스토리
# ══════════════════════════════════════════════════════════

def story():
    W, H = 1080, 1920
    M = 88
    TOP, BOT = 250, 1620
    img = sky_base(W, H)
    starfield(img, 60, 900, 140, seed=52)
    mcx, mcy, MR = W // 2, 860, 250
    moon_light(img, mcx, mcy, MR)
    mf, _ = grinning_moon(MR)
    over(img, mf, mcx - MR, mcy - MR)

    bx, by = W // 2, H - 330
    stage_glow(img, bx, H - 220, W * 0.6, 360, [0.34, 0.06, 0.05], 1.0)
    stage_glow(img, bx, H - 200, 300, 180, [0.60, 0.26, 0.08], 0.6)
    rng = np.random.default_rng(6)
    angs = np.deg2rad(np.concatenate([np.linspace(20, 75, 5), np.linspace(105, 160, 5)]) + rng.normal(0, 2, 10))
    lasers(img, bx, by - 60, angs, 1600, [1.0, 0.10, 0.08], 0.9)
    lasers(img, bx, by - 60, np.deg2rad([40, 140]), 1600, [1.0, 0.55, 0.20], 0.6)

    pil = to_pil(img)
    d = ImageDraw.Draw(pil)
    free = lambda x, y: (y < 1130) and y > TOP + 300
    bat_stream(d, mcx, mcy, MR, -1, 520, 12, 81, free, rise=0.5, smax=64)
    bat_stream(d, mcx, mcy, MR, 1, 520, 12, 82, free, rise=0.5, smax=64)
    booth(d, bx, by + 40, 190, NEAR)
    crowd(d, W, H - 220, 93, 11, 180, 230, avoid=((bx - 140, bx + 140),), col=(44, 12, 14, 255))
    before = pil.copy()
    crowd(d, W, H - 110, 94, 8, 250, 300, avoid=((bx - 130, bx + 130),))
    d.rectangle([0, H - 150, W, H], fill=NEAR)
    img = to_np(pil)
    rim_light(img, before, pil, [1.0, 0.36, 0.14], 0.85)

    pil = to_pil(img)
    d = ImageDraw.Draw(pil)
    fe = cond(28, 'SemiLight Condensed')
    t = 'BLACKOUT CREW PRESENTS'
    tracked(d, (M, TOP + 8), t, fe, 0.42, FAINT)
    lg = logo_img(int(W * 0.19))
    pil.alpha_composite(lg, (W - M - lg.width, TOP))
    d = ImageDraw.Draw(pil)
    fh = krd(92)
    y = TOP + 64
    for line in HOOK:
        d.text(((W - d.textlength(line, font=fh)) / 2, y), line, font=fh, fill=BONE)
        y += hh(line, fh) + 8
    sub = '마녀 · 고양이 · 좀비, 뭐든 좋아요'
    f3 = serif(34, 'Medium')
    d.text(((W - d.textlength(sub, font=f3)) / 2, y + 10), sub, font=f3, fill=DIM)

    size = 60
    for s in range(300, 60, -2):
        if tw(WORD, serif(s), 0.04) <= W - M * 2:
            size = s
            break
    m, pad = title(WORD, size, 0.04)
    ly = 1110
    paste(pil, m, (W - m.shape[1]) / 2, ly - pad)
    d = ImageDraw.Draw(pil)
    y = ly + m.shape[0] - pad * 2 + 20
    d.line([(M + 140, y), (W - M - 140, y)], fill=RED, width=2)
    y += 22
    fd = serif(70, 'Bold')
    tracked(d, ((W - tw(DATE, fd, 0.08)) / 2, y), DATE, fd, 0.08, BONE)
    y += hh(DATE, fd) + 14
    ft = serif(30, 'Medium')
    d.text(((W - d.textlength(TBA, font=ft)) / 2, y), TBA, font=ft, fill=DIM)

    out = to_np(pil)
    bloom(out, 0.55, W * 0.012, 0.42)
    vignette(out, 0.36, 1.8)
    grain(out, 0.016)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'HW_스토리.jpg'), quality=94)
    night(out, 'HW_스토리')
    print('스토리 완료')


if __name__ == '__main__':
    feed()
    story()
