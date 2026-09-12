"""
**파티모아 · AFTER MOON 한 줄.** 릴스 하나 + 피드 둘. 딥하우즈 영상으로.

    python reel_partymoa3.py   →  out/partymoa/T_딥하우즈.mp4  (릴스 12초, 곡 있음)
                                  out/partymoa/TC.jpg           (릴스 커버 1080×1920)
                                  out/partymoa/T1.jpg T2.jpg    (피드 1080×1350)
                                  out/partymoa/_딥하우즈격자.jpg

## 한 줄이 한 판

[릴스 커버 | T1 | T2]. 올리는 순서 T2 → T1 → 릴스.
셋을 잇는 건 **딥하우즈 영상 띠**. 간판 · 홀 · 사람들 컷을 세 칸 아래쪽에
같은 높이로 깔고 보라로 덮는다. 노란 선 하나가 셋을 지난다 — 앞 줄들과 같은 규칙.

    커버   이 파티, 여기서   간판 컷
    T1     9.26 토 22:00     압구정 딥하우즈 · 라인업
    T2     9,900원           웰컴샷 · 1차 30명 · 15:15 · QR

## 릴스

"이 파티 어디서 하냐면" → 간판 → 매장 컷 0.5초씩 → 조건 → 예매는 앱에서.
디스코 하우스 118. 컷은 0.5초 고정이라 박이 달라도 안 어긋난다.
"""
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

from feed_partymoa import ACC, ACCENT, BRAND, DEEP, DOTS, M, WHITE, font
from feed_partymoa9 import cta_plate, head
from fonts import KR, KRB
from qr import build as qr_build
from render import out_expo
from reel_moon import clip_frames, footage
from reel_moon2 import SHOTS_ALL
from reel_partymoa import (DUR, FPS, H, INK, INK_D, NF, OUT, SAFE_BOT, SAFE_TOP,
                           SUB, U, W, encode, end_card, fade, finish, fit_text,
                           logo_rgba, plate, pop, put, text)
from reel_somesoul import footer, logo_line

PARTY_URL = 'https://www.partymoa.com/party/after-moon-20260926'
BGM = 'bgm_disco.wav'
PURPLE = np.float32(BRAND) / 255
DEEPC = np.float32(DEEP) / 255
FH = 1350
BAND_Y = (H - FH) // 2
SHOT = dict((n, (t0, d)) for n, t0, d in SHOTS_ALL)
BAND_CUTS = [('s_sign', 0.55, 0.42), ('s_room', 0.5, 0.50), ('s_crowd', 0.6, 0.55)]


def frame_of(name, frac):
    t0, d = SHOT[name]
    files = clip_frames(name, t0, d)
    return footage(files[min(len(files) - 1, int(len(files) * frac))])


def purple_tint(rgb, k=0.45):
    """영상을 보라 쪽으로. 밝기는 남기고 색만 앱 색으로 끌어온다."""
    g = rgb[..., 0] * .299 + rgb[..., 1] * .587 + rgb[..., 2] * .114
    tint = g[..., None] * (PURPLE * 1.6)
    return rgb * (1 - k) + np.clip(tint, 0, 1) * k


def row_sheet():
    RW = W * 3
    yy = np.linspace(0, 1, FH, dtype=np.float32)[:, None, None]
    a = PURPLE * (1 - yy ** 1.4) + DEEPC * (yy ** 1.4)
    a = np.repeat(a, RW, axis=1)
    # 영상을 칸마다 꽉 채운다. 앞 릴스 줄(RDA·REA·RFA)과 같은 방식 —
    # 보라로 덮고 위쪽은 어둡게 눌러 글자가 산다
    for c, (name, frac, cy) in enumerate(BAND_CUTS):
        fr = frame_of(name, frac)                       # 1080×1920
        top = int(np.clip(fr.shape[0] * (cy + 0.05) - FH / 2, 0, fr.shape[0] - FH))
        tile = purple_tint(fr[top:top + FH, :W], 0.55)
        vy = np.linspace(0, 1, FH, dtype=np.float32)[:, None, None]
        shade = 0.30 + 0.55 * np.clip((0.62 - vy) / 0.45, 0, 1)      # 위 0.85 → 아래 0.30 어둡게
        a[:, c * W:(c + 1) * W] = a[:, c * W:(c + 1) * W] * shade + tile * (1 - shade)
    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    d.line([(M, int(FH * 0.86)), (RW - M, int(FH * 0.86))], fill=WHITE + (110,), width=2)
    ly = int(FH * 0.60)
    d.line([(0, ly), (RW, ly)], fill=ACCENT + (255,), width=6)
    return pil, ly


