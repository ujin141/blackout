"""
**AFTER MOON 릴스 · 딥하우즈 촬영본 세 편 + 이어지는 커버.** 무음.

    python reel_dh.py          셋 다 + 커버
    python reel_dh.py cover    커버만
    python reel_dh.py 1        한 편만 (1 · 2 · 3)

    out/moon/D1_부스.mp4  D2_매장.mp4  D3_디데이.mp4   (12초 · 1080×1920 · 무음)
    out/moon/DC1.jpg DC2.jpg DC3.jpg                  (커버 1080×1920)
    out/moon/_딥하우즈릴스격자.jpg

## 소스

9.21 받은 딥하우즈 촬영본. 31컷. ffprobe 는 3840×2160 이라 하지만 회전
태그(90°)가 붙어 있어 **실제로는 2160×3840 세로**다. 자를 것 없이 1080×1920
으로 줄이기만 한다. 카톡 영상(406×720)을 2.7배 키워 쓰던 것과는 다른 판이다.
ta_1418 만 가로(회전 0)라 안 쓴다.

## 세 편

    1  부스     믹서 · 조그휠 · 노브 · 디제이   여기서 틉니다 → 라인업
    2  매장     간판 · 바 · 칵테일 · 테킬라     압구정 딥하우즈 → 시간 · 값 · 정원
    3  디데이   부스 · 디제이 · 패널 · 샴페인   D-3 → 토요일 밤 10시 → 30명 → 혼자 와도

## 커버는 격자에서 이어진다

세로 컷 셋 — 믹서 · 간판 · 샴페인 병 — 을 가운데 4:5 띠로 자른다.
은선 하나와 조건 한 줄이 세 장을 가로지른다. 글은 칸마다 하나씩.
"""
import glob
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

from feed_teaser import grade
from fonts import KR, KRB
from poster_hook import silver_text
from poster_lineup import LINEUP
from poster_moon import BRAND_FONT, CTA, CTA_KO, DATE, LOGO, OUT, TITLE, tracked
from reel_moon import (DIM, FAINT, FPS, H, INK, M, NF, SAFE_TOP, U, W,
                       beat, darken, end_card, fade, finish, font, plate, put, step, text_rgba)
from reel_moon2 import encode_silent, logo
from render import out_expo

SRC_DIR = os.path.join(os.path.expanduser('~'), 'Downloads')
CACHE = os.path.join(OUT, '_reel_dh')
T_END = 9.8
DDAY = 'D-3'
BAND = 1350
BAND_Y = (H - BAND) // 2


def src(n):
    hits = glob.glob(os.path.join(SRC_DIR, 'drive-download-*', f'ta_{n}.MP4'))
    assert hits, f'ta_{n}.MP4 없음'
    return hits[0]


def clip(n, t0, dur):
    """프레임 캐시. ffmpeg 이 회전 태그를 풀어 세로로 내놓는다. 줄이기만."""
    d = os.path.join(CACHE, f'{n}_{t0:.1f}_{dur:.1f}')
    if os.path.isdir(d) and len(os.listdir(d)) >= int(dur * FPS) - 1:
        return sorted(os.path.join(d, f) for f in os.listdir(d))
    os.makedirs(d, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.2f}', '-t', f'{dur:.2f}',
                    '-i', src(n), '-vf', f'fps={FPS},scale={W}:{H}',
                    '-q:v', '2', os.path.join(d, '%03d.jpg')], check=True)
    return sorted(os.path.join(d, f) for f in os.listdir(d))


def frame(path, zoom=1.0):
    im = Image.open(path).convert('RGB')
    if zoom != 1.0:
        w, h = im.size
        cw, ch = int(w / zoom), int(h / zoom)
        x0, y0 = (w - cw) // 2, (h - ch) // 2
        im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.LANCZOS)
    return grade(np.asarray(im, np.float32) / 255.0)


def still(n, t):
    return frame(clip(n, t, 0.1)[0])


def popin(img, rgba, cx, cy, t, t0, d=0.35, big=1.16):
    k = fade(t, t0, d)
    if k <= 0:
        return
    s = big - (big - 1) * out_expo(k)
    r = cv2.resize(rgba, None, fx=s, fy=s)
    put(img, r, cx - r.shape[1] / 2, cy - r.shape[0] / 2, k)


