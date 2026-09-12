"""
**AFTER MOON · 블랙아웃 한 줄.** 릴스 하나 + 피드 둘. 지난 파티에서 다음 파티로.

    python feed_moon_row.py   →  out/moon/M_지난다음.mp4   (릴스 12초, 무음)
                                 out/moon/MC.jpg            (릴스 커버 1080×1920)
                                 out/moon/M1.jpg M2.jpg     (피드 1080×1350)
                                 out/moon/_한줄격자.jpg

## 한 줄이 한 판

격자에서 [릴스 커버 | M1 | M2]. 올리는 순서 M2 → M1 → 릴스.
셋을 잇는 건 **지난 파티 사진 한 장**이다. 루프탑 풀 와이드컷을 은색으로
빼서 세 칸 아래쪽에 깔고, 달이 가운데 칸에서 그 위로 뜬다.

    커버   AFTER SUNSET → AFTER MOON   지난 파티에서 다음 파티로
    M1     09.26 SAT                   22:00 – 02:10 · 압구정 딥하우즈 · 라인업
    M2     9,900                       웰컴샷 · 1차 30명 · 15:15 · QR

## 릴스

지난 파티 사진 여섯 장이 1초씩 넘어가고, 다음 파티가 뜬다. 무음 —
인스타 음원 얹게. 컷이 1초 고정이라 어떤 곡에도 안 어긋난다.

## 색

판은 검정·은색. 사진도 은색으로 뺀다. 색은 사람에게만 — 여기 사람은
멀리 있으니 사진 전체를 은색으로 두는 게 맞다.
"""
import os

import cv2
import numpy as np
from PIL import Image

from fest_kit import sky, specks, vignette
from fonts import KR, KRB
from poster_kit import bloom, fit, glow, grain, paint, tmask
from poster_lineup import LINEUP
from poster_moon import (BRAND_FONT, DATE, LOGO, OUT, TITLE, godrays, metal,
                         moonface, over, starfield)
from qr import build as qr_build
from feed_crew_moon import (DIM, FAINT, INK, M, RULE, SILVER, U, BOT, TOP, W, H as FH,
                            band, header, lower_h, step)
from reel_moon import (DUR, FPS, NF, SAFE_BOT, SAFE_TOP, darken, end_card, fade,
                       finish, put, text_rgba)
from reel_moon import DIM as DIM_T, FAINT as FAINT_T, INK as INK_T   # 글자용 RGBA 튜플
from reel_moon2 import encode_silent, logo
from reel_partymoa2 import kb

H = 1920
COLS = 3
RW = W * COLS
BAND_Y = (H - FH) // 2
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'partymoa', '_photos')
PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'
LAST = 'AFTER SUNSET'


def silverize(rgb, keep=0.22):
    """사진을 은색으로. 채도를 거의 빼고 푸른 기를 살짝."""
    g = rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114
    mono = np.repeat(g[..., None], 3, 2) * SILVER / SILVER.mean()
    return rgb * keep + mono * (1 - keep)


def strip(y0, y1):
    """지난 파티 와이드컷을 세 칸 폭으로. 위아래는 검정으로 녹는다."""
    im = cv2.imread(os.path.join(PH, '029.jpg'))[..., ::-1]
    h, w = im.shape[:2]
    bh = int(w * (y1 - y0) / RW)
    top = int(np.clip(h * 0.55 - bh / 2, 0, h - bh))
    a = np.asarray(cv2.resize(im[top:top + bh], (RW, y1 - y0), interpolation=cv2.INTER_AREA),
                   np.float32) / 255.0
    a = silverize(a) * 0.62
    yy = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    a *= np.clip(yy / 0.22, 0, 1) * np.clip((1 - yy) / 0.30, 0, 1)
    return a


def sheet():
    img = sky(RW, FH, [(0.0, (0.030, 0.030, 0.040)),
                       (0.45, (0.058, 0.058, 0.074)),
                       (1.0, (0.022, 0.022, 0.030))])
    starfield(img, 0, int(FH * 0.5), n=420, seed=29)
    # 달. 가운데 칸, 사진 띠 위로 뜬다
    MR = int(W * 0.30)
    cx, my = RW * 0.5, 830          # 사진 띠(640~1130) 위로 반쯤 떠서, 위 글자는 안 덮는다
    mf = moonface(MR)
    mf[..., :3] *= 0.62
    over(img, mf, int(cx) - MR, my - MR)
    godrays(img, cx, my, MR, seed=9, a=0.14)
    # 사진 띠. 셋을 잇는 한 장
    y0, y1 = 640, 1130
    s = strip(y0, y1)
    # 띠는 달을 가린다. 달은 띠 위로 머리만 내민다
    yy = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    m = np.clip(yy / 0.22, 0, 1) * np.clip((1 - yy) / 0.30, 0, 1)
    img[y0:y1] = img[y0:y1] * (1 - m) + s
    return img