def feeds():
    sheet, ly = row_sheet()
    tiles = {}

    # ── 커버 (칸 0)
    b = sheet.crop((0, 0, W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, ['이 파티', '여기서'], '압구정 딥하우즈 · 9.26 토', 150, 240)
    d.polygon([(M, ly + 40), (M, ly + 92), (M + 44, ly + 66)], fill=ACCENT)
    d.text((M + 64, ly + 44), '릴스 · 12초', font=font(KR, 34), fill=WHITE + (220,))
    cta_plate(d, '예매 → 프로필 링크', int(FH * 0.86) - 92 - 48)
    footer(d, 0)
    full = Image.new('RGB', (W, H), DEEP)
    full.paste(b.convert('RGB'), (0, BAND_Y))
    full.save(os.path.join(OUT, 'TC.jpg'), quality=94)
    tiles['TC'] = b.convert('RGB')

    # ── T1 (칸 1)
    b = sheet.crop((W, 0, 2 * W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, ['9.26 토', '22:00'], '압구정 딥하우즈 · 02:10 까지', 150, 240)
    fs = font(KRB, 38)
    d.text((M, y + 24), 'BHO · LYNN · LII · AROS · TS', font=fs, fill=WHITE)
    d.text((M, y + 24 + 54), 'TECH HOUSE · BASS HOUSE · TECHNO', font=font(KR, 30), fill=WHITE + (190,))
    assert y + 24 + 54 + 40 < ly - 8
    cta_plate(d, '라인업 보기 → 프로필 링크', int(FH * 0.86) - 92 - 48)
    footer(d, 0)
    b.convert('RGB').save(os.path.join(OUT, 'T1.jpg'), quality=94)
    tiles['T1'] = b.convert('RGB')

    # ── T2 (칸 2)
    b = sheet.crop((2 * W, 0, 3 * W, FH)).convert('RGBA')
    d = ImageDraw.Draw(b)
    logo_line(d, M, 96)
    y = head(d, ['9,900원'], '웰컴샷 포함 · 남녀 같은 값', 150, 300)
    fs = font(KRB, 38)
    for k, line in enumerate(('1차 30명 · 남녀 15 : 15', '한쪽 차면 그쪽부터 마감', '입금 24시간 · 안 하면 자동 취소')):
        yy = y + 24 + k * 54
        d.ellipse([M, yy + 12, M + 16, yy + 28], fill=ACCENT)
        d.text((M + 34, yy), line, font=fs, fill=WHITE)
    assert yy + 44 < ly - 8
    # QR. 띠 오른쪽 아래
    qs, pad = 150, 12
    q = qr_build(PARTY_URL, 150, [0.08, 0.04, 0.24], [1.0, 1.0, 1.0], badge=False, error='m')
    q = q.resize((qs, qs), Image.NEAREST).convert('RGBA')
    box = Image.new('RGBA', (qs + pad * 2, qs + pad * 2), (255, 255, 255, 255))
    box.paste(q, (pad, pad))
    b.alpha_composite(box, (W - M - qs - pad * 2, 1090 - qs - pad * 2 - U * 2))
    d.text((W - M - qs - pad * 2 - 12 - d.textlength('카메라로 찍으면 예매', font=font(KR, 26)),
            1090 - qs - pad * 2 - U * 2 + pad + qs / 2 - 16), '카메라로 찍으면 예매', font=font(KR, 26), fill=WHITE)
    cta_plate(d, 'App Store · 파티모아', int(FH * 0.86) - 92 - 48)
    footer(d, 0)
    b.convert('RGB').save(os.path.join(OUT, 'T2.jpg'), quality=94)
    tiles['T2'] = b.convert('RGB')

    g = Image.new('RGB', (W * 3 + 16, FH * 2 + 8), (255, 255, 255))
    for i, k in enumerate(('TC', 'T1', 'T2')):
        g.paste(tiles[k], (i * (W + 8), 0))
    for i, k in enumerate(('SC', 'S1', 'S2')):
        p = os.path.join(OUT, f'{k}.jpg')
        if os.path.exists(p):
            im = Image.open(p)
            if im.height == H:
                im = im.crop((0, BAND_Y, W, BAND_Y + FH))
            g.paste(im, (i * (W + 8), FH + 8))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_딥하우즈격자.jpg'), quality=92)
    print('피드 완료: TC T1 T2')


def reel():
    cut = 0.5
    order = ['s_room', 's_crowd', 's_bar', 's_grill', 's_crowd', 's_room', 's_sign2',
             's_bar', 's_steak', 's_crowd', 's_room', 's_crowd', 's_bar']
    by = {n: clip_frames(n, t0, d) for n, t0, d in SHOTS_ALL}
    t_cut0 = 2.0
    t_next = t_cut0 + cut * len(order)
    t_end = 10.4
    lg = logo_rgba(36)
    h1 = fit_text('이 파티', KRB, W - M * 2, 150)
    h2 = fit_text('어디서 하냐면', KRB, W - M * 2, 150)
    where = fit_text('압구정 딥하우즈', KRB, W - M * 2, 120, ACCENT + (255,))
    n1 = fit_text('AFTER MOON', KRB, W - M * 2, 130)
    n2 = text('9.26 토 22:00 – 02:10', KRB, 52)
    n3 = text('9,900원 · 웰컴샷 · 1차 30명 · 남녀 15:15', KR, 38, SUB)

    def frames():
        for i in range(NF):
            t = i / FPS
            if t < t_cut0:
                files = by['s_sign']
                fi = min(len(files) - 1, int(t / t_cut0 * len(files)))
                img = purple_tint(footage(files[fi], 1.0 + 0.05 * t / t_cut0), 0.35)
                img[int(H * 0.52):int(H * 0.76)] *= 0.55
                pop(img, h1, W / 2, H * 0.58, t, 0.0, 0.35)
                pop(img, h2, W / 2, H * 0.58 + 150, t, 0.4, 0.35)
            elif t < t_next:
                ci = min(len(order) - 1, int((t - t_cut0) / cut))
                files = by[order[ci]]
                k = (t - t_cut0 - ci * cut) / cut
                fi = min(len(files) - 1, int(k * cut * FPS) + (ci * 9) % max(1, len(files) - 16))
                img = purple_tint(footage(files[fi], 1.0 + 0.06 * k), 0.30)
                if ci == 0:
                    img[int(H * 0.30):int(H * 0.50)] *= 0.5
                    pop(img, where, W / 2, H * 0.40, t, t_cut0, 0.35)
                n = text(f'{ci + 1:02d} / {len(order):02d}', KR, 28, SUB)
                put(img, n, W - M - n.shape[1], SAFE_TOP + U * 4 + 8)
            else:
                files = by['s_crowd']
                img = purple_tint(footage(files[-1], 1.06), 0.5)
                img *= 0.55
                if t < t_end:
                    pop(img, n1, W / 2, H * 0.38, t, t_next, 0.35)
                    put(img, n2, (W - n2.shape[1]) / 2, H * 0.38 + 100, fade(t, t_next + 0.2))
                    put(img, n3, (W - n3.shape[1]) / 2, H * 0.38 + 170, fade(t, t_next + 0.4))
            put(img, lg, M, SAFE_TOP + U * 4)
            end_card(img, t, t_end)
            yield finish(img)

    encode('T_딥하우즈', frames(), BGM)


if __name__ == '__main__':
    feeds()
    reel()