def base(cuts, t):
    """(컷번호, 시작, 길이, 박) 목록에서 이 시각의 프레임."""
    ci = max(j for j, c in enumerate(cuts) if t >= c[3])
    n, t0, dur, at = cuts[ci]
    files = clip(n, t0, dur)
    nxt = cuts[ci + 1][3] if ci + 1 < len(cuts) else T_END + 2.2
    k = (t - at) / max(0.01, nxt - at)
    fi = min(len(files) - 1, int((t - at) * FPS))
    img = frame(files[fi], 1.0 + 0.05 * k)
    img *= 0.80
    logo(img, M, SAFE_TOP + U * 2, 0.22)
    return img, ci, at


def center(img, rgba, y, a=1.0):
    put(img, rgba, (W - rgba.shape[1]) / 2, y, a)


# ── 1. 부스 ───────────────────────────────────────────
def reel_1():
    #        컷    시작  길이  박
    cuts = [(1426, 20.0, 2.2, 0.0),
            (1414, 6.0, 2.2, beat(4)),
            (1422, 3.0, 2.2, beat(8)),
            (1420, 8.0, 2.2, beat(12)),
            (1407, 30.0, 3.0, beat(16))]
    h1 = silver_text('여기서', font(KRB, 190), 0.0)
    h2 = silver_text('틉니다', font(KRB, 190), 0.0)
    sub = text_rgba('압구정 딥하우즈 · 9.26 토', KR, step(1), DIM)
    names = [silver_text(n, font(BRAND_FONT, 96), 0.06) for n, _, _ in LINEUP]
    times = [text_rgba(f'{a} — {b}', BRAND_FONT, step(0), FAINT, 0.12) for _, a, b in LINEUP]
    lab = text_rgba('LINE UP', BRAND_FONT, step(-1), DIM, 0.40)

    def frames():
        for i in range(NF):
            t = i / FPS
            img, ci, at = base(cuts, t)
            if ci < 2:
                darken(img, int(H * 0.30), int(H * 0.72), 0.55)
                popin(img, h1, W / 2, H * 0.44, t, 0.15)
                popin(img, h2, W / 2, H * 0.44 + 200, t, beat(2) - 0.1)
                center(img, sub, H * 0.44 + 320, fade(t, beat(3)))
            elif t < T_END:
                darken(img, int(H * 0.24), int(H * 0.80), 0.62)
                center(img, lab, SAFE_TOP + U * 12, fade(t, beat(8)))
                y0 = SAFE_TOP + U * 18
                for j in range(5):
                    kk = fade(t, beat(8) + 0.12 + j * 0.28, 0.35)
                    if kk <= 0:
                        continue
                    y = y0 + j * 148
                    put(img, names[j], M, y, kk)
                    put(img, times[j], W - M - times[j].shape[1], y + names[j].shape[0] - times[j].shape[0] - 6, kk)
            end_card(img, t, T_END)
            yield finish(img)

    encode_silent('D1_부스', frames())


