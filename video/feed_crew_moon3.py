"""
**AFTER MOON 라인업 셋 · 한 장에 전원.** 첫 장이 여섯 칸 격자다.

    python feed_crew_moon3.py   →  out/moon/E1.jpg E2.jpg E3.jpg · _전원격자.jpg

## 첫 장

페스티벌 라인업 판의 문법이다 — 칸을 나누고 칸마다 사람 하나, 날짜·이름.
우리는 날짜 대신 시간이다. 한 파티 다섯 명.

    01 BHO    02 LYNN   03 LII
    04 AROS   05 TS     일시·장소

여섯째 칸은 일시·장소. 다섯이라 한 칸이 남는데 비워 두면 빠진 사람처럼
보인다. BHO · LII 는 누끼가 없어 이름 칸이다.

## 둘째 · 셋째 장

    E2   TIME TABLE   등뼈 하나에 다섯 마디
    E3   9,900원      조건 · QR

## 이어지는 것

    시간 막대   y 1056. 세 장 아래를 한 줄로
    달          가운데 장 위
    아래 띠     같은 높이, 같은 글
"""
import os

import cv2
import numpy as np
from PIL import Image

from fest_kit import sky, specks, vignette
from fonts import KR, KRB
from poster_crew import crop_head, rimlight
from poster_dj4 import fringe, melt, sharpen
from poster_dj_moon import composite, ring
from poster_kit import bloom, fit, glow, grain, paint, tmask
from poster_lineup import LINEUP
from poster_lounge import bokeh
from poster_moon import (BRAND_FONT, OUT, godrays, metal, moonface, over,
                         starfield)
from qr import build as qr_build
from feed_crew_moon import (DIM, FAINT, INK, M, RULE, SILVER, U, BOT, TOP, W,
                            H, band, header, lower_h, step)
from feed_crew_moon2 import PANEL, PHOTO, mins

COLS = 3
RW = W * COLS
PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'
V = 1.0
TL_Y = 1056
GUT = 16
GY0, GY1 = 352, 1010                   # 격자 위·아래
CW = (W - M * 2 - GUT * 2) // 3        # 칸 폭
CH = (GY1 - GY0 - GUT) // 2            # 칸 높이


def box(img, x0, y0, w, h):
    x1, y1 = x0 + w, y0 + h
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * 0.35 + PANEL * 0.65
    yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    img[y0:y1, x0:x1] += (1 - yy) ** 2 * np.float32([0.075, 0.078, 0.092])
    cv2.rectangle(img, (x0, y0), (x1 - 1, y1 - 1), (SILVER * 0.28).tolist(), 1, cv2.LINE_AA)


def label(img, x0, y0, w, i, a):
    num = tmask(f'{i:02d}', BRAND_FONT, step(0), 0.20)
    paint(img, num, x0 + U, y0 + U + num.shape[0] / 2, color=INK, anchor='l')
    tm = tmask(a, BRAND_FONT, step(-3), 0.12)
    paint(img, tm, x0 + w - U, y0 + U + num.shape[0] / 2, color=DIM, anchor='r')
    return y0 + U + num.shape[0] + U


def plate(img, x0, w, name, y_bottom, cap):
    size = min(fit(name, BRAND_FONT, w - U * 2, 0.06), cap)
    m = tmask(name, BRAND_FONT, size, 0.06)
    p = metal(*m.shape, m.astype(np.float32) / 255.0)
    cx = x0 + w / 2
    y = int(y_bottom - m.shape[0])
    glow(img, m, cx, y + m.shape[0] / 2, SILVER, 0.20, 16, 'c', 'c')
    over(img, p, int(cx - m.shape[1] / 2), y)
    return y


def photo(img, x0, y0, w, h, i, name, a):
    box(img, x0, y0, w, h)
    top = label(img, x0, y0, w, i, a)
    # 이름 크기는 제일 긴 이름(LYNN·AROS) 기준으로 전원 같게
    cap = min(fit('AROS', BRAND_FONT, w - U * 2, 0.06), 52)
    ny = y0 + h - U * 2 - int(cap * 1.15)
    # 얼굴이 칸을 채워야 한다. 머리·어깨 높이를 칸보다 크게 잡고 아래는
    # 이름 판과 칸 바닥이 자른다 — 참고한 페스티벌 판이 이렇게 한다
    top -= U
    base_h = int((ny + cap * 0.5 - top) / 0.84 * 1.32)
    fig = crop_head(name, w, base_h)
    a_ = np.clip((fig[..., 3] - 0.045) / 0.955, 0, 1).copy()
    px = sharpen(np.clip(fig[..., :3], 0, 1).copy(), 1.6, 0.6)
    a_, px = melt(a_, px, 0.24, len(name) * 31, V)
    n = min(y0 + h - top, a_.shape[0])
    sub = img[:, x0:x0 + w]
    composite(sub, top, a_[:n], px[:n])
    rim = rimlight(a_[:n], V, 1.2, 2.0, 0.28)
    sub[top:top + n] += rim[..., None] * SILVER * 0.55
    img[:, x0:x0 + w] = sub
    plate(img, x0, w, name, y0 + h - U * 2, cap)


