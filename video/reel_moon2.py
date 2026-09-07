"""
**AFTER MOON 릴스 두 번째 세트.** 무음. 구성·편집·커버 전부 첫 세트와 다르게.

    python reel_moon2.py           셋 다 + 커버
    python reel_moon2.py count     골라서 (count · line · split · cover)

    out/moon/N1_카운트.mp4  N2_타임라인.mp4  N3_스플릿.mp4    (소리 없음)
    out/moon/RN1.jpg RN2.jpg RN3.jpg                         (커버 1080×1920)
    out/moon/_릴스2커버격자.jpg

## 첫 세트와 어떻게 다른가

    첫 세트  R1 영상 느린 컷  R2 디제이 카드  R3 글자 순서대로   곡 있음
    이 세트  N1 0.4초 속사    N2 등뼈가 그려짐 N3 위아래 반 나눔   곡 없음

곡을 안 넣는다. 인스타에서 유행하는 소리를 얹을 수 있게. 그래서 컷은
박이 아니라 **0.4초 · 0.8초 같은 고정 간격**으로 자른다 — 어떤 곡을
얹어도 어긋나지 않는 간격이다.

## 커버가 이어지는 방식

첫 세트는 AFTER / MOON / 09.26 단어를 셋에 나눴다. 여기는 **달 하나가
세 칸을 지난다.** 가운데 칸에 달 중심, 양옆 칸에 달 가장자리와 빛줄기.
칸마다 은색 숫자 하나 — 30 · 9,900 · 22:00. 한 장씩 봐도 숫자가 훅이고
붙이면 달이다.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

from fest_kit import sky
from fonts import KR, KRB
from poster_lineup import LINEUP
from poster_lounge import bokeh
from poster_moon import (BRAND_FONT, CTA, CTA_KO, DATE, LEAD, LOGO, OUT, TITLE,
                         godrays, metal, moonface, over, starfield, tracked, tracked_w)
from reel_moon import (DIM, DUR, FAINT, FPS, H, INK, M, NF, SAFE_BOT, SAFE_TOP, U,
                       W, clip_frames, darken, end_card, fade, finish, font, footage,
                       plate, put, step, text_rgba)
from render import out_cubic, out_expo


def encode_silent(name, frames):
    dst = os.path.join(OUT, f'{name}.mp4')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-an',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
           '-movflags', '+faststart', dst]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    print('완료:', dst)


def logo(img, x, y, frac=0.22, a=1.0):
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * frac)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    put(img, np.asarray(lg, np.float32) / 255.0, x, y, a)


# ══════════════════════════════════════════════════════════
#  N1. 카운트 — 0.4초 속사 + 숫자
# ══════════════════════════════════════════════════════════
#
# 매장 영상 전 구간을 0.4초씩 잘라 번갈아 튼다. 위에 숫자 하나씩.
# 빠른 컷은 그 자체가 파티 같다. 숫자는 그 위에서 한 박씩 산다.

# 영상의 쓸 만한 구간. (시작, 길이)
SHOTS_ALL = [('s_sign', 1.0, 2.0), ('s_grill', 4.0, 1.2), ('s_steak', 6.0, 1.2),
             ('s_room', 8.6, 3.0), ('s_bar', 12.2, 2.4), ('s_crowd', 14.8, 3.0),
             ('s_sign2', 18.2, 1.4)]
NUMS = [('30', '명만'), ('15:15', '남녀'), ('9,900', '원'), ('22:00', '시작'), ('5', '명이 틉니다')]


def reel_count():
    seqs = [(n, clip_frames(n, t0, d)) for n, t0, d in SHOTS_ALL]
    cut = 0.4
    # 컷 순서. 간판으로 열고 사람으로 닫는다. 그릴·스테이크는 양념
    order = ['s_sign', 's_room', 's_crowd', 's_bar', 's_grill', 's_crowd', 's_room',
             's_bar', 's_steak', 's_crowd', 's_sign2', 's_room', 's_bar', 's_crowd',
             's_sign', 's_crowd', 's_room', 's_bar', 's_crowd', 's_crowd']
    by = dict(seqs)
    mark = plate(TITLE, 96, 0.10) if False else None
    fnum = font(BRAND_FONT, 260)
    fko = font(KRB, step(3))
    t_end = 9.6
    plates = [(text_rgba(a, BRAND_FONT, 230, INK, 0.02), text_rgba(b, KRB, step(3), DIM))
              for a, b in NUMS]
    title = text_rgba(TITLE, BRAND_FONT, step(2), INK, 0.16)
    date = text_rgba(f'{DATE} · 압구정 딥하우즈', KR, step(0), DIM)

    def frames():
        for i in range(NF):
            t = i / FPS
            if t < t_end:
                ci = min(len(order) - 1, int(t / cut))
                files = by[order[ci]]
                k = (t - ci * cut) / cut
                fi = min(len(files) - 1, int(k * cut * FPS) + (ci * 7) % max(1, len(files) - 12))
                img = footage(files[fi], 1.0 + 0.06 * k)
                img *= 1.08
                # 숫자. 1.6초마다 하나. 위아래 검은 띠 없이 그냥 얹는다 — 컷이 빠르면 띠가 흔들려 보인다
                ni = min(len(plates) - 1, int(t / 1.9))
                num, ko = plates[ni]
                kk = (t - ni * 1.9) / 1.9
                a = min(1.0, kk / 0.12) * (1.0 if kk < 0.85 else (1 - (kk - 0.85) / 0.15))
                s = 1.10 - 0.10 * out_expo(kk / 0.3)
                nh, nw = num.shape[:2]
                ns = cv2.resize(num, (int(nw * s), int(nh * s)))
                darken(img, int(H * 0.36), int(H * 0.64), 0.42)
                put(img, ns, (W - ns.shape[1]) / 2, H * 0.47 - ns.shape[0] / 2, a)
                put(img, ko, (W - ko.shape[1]) / 2, H * 0.47 + nh / 2 + U * 2, a)
                logo(img, M, SAFE_TOP + U * 2, 0.20)
                put(img, title, M, SAFE_BOT - title.shape[0] - date.shape[0] - U * 6)
                put(img, date, M, SAFE_BOT - date.shape[0] - U * 4)
            else:
                files = by['s_crowd']
                img = footage(files[-1], 1.06)
                darken(img, 0, H, 0.5)
            end_card(img, t, t_end)
            yield finish(img)

    encode_silent('N1_카운트', frames())


# ══════════════════════════════════════════════════════════
#  N2. 타임라인 — 등뼈가 위에서 아래로 그려진다
# ══════════════════════════════════════════════════════════

def reel_line():
    img0 = sky(W, H, [(0.0, (0.040, 0.040, 0.052)),
                      (0.45, (0.080, 0.080, 0.100)),
                      (1.0, (0.030, 0.030, 0.040))])
    starfield(img0, 0, int(H * 0.5), n=160, seed=4)
    MR = int(W * 0.30)
    mf = moonface(MR)
    mf[..., :3] *= 0.5
    over(img0, mf, W - int(W * 0.18) - MR, SAFE_TOP - int(MR * 0.4))
    bokeh(img0, n=18, seed=6, y0=0.0, y1=0.4)
    from poster_lineup import silver
    ftime = font(BRAND_FONT, step(0))
    names = {n: silver(n, font(BRAND_FONT, 118), 0.06) for n, _, _ in LINEUP}
    timew = int(max(tracked_w(a, ftime, 0.14) for _, a, _ in LINEUP)) + U * 3
    sx = M + timew
    nx = sx + U * 5
    y0, y1 = SAFE_TOP + int(U * 20), SAFE_BOT - int(U * 14)
    band = (y1 - y0) / len(LINEUP)
    head = text_rgba(f'{TITLE}   ·   {DATE}', BRAND_FONT, step(-1), DIM, 0.22)
    lab = text_rgba('LINE UP', BRAND_FONT, step(-1), DIM, 0.40)
    strip = text_rgba('9,900원 · 1차 30명 · 남녀 15:15 · 웰컴샷', KR, step(-1), DIM)
    t_end = 9.8
    each = 1.5                                   # 한 명이 들어오는 간격

    def frames():
        for i in range(NF):
            t = i / FPS
            img = img0.copy()
            logo(img, M, SAFE_TOP + U * 2, 0.22)
            put(img, head, M, SAFE_TOP + U * 9)
            put(img, lab, M, SAFE_TOP + U * 9 + head.shape[0] + U)
            hold = 1 - fade(t, t_end, 0.4)
            # 선이 위에서 아래로 그려진다
            k = fade(t, 0.3, len(LINEUP) * each)
            if hold > 0:
                lay = np.zeros((H, W), np.float32)
                cv2.line(lay, (sx, y0), (sx, int(y0 + (y1 - y0) * k)), 1.0, 3, cv2.LINE_AA)
                img[...] = img * (1 - lay[..., None] * hold) + np.float32([0.42, 0.44, 0.50]) * lay[..., None] * hold
                for j, (n, a, b) in enumerate(LINEUP):
                    t0 = 0.3 + j * each
                    kk = fade(t, t0, 0.45)
                    if kk <= 0:
                        continue
                    cy = y0 + band * j
                    dot = np.zeros((H, W), np.float32)
                    cv2.circle(dot, (sx, int(cy)), 9, 1.0, -1, cv2.LINE_AA)
                    img[...] = img * (1 - dot[..., None] * hold) + np.float32([0.82, 0.84, 0.90]) * dot[..., None] * hold
                    tm = text_rgba(a, BRAND_FONT, step(0), FAINT, 0.14)
                    put(img, tm, M, cy - tm.shape[0] / 2, kk * hold)
                    p = names[n]
                    dx = (1 - out_expo(kk)) * 90
                    put(img, p, nx + dx, cy + (band - p.shape[0]) / 2, kk * hold)
                # 끝 시각
                if t > 0.3 + len(LINEUP) * each:
                    tm = text_rgba(LINEUP[-1][2], BRAND_FONT, step(0), FAINT, 0.14)
                    put(img, tm, M, y1 - tm.shape[0] / 2, fade(t, 0.3 + len(LINEUP) * each) * hold)
            put(img, strip, M, SAFE_BOT - strip.shape[0] - U * 2, fade(t, 1.0) * hold)
            end_card(img, t, t_end)
            yield finish(img)

    encode_silent('N2_타임라인', frames())


# ══════════════════════════════════════════════════════════
#  N3. 스플릿 — 위 반은 영상, 아래 반은 후크
# ══════════════════════════════════════════════════════════

HOOKS = [(['추석에 혼자면'], '여기로 오세요'),
         (['아는 사람', '없어야 더 재밌어요'], '그래서 1인 예매만 받습니다'),
         (['30명 채우면', '1차 닫아요'], '차는 성별부터 먼저 닫힙니다'),
         (['9,900원'], '웰컴샷 한 잔 포함')]


def reel_split():
    seqs = {n: clip_frames(n, t0, d) for n, t0, d in SHOTS_ALL}
    order = ['s_crowd', 's_room', 's_bar', 's_sign']
    from poster_lineup import silver
    hooks = []
    for lines, sub in HOOKS:
        sz = 150
        for s_ in range(150, 60, -4):
            if all(font(KRB, s_).getlength(l) <= W - M * 2 for l in lines):
                sz = s_
                break
        hooks.append(([text_rgba(l, KRB, sz, INK) for l in lines],
                      text_rgba(sub, KR, step(1), DIM)))
    each = 2.4
    t_end = each * len(HOOKS)
    half = H // 2

    def frames():
        for i in range(NF):
            t = i / FPS
            hi = min(len(HOOKS) - 1, int(t / each))
            kk = (t - hi * each) / each
            files = seqs[order[hi % len(order)]]
            fi = min(len(files) - 1, int(kk * each * FPS))
            src = footage(files[fi], 1.0 + 0.05 * kk) * 1.10
            img = np.zeros((H, W, 3), np.float32) + np.float32([0.03, 0.03, 0.04])
            # 위 반: 영상. 세로 가운데를 잘라 위 절반에 놓는다
            top_src = src[H // 4:H // 4 + half]
            img[:half] = top_src
            # 경계. 은색 가는 선
            cv2.line(img, (0, half), (W, half), (0.72, 0.75, 0.82), 3, cv2.LINE_AA)
            # 아래 반: 후크
            lines, sub = hooks[hi]
            a = min(1.0, kk / 0.10) * (1.0 if kk < 0.9 else 1 - (kk - 0.9) / 0.1)
            th = sum(l.shape[0] for l in lines) + U * (len(lines) - 1) + U * 3 + sub.shape[0]
            y = half + (half - th) / 2 - U * 12
            for l in lines:
                dx = (1 - out_expo(min(1, kk / 0.3))) * 60
                put(img, l, M + dx, y, a)
                y += l.shape[0] + U
            y += U * 3
            put(img, sub, M, y, a * fade(kk, 0.12, 0.2))
            logo(img, M, SAFE_TOP + U * 2, 0.20)
            date = text_rgba(f'{TITLE} · {DATE} · 압구정 딥하우즈', KR, step(-1), DIM)
            put(img, date, M, SAFE_TOP + U * 2 + 70)
            if t >= t_end:
                img *= 0.45
            end_card(img, t, t_end)
            yield finish(img)

    encode_silent('N3_스플릿', frames())


# ══════════════════════════════════════════════════════════
#  커버 — 달 하나가 세 칸을 지난다
# ══════════════════════════════════════════════════════════

BAND = 1350
BAND_Y = (H - BAND) // 2
RW = W * 3
COVER = [('RN1', '30', '명만 받아요', '1차 · 남녀 15:15'),
         ('RN2', '9,900', '원 · 웰컴샷 포함', 'AFTER MOON · 9.26 SAT'),
         ('RN3', '22:00', '부터 새벽 2시 10분', '압구정 딥하우즈')]


def covers():
    from poster_lineup import silver
    band = sky(RW, BAND, [(0.0, (0.036, 0.036, 0.048)),
                          (0.5, (0.070, 0.070, 0.090)),
                          (1.0, (0.028, 0.028, 0.038))])
    starfield(band, 0, int(BAND * 0.6), n=260, seed=9)
    MR = int(BAND * 0.62)
    mf = moonface(MR)
    mf[..., :3] *= 0.62
    over(band, mf, RW // 2 - MR, BAND // 2 - MR + int(BAND * 0.06))
    godrays(band, RW / 2, BAND / 2 + BAND * 0.06, MR, seed=3, a=0.20)
    bokeh(band, n=30, seed=5, y0=0.0, y1=1.0)
    yy = np.arange(BAND, dtype=np.float32)[:, None, None]
    band *= 1 - 0.45 * np.clip((yy - BAND * 0.62) / (BAND * 0.38), 0, 1)
    band *= 1 - 0.30 * np.exp(-(((yy - BAND * 0.64) / (BAND * 0.10)) ** 2))

    pil = Image.fromarray((np.clip(band, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(pil)
    d.line([(int(W * 0.08), int(BAND * 0.80)), (RW - int(W * 0.08), int(BAND * 0.80))],
           fill=(110, 113, 124, 255), width=2)

    tiles = []
    for s_ in range(250, 100, -6):
        if all(tracked_w(n_, font(BRAND_FONT, s_), 0.02) <= W - M * 2 for _, n_, _, _ in COVER):
            break
    for i, (name, num, ko, sub) in enumerate(COVER):
        tile = pil.crop((i * W, 0, (i + 1) * W, BAND)).convert('RGBA')
        d = ImageDraw.Draw(tile)
        p = silver(num, font(BRAND_FONT, s_), 0.02)
        pp = Image.fromarray((np.clip(p, 0, 1) * 255).astype(np.uint8), 'RGBA')
        ny = int(BAND * 0.80) - pp.height - U * 9
        tile.alpha_composite(pp, (M, ny))
        d = ImageDraw.Draw(tile)
        d.text((M, ny + pp.height + U), ko, font=font(KRB, step(2)), fill=(236, 238, 244, 255))
        d.text((M, int(BAND * 0.80) + U * 2), sub, font=font(KR, step(-1)), fill=(176, 179, 188, 255))
        d.polygon([(W - M - 44, int(BAND * 0.80) + U * 2 + 2), (W - M - 44, int(BAND * 0.80) + U * 2 + 30),
                   (W - M - 18, int(BAND * 0.80) + U * 2 + 16)], fill=(236, 238, 244, 255))
        lg = Image.open(LOGO).convert('RGBA')
        lw = int(W * 0.22)
        lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
        tile.alpha_composite(lg, (M, U * 8))
        fe = font(BRAND_FONT, step(-2))
        tracked(d, (W - M - tracked_w(f'{TITLE}  ·  {DATE}', fe, 0.22), U * 8 + 10),
                f'{TITLE}  ·  {DATE}', fe, 0.22, (176, 179, 188, 255))

        out = tile.convert('RGB')
        full = Image.new('RGB', (W, H), (10, 10, 13))
        full.paste(out, (0, BAND_Y))
        full.save(os.path.join(OUT, f'{name}.jpg'), quality=94)
        tiles.append(out)

    g = Image.new('RGB', (W * 3 + 16, BAND), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_릴스2커버격자.jpg'), quality=92)
    print('커버 완료')


def main(argv):
    want = set(argv) or {'count', 'line', 'split', 'cover'}
    if 'cover' in want:
        covers()
    if 'count' in want:
        reel_count()
    if 'line' in want:
        reel_line()
    if 'split' in want:
        reel_split()


if __name__ == '__main__':
    main(sys.argv[1:])