# ── 2. 매장 ───────────────────────────────────────────
def reel_2():
    cuts = [(1415, 4.0, 2.2, 0.0),
            (1410, 3.0, 2.2, beat(4)),
            (1421, 3.0, 2.2, beat(8)),
            (1423, 3.0, 2.2, beat(12)),
            (1408, 4.0, 3.0, beat(16))]
    h1 = silver_text('압구정', font(KRB, 180), 0.0)
    h2 = silver_text('딥하우즈', font(KRB, 180), 0.0)
    rows = [('22:00 — 02:10', '토요일 밤 열 시부터 새벽 두 시'),
            ('9,900원', '웰컴샷 포함 · 남녀 같은 값'),
            ('1차 30명', '남녀 15 : 15 · 한쪽 차면 마감')]
    bigs = [silver_text(a, font(KRB, 150), 0.0) for a, _ in rows]
    smalls = [text_rgba(b, KR, step(1), DIM) for _, b in rows]

    def frames():
        for i in range(NF):
            t = i / FPS
            img, ci, at = base(cuts, t)
            if ci == 0:
                # 간판이 화면 가운데다. 글은 그 아래로 내린다
                darken(img, int(H * 0.56), int(H * 0.92), 0.7)
                popin(img, h1, W / 2, H * 0.66, t, 0.15)
                popin(img, h2, W / 2, H * 0.66 + 190, t, beat(2) - 0.1)
            else:
                darken(img, int(H * 0.30), int(H * 0.72), 0.8 if ci == 4 else 0.58)
            if ci == 0:
                pass
            elif ci < 4:
                j = ci - 1
                popin(img, bigs[j], W / 2, H * 0.46, t, at)
                center(img, smalls[j], H * 0.46 + 100, fade(t, at + 0.3))
            elif t < T_END:
                popin(img, plate(TITLE, step(5), 0.16), W / 2, H * 0.44, t, at)
                popin(img, plate(DATE, step(4), 0.06), W / 2, H * 0.44 + 120, t, at + 0.2)
            end_card(img, t, T_END)
            yield finish(img)

    encode_silent('D2_매장', frames())


# ── 3. 디데이 ─────────────────────────────────────────
def reel_3():
    cuts = [(1429, 30.0, 2.2, 0.0),
            (1428, 10.0, 2.2, beat(4)),
            (1433, 8.0, 2.2, beat(8)),
            (1438, 4.0, 2.2, beat(12)),
            (1424, 6.0, 3.0, beat(16))]
    d1 = plate(DDAY, 300, 0.04)
    d2 = silver_text('토요일 밤 10시', font(KRB, 140), 0.0)
    d3 = text_rgba('추석 연휴 마지막날', KR, step(2), DIM)
    l1 = silver_text('30명만', font(KRB, 170), 0.0)
    l2 = text_rgba('남녀 15 : 15 · 한쪽 차면 그쪽부터 마감', KR, step(1), DIM)
    l3 = silver_text('혼자 와도 됩니다', font(KRB, 120), 0.0)
    l4 = text_rgba('1인 예매 환영 · 웰컴샷 한 잔', KR, step(1), DIM)

    def frames():
        for i in range(NF):
            t = i / FPS
            img, ci, at = base(cuts, t)
            darken(img, int(H * 0.28), int(H * 0.74), 0.8 if ci == 4 else 0.6)
            if ci == 0:
                popin(img, d1, W / 2, H * 0.46, t, 0.15, 0.4, 1.3)
            elif ci == 1:
                popin(img, d2, W / 2, H * 0.44, t, at)
                center(img, d3, H * 0.44 + 100, fade(t, at + 0.3))
            elif ci == 2:
                popin(img, l1, W / 2, H * 0.44, t, at)
                center(img, l2, H * 0.44 + 120, fade(t, at + 0.3))
            elif ci == 3:
                popin(img, l3, W / 2, H * 0.44, t, at)
                center(img, l4, H * 0.44 + 90, fade(t, at + 0.3))
            elif t < T_END:
                popin(img, plate(TITLE, step(5), 0.16), W / 2, H * 0.44, t, at)
                popin(img, plate(DATE, step(4), 0.06), W / 2, H * 0.44 + 120, t, at + 0.2)
            end_card(img, t, T_END)
            yield finish(img)

    encode_silent('D3_디데이', frames())


# ── 커버 ──────────────────────────────────────────────
# (컷, 시각, 띠를 자를 세로 오프셋, 밝기). 간판은 글 아래로 내리고, 병은 어두워서 올린다
COVER_SRC = [(1426, 20.5, BAND_Y, 0.70), (1415, 4.5, 60, 0.62), (1438, 6.0, BAND_Y, 1.25)]
TOP, BOT = 90, 1266


