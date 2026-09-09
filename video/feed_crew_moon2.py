"""
**AFTER MOON 라인업 셋 · 칸으로 나눈 판.** 한 사람이 한 칸.

    python feed_crew_moon2.py   →  out/moon/D1.jpg D2.jpg D3.jpg · _칸격자.jpg

## 앞 판(C1~C3)과 다른 점

앞 판은 누끼 셋을 한 무리로 겹쳤다. 겹치면 누가 누군지 눈으로 골라내야
한다. 이 판은 **칸을 나눈다.** 한 장에 두 칸, 세 장에 여섯 칸 —
디제이 다섯 + 정보 한 칸. 칸마다 번호 · 시간 · 사람 · 이름.

    D1   01 BHO     02 LYNN
    D2   03 LII     04 AROS
    D3   05 TS      값 · QR

BHO · LII 는 누끼가 없다. 그 칸은 이름을 크게 세운 글자 칸이다. 사진
칸과 글자 칸이 번갈아 서서 비어 보이지 않는다. 사진 오면 CUT 에 넣고
PHOTO 에 이름만 더하면 사진 칸이 된다.

## 이어지는 것

    시간 막대   22:00 → 02:10. 여섯 칸 아래를 한 줄로 지난다
    달          가운데 장 위. 빛이 옆 장으로 번진다
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

COLS = 3
RW = W * COLS
PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'
V = 1.0

PHOTO = {'LYNN', 'AROS', 'TS'}         # 누끼가 있는 사람
GUT = 24                               # 칸 사이
PW = (W - M * 2 - GUT) // 2            # 칸 폭
PY0 = 262                              # 칸 위
PY1 = 1000                             # 칸 아래
TL_Y = 1056                            # 시간 막대
PANEL = np.float32([0.052, 0.054, 0.064])


def mins(t):
    h, m = map(int, t.split(':'))
    if h < 12:
        h += 24
    return h * 60 + m


def panel_box(img, x0):
    """옅은 판 + 위에서 내리는 빛 + 얇은 테두리."""
    x1, y0, y1 = x0 + PW, PY0, PY1
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * 0.35 + PANEL * 0.65
    yy = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    img[y0:y1, x0:x1] += (1 - yy) ** 2 * np.float32([0.075, 0.078, 0.092])
    c = (SILVER * 0.28).tolist()
    cv2.rectangle(img, (x0, y0), (x1 - 1, y1 - 1), c, 1, cv2.LINE_AA)


def slot_label(img, x0, i, a, b):
    num = tmask(f'{i:02d}', BRAND_FONT, step(1), 0.20)
    paint(img, num, x0 + U * 2, PY0 + U * 2 + num.shape[0] / 2, color=INK, anchor='l')
    tm = tmask(f'{a} — {b}', BRAND_FONT, step(-2), 0.12)
    paint(img, tm, x0 + PW - U * 2, PY0 + U * 2 + num.shape[0] / 2, color=DIM, anchor='r')
    return PY0 + U * 2 + num.shape[0] + U * 2


def name_plate(img, x0, name, y_bottom, size_cap):
    size = min(fit(name, BRAND_FONT, PW - U * 4, 0.06), size_cap)
    m = tmask(name, BRAND_FONT, size, 0.06)
    plate = metal(*m.shape, m.astype(np.float32) / 255.0)
    cx = x0 + PW / 2
    y = int(y_bottom - m.shape[0])
    glow(img, m, cx, y + m.shape[0] / 2, SILVER, 0.20, 20, 'c', 'c')
    over(img, plate, int(cx - m.shape[1] / 2), y)
    return y


def photo_cell(img, x0, i, name, a, b):
    panel_box(img, x0)
    top = slot_label(img, x0, i, a, b)
    # 이름은 칸 바닥에서 올라온다. 사람은 이름 윗선까지 내려온다
    size = min(fit(max((n for n in PHOTO), key=len), BRAND_FONT, PW - U * 4, 0.06), 96)
    ny = PY1 - U * 3 - int(size * 1.15)
    base_h = int((ny + size * 0.5 - top) / 0.86)
    fig = crop_head(name, PW, base_h)
    a_ = np.clip((fig[..., 3] - 0.045) / 0.955, 0, 1).copy()
    px = sharpen(np.clip(fig[..., :3], 0, 1).copy(), 2.0, 0.6)
    a_, px = melt(a_, px, 0.26, len(name) * 31, V)
    # 칸 밖으로는 안 나간다
    n = min(PY1 - top, a_.shape[0])
    sub = img[:, x0:x0 + PW]
    composite(sub, top, a_[:n], px[:n])
    rim = rimlight(a_[:n], V, 1.4, 2.2, 0.28)
    sub[top:top + n] += rim[..., None] * SILVER * 0.55
    img[:, x0:x0 + PW] = sub
    name_plate(img, x0, name, PY1 - U * 3, size)
    # 장르는 안 적는다. 멤버 카드의 장르(EDM · Deep House)와 이 파티 장르
    # (tech house · bass house · techno)가 달라서 여기 적으면 어긋난다


def type_cell(img, x0, i, name, a, b):
    """사진 없는 사람. 이름이 칸을 채운다."""
    panel_box(img, x0)
    top = slot_label(img, x0, i, a, b)
    size = min(fit(name, BRAND_FONT, PW - U * 4, 0.06), 150)
    m = tmask(name, BRAND_FONT, size, 0.06)
    plate = metal(*m.shape, m.astype(np.float32) / 255.0)
    cx, cy = x0 + PW / 2, (top + PY1) / 2
    glow(img, m, cx, cy, SILVER, 0.22, 26, 'c', 'c')
    over(img, plate, int(cx - m.shape[1] / 2), int(cy - m.shape[0] / 2))
    sub = tmask('DJ', BRAND_FONT, step(-1), 0.30)
    paint(img, sub, cx, cy + m.shape[0] / 2 + U * 3, color=FAINT, anchor='c')
    # 얇은 십자. 빈 칸이 아니라 자리라는 표시
    for (px_, py_) in ((x0 + U * 3, PY1 - U * 3), (x0 + PW - U * 3, PY1 - U * 3)):
        cv2.line(img, (px_ - 8, py_), (px_ + 8, py_), (SILVER * 0.4).tolist(), 1, cv2.LINE_AA)
        cv2.line(img, (px_, py_ - 8), (px_, py_ + 8), (SILVER * 0.4).tolist(), 1, cv2.LINE_AA)


def info_cell(img, x0):
    panel_box(img, x0)
    y = PY0 + U * 3
    lab = tmask('AFTER MOON', BRAND_FONT, step(-1), 0.24)
    paint(img, lab, x0 + U * 2, y + lab.shape[0] / 2, color=DIM, anchor='l')
    y += lab.shape[0] + U * 3
    price = tmask('9,900', BRAND_FONT, min(fit('9,900', BRAND_FONT, PW - U * 4 - 40, 0.02), 110), 0.02)
    plate = metal(*price.shape, price.astype(np.float32) / 255.0)
    over(img, plate, x0 + U * 2, y)
    won = tmask('원', KRB, step(1))
    paint(img, won, x0 + U * 2 + price.shape[1] + 8, y + price.shape[0] - won.shape[0] / 2 - 4,
          color=INK, anchor='l')
    y += price.shape[0] + U * 2
    for line in ('남녀 같은 값', '웰컴샷 포함', '1차 30명 · 15:15', '9.26 토 22:00'):
        m = tmask(line, KR, step(0))
        paint(img, m, x0 + U * 2, y + m.shape[0] / 2, color=INK, anchor='l')
        y += m.shape[0] + U
    # QR
    qs = 200
    q = qr_build(PARTY_URL, 200, [0.06, 0.06, 0.08], [1.0, 1.0, 1.0], badge=False, error='m')
    qa = np.asarray(q.resize((qs, qs), Image.NEAREST).convert('RGB'), np.float32) / 255.0
    pad = 14
    qy = PY1 - U * 3 - qs - pad * 2
    qx = x0 + U * 2
    img[qy:qy + qs + pad * 2, qx:qx + qs + pad * 2] = 1.0
    img[qy + pad:qy + pad + qs, qx + pad:qx + pad + qs] = qa
    h1 = tmask('예매', KRB, step(0))
    h2 = tmask('QR', BRAND_FONT, step(-1), 0.2)
    paint(img, h1, qx + qs + pad * 2 + U, qy + pad + qs / 2 - 14, color=INK, anchor='l')
    paint(img, h2, qx + qs + pad * 2 + U, qy + pad + qs / 2 + 22, color=FAINT, anchor='l')


def timeline(img):
    """여섯 칸 아래를 지나는 시간 막대. 세 장을 잇는 줄."""
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
    for k, (n, a, b) in enumerate(LINEUP):
        xm = (xof(a) + xof(b)) // 2
        nm = tmask(n, BRAND_FONT, step(-3), 0.16)
        paint(img, nm, xm, TL_Y - 28, color=FAINT, anchor='c')


def sheet():
    img = sky(RW, H, [(0.0, (0.030, 0.030, 0.040)),
                      (0.45, (0.058, 0.058, 0.074)),
                      (1.0, (0.022, 0.022, 0.030))])
    starfield(img, 0, int(H * 0.5), n=420, seed=27)
    # 달은 가운데 장 위에서 살짝만. 머리글을 덮지 않게 위로 올린다
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
    cells = []                                     # (tile, side, kind, ...)
    order = list(LINEUP)
    slots = [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)]
    for (tile, side), (i, (n, a, b)) in zip(slots, enumerate(order, 1)):
        x0 = tile * W + M + side * (PW + GUT)
        if n in PHOTO:
            photo_cell(img, x0, i, n, a, b)
        else:
            type_cell(img, x0, i, n, a, b)
    info_cell(img, 2 * W + M + PW + GUT)
    timeline(img)
    lower = lower_h()
    for t in range(COLS):
        header(img, t * W, t + 1)
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
        im.save(os.path.join(OUT, f'D{c + 1}.jpg'), quality=94)
        tiles.append(im)
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_칸격자.jpg'), quality=92)
    print('완료: D1~D3')


if __name__ == '__main__':
    main()
