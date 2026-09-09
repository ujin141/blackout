"""
**AFTER MOON 라인업 셋 · 피드 세 장.** 첫 장에 디제이가 한꺼번에 선다.

    python feed_crew_moon.py   →  out/moon/C1.jpg C2.jpg C3.jpg · _크루격자.jpg

## 세 장이 하는 일

    C1  누가        누끼 셋이 달 앞에 한 무리로. 이름 다섯
    C2  언제        타임테이블. 22:00 → 02:10 등뼈 하나에 다섯 마디
    C3  얼마        9,900원 · 조건 · QR · PARTYMOA

## 이어지는 것

    달빛      C1 의 달에서 뻗는 빛줄기가 C2 로 넘어간다
    지평선    y 928, 세 칸을 가로지르는 한 줄 (홍보 3장과 같은 자리)
    아래 띠   같은 높이의 줄 두 개, 같은 글

## 사람은 셋뿐이다

BHO · LII 는 누끼가 없다. 사진 오면 CUT 에 넣고 GROUP 에 자리만 더하면
같은 판으로 다시 뽑힌다. 없는 사람을 실루엣으로 세우지 않는다 — 그건
지어낸 사진이다. 이름 다섯은 전부 적는다.

## 색은 사람에게만

검정 · 은색 · 흰색. 누끼의 색이 이 세 장의 유일한 색이다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import sky, specks, vignette
from fonts import KR, KRB
from poster_crew import crop_head, rimlight
from poster_dj4 import fringe, melt, sharpen
from poster_dj_moon import composite, ring
from poster_kit import bloom, fit, glow, grain, paint, tmask
from poster_lineup import LINEUP
from poster_lounge import bokeh
from poster_moon import (ARC_BOT, BRAND_FONT, CTA, CTA_KO, DATE, LOGO, OUT,
                         TITLE, godrays, metal, moonface, over, starfield)
from qr import build as qr_build

W, H = 1080, 1350
COLS = 3
RW = W * COLS
TOP, BOT = 96, 1266
SQ_T, SQ_B = 135, 1215            # 격자 정사각 크롭 안전 구간
M = int(W * 0.082)
U = 12
BASE = 26
V = 1.0

SILVER = np.float32([0.74, 0.77, 0.84])
INK = np.float32([0.96, 0.96, 0.98])
DIM = np.float32([0.62, 0.64, 0.70])
FAINT = np.float32([0.44, 0.46, 0.52])
RULE = np.float32([0.26, 0.27, 0.31])
STRIP = '22:00—02:10 · 9,900원 · 1차 30명 · 15:15 · 웰컴샷'
PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'

# (이름, 칸 폭 비율, 머리·어깨 높이, 가운데 x 비율, 정수리 y 오프셋, 앞뒤)
# 앞(z 큰 것)이 나중에 그려져 위에 선다. 가운데가 제일 앞, 제일 크다
# LYNN 은 오른팔을 올리고 있다. 그 팔이 오른쪽 사람 얼굴을 덮으니
# 오른쪽(TS)을 맨 앞에 세운다 — 얼굴이 팔을 덮지, 팔이 얼굴을 덮지 않는다
GROUP = [
    ('AROS', 0.56, 640, 0.25, 60, 0),
    ('LYNN', 0.58, 690, 0.44, 0, 1),
    ('TS',   0.54, 600, 0.79, 80, 2),
]


def step(n):
    return int(round(BASE * 1.28 ** n))


def band(img, x0, lower):
    """아래 띠. 디제이 개인 판과 같은 줄이라 옆에 놓여도 한 세트로 읽힌다."""
    fstrip = tmask(STRIP, KR, step(-1))
    fcta = tmask(CTA, BRAND_FONT, step(0), 0.20)
    fko = tmask(CTA_KO, KR, step(-2))
    fgen = tmask(ARC_BOT, BRAND_FONT, step(-2), 0.10)
    yb = BOT - lower
    cv2.line(img, (x0 + M, yb), (x0 + W - M, yb), RULE.tolist(), 1, cv2.LINE_AA)
    yb += U * 3
    paint(img, fstrip, x0 + M, yb + fstrip.shape[0] / 2, color=DIM, anchor='l')
    yb += fstrip.shape[0] + U * 3
    cv2.line(img, (x0 + M, yb), (x0 + W - M, yb), RULE.tolist(), 1, cv2.LINE_AA)
    yb += 2 + U * 3
    paint(img, fgen, x0 + M, yb + fcta.shape[0] / 2, color=FAINT, anchor='l')
    paint(img, fcta, x0 + W - M, yb + fcta.shape[0] / 2, color=INK, anchor='r')
    paint(img, fko, x0 + W - M - fcta.shape[1] - U, yb + fcta.shape[0] / 2 + 2,
          color=FAINT, anchor='r')


def lower_h():
    fstrip = tmask(STRIP, KR, step(-1))
    fcta = tmask(CTA, BRAND_FONT, step(0), 0.20)
    return int(U * 3 + fstrip.shape[0] + U * 3 + 2 + U * 3 + fcta.shape[0])


def header(img, x0, num):
    """로고 · 무슨 파티 · 번호. 세 칸 같은 자리 — 낱장으로 떠도 읽힌다."""
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.22)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    la = np.asarray(lg, np.float32) / 255.0
    lh = la.shape[0]
    sl_y, sl_x = slice(TOP, TOP + lh), slice(x0 + M, x0 + M + lw)
    al = la[..., 3:4]
    img[sl_y, sl_x] = img[sl_y, sl_x] * (1 - al) + la[..., :3] * al
    lab = tmask(f'{TITLE}   ·   {DATE}', BRAND_FONT, step(-2), 0.24)
    paint(img, lab, x0 + W / 2, TOP + lh + U * 3, color=DIM, anchor='c')
    n = tmask(f'{num:02d} / 03', BRAND_FONT, step(-1), 0.20)
    paint(img, n, x0 + W - M, TOP + lh / 2, color=DIM, anchor='r')
    return TOP + lh


def figure_at(name, box_w, base_h, cx_frac):
    """누끼 하나를 칸 폭 box_w 로 잘라, 칸 안 x 위치로 놓을 (x0, rgba) 를 준다."""
    fig = crop_head(name, box_w, base_h)
    x0 = int(W * cx_frac - box_w / 2)
    return x0, fig


def sheet():
    img = sky(RW, H, [(0.0, (0.030, 0.030, 0.040)),
                      (0.45, (0.058, 0.058, 0.074)),
                      (1.0, (0.022, 0.022, 0.030))])
    starfield(img, 0, int(H * 0.55), n=420, seed=26)

    # 달. C1 가운데 사람들 머리 뒤. 빛줄기는 C2 까지 뻗는다
    MR = int(W * 0.36)
    cx, my = W * 0.5, 540
    mf = moonface(MR)
    mf[..., :3] *= 0.70
    over(img, mf, int(cx) - MR, my - MR)
    godrays(img, cx, my, MR, seed=7, a=0.18)
    yy, xx = np.mgrid[0:H, 0:RW].astype(np.float32)
    img += np.exp(-(((xx - cx) ** 2 + (yy - my) ** 2) / (2 * (MR * 2.2) ** 2)))[..., None] \
        * np.float32([0.05, 0.05, 0.07])
    ring(img, cx, my, MR + 20, 2, 0.50)
    ring(img, cx, my, MR + 54, 1, 0.18)
    bokeh(img, n=30, seed=3, y0=0.0, y1=0.45)
    bokeh(img, n=16, seed=9, y0=0.62, y1=1.0)

    # 지평선. 홍보 3장과 같은 y — 프로필에서 두 줄이 같은 결로 읽힌다
    y = 928
    line = np.sin(np.linspace(0, np.pi, RW)) ** 0.7
    img[y:y + 2] += (line[None, :, None] * np.float32([0.30, 0.31, 0.42])) * 0.5
    return img


def tile1(img):
    x0 = 0
    lh_bottom = header(img, x0, 1)
    # 머리글 줄과 손이 안 겹치게 한 뼘 내린다
    head_top = lh_bottom + U * 10

    # 이름 판 자리를 먼저 잡는다. 사람은 그 위에 선다
    lower = lower_h()
    title = tmask('LINE UP', BRAND_FONT, min(fit('LINE UP', BRAND_FONT, W - M * 2, 0.10), 150), 0.10)
    names = tmask('  ·  '.join(n for n, _, _ in LINEUP), BRAND_FONT, step(-1), 0.16)
    ny = BOT - lower - U * 5 - names.shape[0] - int(U * 1.5) - title.shape[0]

    # 뒷그림자 → 사람. z 순서대로
    for name, bw, bh, cxf, dy, _ in sorted(GROUP, key=lambda g: g[5]):
        box_w = int(W * bw)
        fx, fig = figure_at(name, box_w, bh, cxf)
        top = head_top + dy
        a_ = np.clip((fig[..., 3] - 0.045) / 0.955, 0, 1).copy()
        px = sharpen(np.clip(fig[..., :3], 0, 1).copy(), 2.3, 0.6)
        a_, px = melt(a_, px, 0.30, len(name) * 31, V)
        # 칸 폭짜리 마스크를 칸 x 위치에 얹는다: 통짜 폭으로 옮겨 담는다
        A = np.zeros((a_.shape[0], W), np.float32)
        P = np.zeros((a_.shape[0], W, 3), np.float32)
        sx0, sx1 = max(0, fx), min(W, fx + box_w)
        A[:, sx0:sx1] = a_[:, sx0 - fx:sx1 - fx]
        P[:, sx0:sx1] = px[:, sx0 - fx:sx1 - fx]
        # 뒤에 선 사람은 살짝 어둡게 — 거리가 생긴다
        if name == 'AROS':
            P *= 0.86
        sub = img[:, x0:x0 + W]
        composite(sub, top, A, P)
        rim = rimlight(A, V, 1.4, 2.2, 0.28)
        n = min(H - top, rim.shape[0])
        sub[top:top + n] += rim[:n][..., None] * SILVER * 0.55
        img[:, x0:x0 + W] = sub

    # 이름 판. 어깨를 살짝 덮는다
    cx = x0 + W / 2
    plate = metal(*title.shape, title.astype(np.float32) / 255.0)
    glow(img, title, cx, ny + title.shape[0] / 2, SILVER, 0.22, 26, 'c', 'c')
    over(img, plate, int(cx - title.shape[1] / 2), ny)
    y = ny + title.shape[0] + int(U * 1.5)
    paint(img, names, cx, y + names.shape[0] / 2, color=DIM, anchor='c')
    band(img, x0, lower)


def tile2(img):
    x0 = W
    lh_bottom = header(img, x0, 2)
    lower = lower_h()
    title = tmask('TIME TABLE', BRAND_FONT, step(3), 0.20)
    ty = lh_bottom + U * 7
    paint(img, title, x0 + M, ty + title.shape[0] / 2, color=INK, anchor='l')
    y_top = ty + title.shape[0] + U * 5
    y_bot = BOT - lower - U * 5
    # 등뼈 한 줄. 22:00 에서 02:10 까지 밤이 내려간다
    sx = x0 + M + 14
    cv2.line(img, (sx, y_top), (sx, y_bot), (SILVER * 0.55).tolist(), 2, cv2.LINE_AA)
    n = len(LINEUP)
    gap = (y_bot - y_top) / (n - 1 + 0.6)
    size = min(fit(max((nm for nm, _, _ in LINEUP), key=len), BRAND_FONT, W * 0.62, 0.06), 118)
    for i, (nm, a, b) in enumerate(LINEUP):
        cy = int(y_top + gap * (i + 0.3))
        cv2.circle(img, (sx, cy), 7, INK.tolist(), -1, cv2.LINE_AA)
        cv2.circle(img, (sx, cy), 13, (SILVER * 0.6).tolist(), 1, cv2.LINE_AA)
        tm = tmask(f'{a} — {b}', BRAND_FONT, step(-1), 0.10)
        paint(img, tm, sx + 44, cy - size * 0.42, color=DIM, anchor='l')
        nm_m = tmask(nm, BRAND_FONT, size, 0.06)
        plate = metal(*nm_m.shape, nm_m.astype(np.float32) / 255.0)
        over(img, plate, sx + 44, int(cy - size * 0.42 + tm.shape[0] + U * 0.8))
        num = tmask(f'{i + 1:02d}', BRAND_FONT, step(-1), 0.20)
        paint(img, num, x0 + W - M, cy, color=FAINT, anchor='r')
    band(img, x0, lower)


def tile3(img):
    x0 = 2 * W
    lh_bottom = header(img, x0, 3)
    lower = lower_h()
    y = lh_bottom + U * 7
    # 값. 숫자는 은색 판, 원 은 흰 글자
    price = tmask('9,900', BRAND_FONT, 190, 0.02)
    plate = metal(*price.shape, price.astype(np.float32) / 255.0)
    glow(img, price, x0 + M + price.shape[1] / 2, y + price.shape[0] / 2, SILVER, 0.20, 26, 'c', 'c')
    over(img, plate, x0 + M, y)
    won = tmask('원', KRB, step(3))
    paint(img, won, x0 + M + price.shape[1] + U, y + price.shape[0] - won.shape[0] / 2 - 6,
          color=INK, anchor='l')
    y += price.shape[0] + U * 2
    sub = tmask('남녀 같은 값 · 웰컴샷 포함', KR, step(0))
    paint(img, sub, x0 + M, y + sub.shape[0] / 2, color=DIM, anchor='l')
    y += sub.shape[0] + U * 5

    facts = [('일시', '9.26 토 22:00 — 02:10'), ('장소', '압구정 딥하우즈'),
             ('1차', '30명 · 남녀 15:15'), ('예매', '파티모아 · 입금 24시간')]
    for k, (lab, val) in enumerate(facts):
        cv2.line(img, (x0 + M, y), (x0 + W - M, y), RULE.tolist(), 1, cv2.LINE_AA)
        y += U * 2
        lm = tmask(lab, KR, step(-1))
        vm = tmask(val, KRB, step(1))
        paint(img, lm, x0 + M, y + vm.shape[0] / 2, color=FAINT, anchor='l')
        paint(img, vm, x0 + M + 120, y + vm.shape[0] / 2, color=INK, anchor='l')
        y += vm.shape[0] + U * 2
    cv2.line(img, (x0 + M, y), (x0 + W - M, y), RULE.tolist(), 1, cv2.LINE_AA)

    # QR. 흰 판에 검정 코드. 옆에 한 줄
    qs = 236
    q = qr_build(PARTY_URL, 220, [0.06, 0.06, 0.08], [1.0, 1.0, 1.0], badge=False, error='m')
    q = q.resize((qs, qs), Image.NEAREST).convert('RGB')
    qa = np.asarray(q, np.float32) / 255.0
    pad = 18
    qy = BOT - lower - U * 4 - qs - pad * 2
    qx = x0 + M
    img[qy:qy + qs + pad * 2, qx:qx + qs + pad * 2] = 1.0
    img[qy + pad:qy + pad + qs, qx + pad:qx + pad + qs] = qa
    hint = tmask('카메라로 찍으면 예매 화면', KR, step(0))
    paint(img, hint, qx + qs + pad * 2 + U * 2, qy + pad + qs * 0.5 - 18, color=INK, anchor='l')
    hint2 = tmask('partymoa.com', KR, step(-1))
    paint(img, hint2, qx + qs + pad * 2 + U * 2, qy + pad + qs * 0.5 + 24, color=FAINT, anchor='l')
    band(img, x0, lower)


def main():
    img = sheet()
    tile1(img)
    tile2(img)
    tile3(img)
    specks(img, 160, int(H * 0.05), int(H * 0.60), SILVER, 0.55, seed=13, rmax=2.2)
    bloom(img, 0.62, 22, 0.28)
    fringe(img, 0.0016)
    out = np.clip(img, 0, 1)
    tiles = []
    for c in range(COLS):
        t = out[:, c * W:(c + 1) * W].copy()
        vignette(t, 0.38, 2.0)
        grain(t, 0.011)
        t = np.clip(t, 0, 1)
        im = Image.fromarray((t * 255).astype(np.uint8))
        im.save(os.path.join(OUT, f'C{c + 1}.jpg'), quality=94)
        tiles.append(im)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_크루격자.jpg'), quality=92)
    print('완료: C1~C3')


if __name__ == '__main__':
    main()