def typo(img, x0, y0, w, h, i, name, a):
    box(img, x0, y0, w, h)
    top = label(img, x0, y0, w, i, a)
    size = min(fit(name, BRAND_FONT, w - U * 2, 0.06), 78)
    m = tmask(name, BRAND_FONT, size, 0.06)
    p = metal(*m.shape, m.astype(np.float32) / 255.0)
    cx, cy = x0 + w / 2, (top + y0 + h) / 2
    glow(img, m, cx, cy, SILVER, 0.22, 20, 'c', 'c')
    over(img, p, int(cx - m.shape[1] / 2), int(cy - m.shape[0] / 2))
    sub = tmask('DJ', BRAND_FONT, step(-2), 0.30)
    paint(img, sub, cx, cy + m.shape[0] / 2 + U * 2, color=FAINT, anchor='c')


def info(img, x0, y0, w, h):
    box(img, x0, y0, w, h)
    cx = x0 + w / 2
    y = y0 + U * 3
    for text, f, sz, col in (('09.26', BRAND_FONT, step(4), INK),
                             ('SAT', BRAND_FONT, step(-1), DIM),
                             ('22:00 — 02:10', BRAND_FONT, step(-2), INK),
                             ('압구정', KRB, step(1), INK),
                             ('딥하우즈', KRB, step(1), INK)):
        m = tmask(text, f, sz, 0.10 if f == BRAND_FONT else 0)
        paint(img, m, cx, y + m.shape[0] / 2, color=col, anchor='c')
        y += m.shape[0] + (U if f == KRB else int(U * 1.4))


def tile1(img):
    x0 = 0
    lh_bottom = header(img, x0, 1)
    title = tmask('LINE UP', BRAND_FONT, min(fit('LINE UP', BRAND_FONT, W - M * 2, 0.16), 96), 0.16)
    p = metal(*title.shape, title.astype(np.float32) / 255.0)
    ty = lh_bottom + U * 5
    glow(img, title, x0 + W / 2, ty + title.shape[0] / 2, SILVER, 0.18, 22, 'c', 'c')
    over(img, p, int(x0 + W / 2 - title.shape[1] / 2), ty)

    cells = [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)]
    for (c, r), (i, (n, a, b)) in zip(cells, enumerate(LINEUP, 1)):
        cx0 = x0 + M + c * (CW + GUT)
        cy0 = GY0 + r * (CH + GUT)
        (photo if n in PHOTO else typo)(img, cx0, cy0, CW, CH, i, n, a)
    info(img, x0 + M + 2 * (CW + GUT), GY0 + CH + GUT, CW, CH)


def tile2(img):
    x0 = W
    lh_bottom = header(img, x0, 2)
    title = tmask('TIME TABLE', BRAND_FONT, step(3), 0.20)
    ty = lh_bottom + U * 5
    paint(img, title, x0 + M, ty + title.shape[0] / 2, color=INK, anchor='l')
    y_top = ty + title.shape[0] + U * 4
    y_bot = TL_Y - U * 6
    sx = x0 + M + 14
    cv2.line(img, (sx, y_top), (sx, y_bot), (SILVER * 0.55).tolist(), 2, cv2.LINE_AA)
    n = len(LINEUP)
    gap = (y_bot - y_top) / (n - 1 + 0.6)
    size = min(fit(max((nm for nm, _, _ in LINEUP), key=len), BRAND_FONT, W * 0.62, 0.06), 104)
    for i, (nm, a, b) in enumerate(LINEUP):
        cy = int(y_top + gap * (i + 0.3))
        cv2.circle(img, (sx, cy), 7, INK.tolist(), -1, cv2.LINE_AA)
        cv2.circle(img, (sx, cy), 13, (SILVER * 0.6).tolist(), 1, cv2.LINE_AA)
        tm = tmask(f'{a} — {b}', BRAND_FONT, step(-1), 0.10)
        paint(img, tm, sx + 44, cy - size * 0.42, color=DIM, anchor='l')
        nm_m = tmask(nm, BRAND_FONT, size, 0.06)
        p = metal(*nm_m.shape, nm_m.astype(np.float32) / 255.0)
        over(img, p, sx + 44, int(cy - size * 0.42 + tm.shape[0] + U * 0.8))
        num = tmask(f'{i + 1:02d}', BRAND_FONT, step(-1), 0.20)
        paint(img, num, x0 + W - M, cy, color=FAINT, anchor='r')