def covers():
    RW = W * 3
    img = np.zeros((BAND, RW, 3), np.float32)
    for c, (n, t, oy, k) in enumerate(COVER_SRC):
        img[:, c * W:(c + 1) * W] = still(n, t)[oy:oy + BAND] * k
    yy = np.linspace(0, 1, BAND, dtype=np.float32)[:, None, None]
    img *= 0.42 + 0.58 * np.exp(-((yy - 0.5) / 0.30) ** 2)
    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)

    ly = int(BAND * 0.70)
    d.line([(0, ly), (RW, ly)], fill=(150, 154, 168, 255), width=2)
    ft = font(KR, step(1))
    unit = f'{TITLE}  ·  {DATE}  ·  압구정 딥하우즈  ·  22:00 — 02:10  ·  9,900원  ·  웰컴샷 포함     '
    x = M
    while x < RW:
        d.text((x, ly + U * 2), unit, font=ft, fill=DIM)
        x += d.textlength(unit, font=ft)

    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.17)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    fe = font(BRAND_FONT, step(-2))
    labels = ['01  부스', '02  매장', '03  디데이']
    for c in range(3):
        x0 = c * W
        tracked(d, (x0 + M, TOP + U * 2), 'BLACKOUT CREW', fe, 0.40, FAINT)
        pil.alpha_composite(lg, (x0 + W - M - lw, TOP + U))
        d.text((x0 + M, BOT - 30), labels[c], font=font(KR, step(-2)), fill=FAINT)
        d.polygon([(x0 + W - M - 150, BOT - 34), (x0 + W - M - 150, BOT), (x0 + W - M - 122, BOT - 17)], fill=(214, 217, 226, 255))
        d.text((x0 + W - M - 108, BOT - 34), '릴스 · 12초', font=font(KR, step(-2)), fill=FAINT)
        fc, ff = font(BRAND_FONT, step(2)), font(KR, step(0))
        wk = d.textlength(CTA_KO + '  ', font=ff)
        cy = ly + U * 2 + step(1) + U * 4
        tracked(d, (x0 + M + wk, cy), CTA, fc, 0.22, (214, 217, 226, 255))
        d.text((x0 + M, cy + step(2) - step(0)), CTA_KO, font=ff, fill=FAINT)

    def big(txt, size, x, y):
        m = silver_text(txt, font(KRB, size), 0.0)
        pil.alpha_composite(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), 'RGBA'), (int(x), int(y)))
        return m.shape[0]

    y = TOP + U * 8
    y += big('여기서', 200, M, y) + U
    y += big('틉니다', 200, M, y) + U * 2
    d.text((M, y), ' · '.join(n for n, _, _ in LINEUP), font=font(KRB, step(2)), fill=INK)

    x0 = W
    y = TOP + U * 8
    y += big('압구정', 200, x0 + M, y) + U
    y += big('딥하우즈', 200, x0 + M, y) + U * 2
    d.text((x0 + M, y), '9.26 토 22:00 — 02:10', font=font(KRB, step(2)), fill=INK)

    x0 = 2 * W
    y = TOP + U * 6
    tracked(d, (x0 + M, y), DDAY, font(BRAND_FONT, 260), 0.02, INK)
    y += 260 + U * 4
    d.text((x0 + M, y), '9,900원 · 웰컴샷 포함', font=font(KRB, step(2)), fill=INK)
    y += step(2) + U * 2
    d.text((x0 + M, y), '1차 30명 · 남녀 15 : 15', font=font(KR, step(1)), fill=DIM)

    out = np.asarray(pil.convert('RGB'), np.float32) / 255.0
    band_img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    tiles = []
    for c, (n, t, oy, k) in enumerate(COVER_SRC):
        tile = band_img.crop((c * W, 0, (c + 1) * W, BAND))
        tiles.append(tile)
        full = Image.fromarray((np.clip(still(n, t) * 0.28, 0, 1) * 255).astype(np.uint8))
        full.paste(tile, (0, BAND_Y))
        full.save(os.path.join(OUT, f'DC{c + 1}.jpg'), quality=94)
    g = Image.new('RGB', (W * 3 + 16, BAND), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_딥하우즈릴스격자.jpg'), quality=92)
    print('커버 완료: DC1 DC2 DC3')


def main(argv):
    if 'cover' in argv:
        covers()
        return
    picked = [a for a in argv if a in ('1', '2', '3')]
    for w in picked or ['1', '2', '3']:
        {'1': reel_1, '2': reel_2, '3': reel_3}[w]()
    if not picked:
        covers()


if __name__ == '__main__':
    main(sys.argv[1:])