def feeds():
    img = sheet()
    lower = lower_h()

    # ── 커버 (칸 0). 지난 → 다음
    x0 = 0
    lh = header(img, x0, 1)
    y = lh + U * 9
    lab = tmask('지난 파티 8.29', KR, step(-1))
    paint(img, lab, x0 + M, y + lab.shape[0] / 2, color=DIM, anchor='l')
    y += lab.shape[0] + U
    last = tmask(LAST, BRAND_FONT, min(fit(LAST, BRAND_FONT, W - M * 2, 0.06), 84), 0.06)
    paint(img, last, x0 + M, y + last.shape[0] / 2, color=FAINT, anchor='l')
    y += last.shape[0] + U * 2
    arrow = tmask('↓  다음 파티 9.26', KR, step(-1))
    paint(img, arrow, x0 + M, y + arrow.shape[0] / 2, color=DIM, anchor='l')
    y += arrow.shape[0] + U
    ttl = tmask(TITLE, BRAND_FONT, min(fit(TITLE, BRAND_FONT, W - M * 2, 0.06), 110), 0.06)
    plate = metal(*ttl.shape, ttl.astype(np.float32) / 255.0)
    glow(img, ttl, x0 + M + ttl.shape[1] / 2, y + ttl.shape[0] / 2, SILVER, 0.22, 26, 'c', 'c')
    over(img, plate, x0 + M, y)
    # 재생 표시 — 이 칸이 릴스라는 신호. 사진 띠 위
    py = 1160
    cv2.fillPoly(img, [np.array([[x0 + M, py], [x0 + M, py + 44], [x0 + M + 36, py + 22]])], INK.tolist(), cv2.LINE_AA)
    rl = tmask('릴스 · 12초', KR, step(-1))
    paint(img, rl, x0 + M + 54, py + 22, color=DIM, anchor='l')
    band(img, x0, lower)

    # ── M1 (칸 1). 날짜 · 장소 · 라인업
    x0 = W
    lh = header(img, x0, 2)
    y = lh + U * 9
    d = tmask(DATE, BRAND_FONT, min(fit(DATE, BRAND_FONT, W - M * 2, 0.04), 150), 0.04)
    plate = metal(*d.shape, d.astype(np.float32) / 255.0)
    glow(img, d, x0 + M + d.shape[1] / 2, y + d.shape[0] / 2, SILVER, 0.22, 26, 'c', 'c')
    over(img, plate, x0 + M, y)
    y += d.shape[0] + U * 2
    t1 = tmask('22:00 — 02:10 · 압구정 딥하우즈', KRB, step(1))
    paint(img, t1, x0 + M, y + t1.shape[0] / 2, color=INK, anchor='l')
    y += t1.shape[0] + U
    t2 = tmask('  ·  '.join(n for n, _, _ in LINEUP), BRAND_FONT, step(-1), 0.14)
    paint(img, t2, x0 + M, y + t2.shape[0] / 2, color=DIM, anchor='l')
    band(img, x0, lower)

    # ── M2 (칸 2). 값 · 조건 · QR
    x0 = 2 * W
    lh = header(img, x0, 3)
    y = lh + U * 9
    p = tmask('9,900', BRAND_FONT, 150, 0.02)
    plate = metal(*p.shape, p.astype(np.float32) / 255.0)
    glow(img, p, x0 + M + p.shape[1] / 2, y + p.shape[0] / 2, SILVER, 0.22, 26, 'c', 'c')
    over(img, plate, x0 + M, y)
    won = tmask('원', KRB, step(3))
    paint(img, won, x0 + M + p.shape[1] + U, y + p.shape[0] - won.shape[0] / 2 - 6, color=INK, anchor='l')
    y += p.shape[0] + U * 2
    c1 = tmask('웰컴샷 포함 · 남녀 같은 값', KRB, step(1))
    paint(img, c1, x0 + M, y + c1.shape[0] / 2, color=INK, anchor='l')
    y += c1.shape[0] + U
    c2 = tmask('1차 30명 · 남녀 15 : 15 · 한쪽 차면 마감', KR, step(0))
    paint(img, c2, x0 + M, y + c2.shape[0] / 2, color=DIM, anchor='l')
    # QR. 사진 띠 오른쪽 아래 흰 판
    qs, pad = 150, 12
    q = qr_build(PARTY_URL, 150, [0.06, 0.06, 0.08], [1.0, 1.0, 1.0], badge=False, error='m')
    qa = np.asarray(q.resize((qs, qs), Image.NEAREST).convert('RGB'), np.float32) / 255.0
    qx, qy = x0 + W - M - qs - pad * 2, 1130 - qs - pad * 2 - U * 2
    img[qy:qy + qs + pad * 2, qx:qx + qs + pad * 2] = 1.0
    img[qy + pad:qy + pad + qs, qx + pad:qx + pad + qs] = qa
    hint = tmask('카메라로 찍으면 예매', KR, step(-1))
    paint(img, hint, qx - U, qy + pad + qs / 2, color=INK, anchor='r')
    band(img, x0, lower)

    specks(img, 120, int(FH * 0.04), int(FH * 0.40), SILVER, 0.5, seed=17, rmax=2.0)
    bloom(img, 0.62, 22, 0.24)
    out = np.clip(img, 0, 1)
    tiles = []
    for c, name in enumerate(('MC', 'M1', 'M2')):
        t = out[:, c * W:(c + 1) * W].copy()
        vignette(t, 0.32, 2.0)
        grain(t, 0.011)
        im = Image.fromarray((np.clip(t, 0, 1) * 255).astype(np.uint8))
        if name == 'MC':
            full = Image.new('RGB', (W, H), (8, 8, 10))
            full.paste(im, (0, BAND_Y))
            full.save(os.path.join(OUT, 'MC.jpg'), quality=94)
        else:
            im.save(os.path.join(OUT, f'{name}.jpg'), quality=94)
        tiles.append(im)
    g = Image.new('RGB', (W * 3 + 16, FH * 2 + 8), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    for i, name in enumerate(('E1', 'E2', 'E3')):
        p = os.path.join(OUT, f'{name}.jpg')
        if os.path.exists(p):
            g.paste(Image.open(p), (i * (W + 8), FH + 8))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_한줄격자.jpg'), quality=92)
    print('피드 완료: MC M1 M2')


# ══════════════════════════════════════════════════════════
#  릴스 — 지난 파티 여섯 컷 → 다음 파티. 무음, 1초 컷
# ══════════════════════════════════════════════════════════

def reel():
    cuts = [('209', (1.0, 1.10), (0, 0)), ('083', (1.1, 1.0), (-0.3, 0)),
            ('184', (1.0, 1.12), (0, 0.3)), ('262', (1.05, 1.15), (0, -0.2)),
            ('221', (1.0, 1.1), (0, 0)), ('244', (1.12, 1.0), (0, 0))]
    per = 1.0
    t_cut0 = 2.4
    t_next = t_cut0 + per * len(cuts)
    t_end = 10.4
    lab_last = text_rgba('지난 파티 · 8.29', KR, step(0), DIM_T)
    ttl_last = text_rgba(LAST, BRAND_FONT, step(4), INK_T, 0.10)
    lab_next = text_rgba('다음 파티', KR, step(0), DIM_T)
    ttl_next = text_rgba(TITLE, BRAND_FONT, step(5), INK_T, 0.10)
    l1 = text_rgba(f'{DATE} · 22:00 — 02:10', KRB, step(1), INK_T)
    l2 = text_rgba('압구정 딥하우즈 · 9,900원 · 1차 30명', KR, step(0), DIM_T)

    def frames():
        for i in range(NF):
            t = i / FPS
            if t < t_cut0:
                img = silverize(kb('044', t / t_cut0, (1.0, 1.08), (0, 0), dim=0.5), 0.15)
                darken(img, int(H * 0.36), int(H * 0.60), 0.4)
                put(img, lab_last, (W - lab_last.shape[1]) / 2, H * 0.42, fade(t, 0.0))
                put(img, ttl_last, (W - ttl_last.shape[1]) / 2, H * 0.42 + 60, fade(t, 0.2))
            elif t < t_next:
                j = min(len(cuts) - 1, int((t - t_cut0) / per))
                name, zm, pn = cuts[j]
                k = (t - t_cut0 - j * per) / per
                img = silverize(kb(name, k, zm, pn), 0.35)
                n = text_rgba(f'{j + 1:02d} / {len(cuts):02d}', BRAND_FONT, step(-1), DIM_T, 0.2)
                put(img, n, W - M - n.shape[1], SAFE_TOP + U * 4)
            else:
                img = silverize(kb('029', (t - t_next) / (DUR - t_next), (1.0, 1.06), (0, 0), dim=0.55), 0.12)
                darken(img, int(H * 0.32), int(H * 0.66), 0.45)
                if t < t_end:
                    put(img, lab_next, (W - lab_next.shape[1]) / 2, H * 0.36, fade(t, t_next))
                    put(img, ttl_next, (W - ttl_next.shape[1]) / 2, H * 0.36 + 56, fade(t, t_next + 0.1))
                    put(img, l1, (W - l1.shape[1]) / 2, H * 0.36 + 56 + ttl_next.shape[0] + U * 2, fade(t, t_next + 0.3))
                    put(img, l2, (W - l2.shape[1]) / 2, H * 0.36 + 56 + ttl_next.shape[0] + U * 2 + l1.shape[0] + U, fade(t, t_next + 0.5))
            logo(img, M, SAFE_TOP + U * 2, 0.20)
            end_card(img, t, t_end)
            yield finish(img)

    encode_silent('M_지난다음', frames())


if __name__ == '__main__':
    feeds()
    reel()