def tile3(img):
    x0 = 2 * W
    lh_bottom = header(img, x0, 3)
    y = lh_bottom + U * 5
    price = tmask('9,900', BRAND_FONT, 170, 0.02)
    p = metal(*price.shape, price.astype(np.float32) / 255.0)
    glow(img, price, x0 + M + price.shape[1] / 2, y + price.shape[0] / 2, SILVER, 0.20, 26, 'c', 'c')
    over(img, p, x0 + M, y)
    won = tmask('원', KRB, step(3))
    paint(img, won, x0 + M + price.shape[1] + U, y + price.shape[0] - won.shape[0] / 2 - 6,
          color=INK, anchor='l')
    y += price.shape[0] + U * 2
    sub = tmask('남녀 같은 값 · 웰컴샷 포함', KR, step(0))
    paint(img, sub, x0 + M, y + sub.shape[0] / 2, color=DIM, anchor='l')
    y += sub.shape[0] + U * 4
    facts = [('일시', '9.26 토 22:00 — 02:10'), ('장소', '압구정 딥하우즈'),
             ('1차', '30명 · 남녀 15:15'), ('예매', '파티모아 · 입금 24시간')]
    for lab, val in facts:
        cv2.line(img, (x0 + M, y), (x0 + W - M, y), RULE.tolist(), 1, cv2.LINE_AA)
        y += int(U * 1.6)
        lm = tmask(lab, KR, step(-1))
        vm = tmask(val, KRB, step(1))
        paint(img, lm, x0 + M, y + vm.shape[0] / 2, color=FAINT, anchor='l')
        paint(img, vm, x0 + M + 120, y + vm.shape[0] / 2, color=INK, anchor='l')
        y += vm.shape[0] + int(U * 1.6)
    cv2.line(img, (x0 + M, y), (x0 + W - M, y), RULE.tolist(), 1, cv2.LINE_AA)
    qs = 196
    q = qr_build(PARTY_URL, 196, [0.06, 0.06, 0.08], [1.0, 1.0, 1.0], badge=False, error='m')
    qa = np.asarray(q.resize((qs, qs), Image.NEAREST).convert('RGB'), np.float32) / 255.0
    pad = 16
    qy = TL_Y - U * 6 - qs - pad * 2
    qx = x0 + M
    img[qy:qy + qs + pad * 2, qx:qx + qs + pad * 2] = 1.0
    img[qy + pad:qy + pad + qs, qx + pad:qx + pad + qs] = qa
    h1 = tmask('카메라로 찍으면 예매 화면', KR, step(0))
    h2 = tmask('partymoa.com', KR, step(-1))
    paint(img, h1, qx + qs + pad * 2 + U * 2, qy + pad + qs / 2 - 16, color=INK, anchor='l')
    paint(img, h2, qx + qs + pad * 2 + U * 2, qy + pad + qs / 2 + 22, color=FAINT, anchor='l')


def timeline(img):
    x_a, x_b = M, RW - M
    t0, t1 = mins('22:00'), mins('02:10')

    def xof(t):
        return int(x_a + (x_b - x_a) * (mins(t) - t0) / (t1 - t0))

    cv2.line(img, (x_a, TL_Y), (x_b, TL_Y), (SILVER * 0.45).tolist(), 2, cv2.LINE_AA)
    marks = [a for _, a, _ in LINEUP] + ['02:10']
    for k, t in enumerate(marks):
        x = xof(t)
        cv2.line(img, (x, TL_Y - 10), (x, TL_Y + 10), (SILVER * 0.7).tolist(), 2, cv2.LINE_AA)
        tm = tmask(t, BRAND_FONT, step(-3), 0.12)
        anchor = 'l' if k == 0 else 'r' if k == len(marks) - 1 else 'c'
        paint(img, tm, x, TL_Y + 30, color=DIM, anchor=anchor)
    for n, a, b in LINEUP:
        xm = (xof(a) + xof(b)) // 2
        nm = tmask(n, BRAND_FONT, step(-3), 0.16)
        paint(img, nm, xm, TL_Y - 28, color=FAINT, anchor='c')


def sheet():
    img = sky(RW, H, [(0.0, (0.030, 0.030, 0.040)),
                      (0.45, (0.058, 0.058, 0.074)),
                      (1.0, (0.022, 0.022, 0.030))])
    starfield(img, 0, int(H * 0.5), n=420, seed=28)
    MR = int(W * 0.26)
    cx, my = RW * 0.5, 40
    mf = moonface(MR)
    mf[..., :3] *= 0.50
    over(img, mf, int(cx) - MR, my - MR)
    godrays(img, cx, my, MR, seed=8, a=0.16)
    ring(img, cx, my, MR + 18, 2, 0.45)
    bokeh(img, n=34, seed=4, y0=0.0, y1=0.5)
    return img


def main():
    img = sheet()
    tile1(img)
    tile2(img)
    tile3(img)
    timeline(img)
    lower = lower_h()
    for t in range(COLS):
        band(img, t * W, lower)
    specks(img, 140, int(H * 0.04), int(H * 0.30), SILVER, 0.5, seed=15, rmax=2.0)
    bloom(img, 0.62, 22, 0.26)
    fringe(img, 0.0014)
    out = np.clip(img, 0, 1)
    tiles = []
    for c in range(COLS):
        t = out[:, c * W:(c + 1) * W].copy()
        vignette(t, 0.34, 2.0)
        grain(t, 0.011)
        im = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8))
        im.save(os.path.join(OUT, f'E{c + 1}.jpg'), quality=94)
        tiles.append(im)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_전원격자.jpg'), quality=92)
    print('완료: E1~E3')


if __name__ == '__main__':
    main()
