"""
**AFTER MOON 릴스 3편 + 이어지는 커버 3장.** 1080×1920 · 30fps · 12초.

    python reel_moon.py            셋 다 + 커버
    python reel_moon.py place      골라서 (place · lineup · book)
    python reel_moon.py cover      커버만

    out/moon/R1_장소.mp4   R2_라인업.mp4   R3_예매.mp4
    out/moon/RC1.jpg RC2.jpg RC3.jpg   릴스 커버 (1080×1920)
    out/moon/_릴스커버격자.jpg

## 세 편이 나누는 것

    1  장소     매장 영상. 간판 → 안 → 바 → 사람들. 이름과 날짜를 얹는다
    2  라인업   다섯 명이 한 명씩. 누끼 있는 셋은 얼굴까지
    3  예매     글자만. 후크 → 값 → 정원 → 예매

한 편에 다 넣으면 12초 안에 여섯 가지를 말하게 된다. 하나씩 나누면
편마다 할 말이 하나라 자막이 숨 쉴 자리가 생긴다.

## 커버는 격자에서 이어진다

릴스 커버는 프로필 격자에서 **가운데 4:5 만** 보인다. 그래서 이어지는
그림은 세로 가운데 1350px 띠 안에만 둔다. 세 칸에 걸쳐 AFTER / MOON /
09.26 을 한 단어씩 — 한 장씩 봐도 읽히고 붙이면 한 줄이 된다. 은색
가로선 하나가 세 장을 꿴다.

앞서 만든 티저 피드(T1~T3)는 AFTER MOON 을 세 칸에 걸쳐 잘라 썼다.
같은 수를 두 번 쓰면 격자에서 두 줄이 같은 판으로 보인다. 여기는
단어 단위로 자른다.

## 컷은 박에 맞춘다

곡이 114BPM 이라 한 박이 0.526초다. 컷을 5·11·16·20박에 둔다.
박에서 컷이 넘어가면 음악을 따라 편집한 것처럼 보인다 — 실제로 그렇다.

## 원본이 작다

매장 영상이 카톡을 거쳐 406×720 이다. 1080 으로 2.7배 키운다. 살짝
흐린 뒤 입자를 얹고, 검정을 내린다. 원본을 받으면 다시 뽑는 게 맞다.
"""
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from feed_teaser import SRC, grade
from fest_kit import sky
from fonts import KR, KRB
from poster_crew import crop_head
from poster_dj4 import melt, sharpen
from poster_kit import bloom, grain
from poster_lineup import LINEUP, silver
from poster_lounge import bokeh
from poster_moon import (BRAND_FONT, CTA, CTA_KO, DATE, LOGO, OUT, TITLE,
                         metal, moonface, over, starfield, tracked, tracked_w)
from render import out_cubic, out_expo

W, H, FPS = 1080, 1920, 30
DUR = 12.0
NF = int(DUR * FPS)
BPM = 114.0
BEAT = 60.0 / BPM
BGM = os.path.join(OUT, 'bgm_bell.wav')
CACHE = os.path.join(OUT, '_reel')
os.makedirs(CACHE, exist_ok=True)

SAFE_TOP, SAFE_BOT = 250, 1620
M = int(W * 0.082)
INK = (244, 245, 248, 255)
DIM = (176, 179, 188, 255)
FAINT = (132, 135, 144, 255)

U = 12
BASE = 26


def step(n):
    return int(round(BASE * 1.28 ** n))


def font(p, s):
    return ImageFont.truetype(p, s)


def beat(n):
    return n * BEAT


# ── 도구 ────────────────────────────────────────────────

def clip_frames(name, t0, dur):
    """매장 영상 한 구간을 30fps jpg 로 풀어 둔다. 한 번 풀면 캐시."""
    d = os.path.join(CACHE, name)
    if os.path.isdir(d) and len(os.listdir(d)) >= int(dur * FPS) - 1:
        return sorted(os.path.join(d, f) for f in os.listdir(d))
    os.makedirs(d, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t0:.2f}', '-t',
                    f'{dur:.2f}', '-i', SRC,
                    '-vf', f'fps={FPS},scale={W}:-2', '-q:v', '2',
                    os.path.join(d, '%03d.jpg')], check=True)
    return sorted(os.path.join(d, f) for f in os.listdir(d))


def footage(path, zoom=1.0):
    """한 장을 1080×1920 으로. 키운 티를 뭉개고 검정을 내린다."""
    im = Image.open(path).convert('RGB')
    if zoom != 1.0:
        w, h = im.size
        cw, ch = int(w / zoom), int(h / zoom)
        x0, y0 = (w - cw) // 2, (h - ch) // 2
        im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((w, h), Image.LANCZOS)
    a = np.zeros((H, W, 3), np.float32)
    src = np.asarray(im, np.float32) / 255.0
    src = cv2.GaussianBlur(src, (0, 0), 0.9)
    h = min(H, src.shape[0])
    y0 = (H - h) // 2
    a[y0:y0 + h] = src[:h]
    return grade(a)


def plate(text, size, track=0.06):
    return silver(text, font(BRAND_FONT, size), track)


def put(img, rgba, x, y, a=1.0):
    """RGBA float 판을 더한다. 밖으로 나가면 자른다."""
    h, w = rgba.shape[:2]
    x, y = int(x), int(y)
    sx0, sy0 = max(0, x), max(0, y)
    sx1, sy1 = min(W, x + w), min(H, y + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = rgba[sy0 - y:sy1 - y, sx0 - x:sx1 - x]
    al = sub[..., 3:4] * a
    dst = img[sy0:sy1, sx0:sx1]
    dst[..., :3] = dst[..., :3] * (1 - al) + sub[..., :3] * al
    # 받는 쪽이 RGBA 면(카드 위에 카드) 알파도 합친다
    if dst.shape[2] == 4:
        dst[..., 3:4] = al + dst[..., 3:4] * (1 - al)


def text_rgba(text, path, size, fill, track=0.0):
    f = font(path, size)
    w = int(tracked_w(text, f, track)) + 8
    asc, desc = f.getmetrics()
    im = Image.new('RGBA', (w, asc + desc), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(im), (4, 0), text, f, track, fill)
    return np.asarray(im, np.float32) / 255.0


def fade(t, t0, d=0.4):
    return out_cubic((t - t0) / d) if t >= t0 else 0.0


def darken(img, y0, y1, amt):
    """가로 띠를 어둡게. 글자 뒤."""
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    k = np.clip((yy - y0) / max(1, (y1 - y0) * 0.3), 0, 1) * \
        np.clip((y1 - yy) / max(1, (y1 - y0) * 0.3), 0, 1)
    img *= 1 - amt * k


def finish(img):
    out = np.clip(img, 0, 1)
    grain(out, 0.010)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def encode(name, frames):
    """프레임 생성기를 ffmpeg 에 그대로 흘린다. 파일을 안 남긴다."""
    dst = os.path.join(OUT, f'{name}.mp4')
    cmd = ['ffmpeg', '-v', 'error', '-y',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-',
           '-ss', '0', '-t', f'{DUR:.2f}', '-i', BGM,
           '-map', '0:v', '-map', '1:a',
           '-af', f'afade=t=out:st={DUR - 0.8:.2f}:d=0.8',
           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
           '-preset', 'medium', '-movflags', '+faststart',
           '-c:a', 'aac', '-b:a', '192k', '-shortest', dst]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fr in frames:
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    print('완료:', dst)


def end_card(img, t, t0):
    """마지막 판. 예매 PARTYMOA."""
    k = fade(t, t0, 0.5)
    if k <= 0:
        return
    img *= 1 - 0.55 * k
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.34)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    la = np.asarray(lg, np.float32) / 255.0
    put(img, la, (W - lw) // 2, int(H * 0.40) - la.shape[0], k)
    p = plate(CTA, step(3), 0.20)
    put(img, p, (W - p.shape[1]) // 2, int(H * 0.44), k)
    t1 = text_rgba(f'{CTA_KO} · 프로필 링크', KR, step(0), DIM)
    put(img, t1, (W - t1.shape[1]) // 2, int(H * 0.44) + p.shape[0] + U * 2, k)
    t2 = text_rgba(f'{DATE}  ·  압구정 딥하우즈', BRAND_FONT, step(-1), FAINT, 0.12)
    put(img, t2, (W - t2.shape[1]) // 2, int(H * 0.44) + p.shape[0] + U * 7, k)


# ══════════════════════════════════════════════════════════
#  1. 장소
# ══════════════════════════════════════════════════════════

# (이름, 원본 시각, 길이). 컷 경계가 박에 온다: 0 · 5 · 11 · 16 · 20박
# 간판은 0.9~3.0 만 깨끗하다. 3.3 부터 그릴이 들어온다. 사람들 컷은
# 15.8 에서 시작하면 끝에 간판이 다시 나와서 14.8 로 당겼다
CUTS = [('sign', 0.9, beat(4)), ('room', 8.8, beat(7)),
        ('bar', 12.4, beat(5)), ('crowd', 14.8, beat(4))]


def reel_place():
    seqs = [(n, clip_frames(n, t0, d + 0.2), d) for n, t0, d in CUTS]
    for sz in range(160, 60, -4):
        if tracked_w(TITLE, font(BRAND_FONT, sz), 0.10) <= W - M * 2:
            break
    mark = plate(TITLE, sz, 0.10)
    date = text_rgba(DATE, BRAND_FONT, step(2), INK, 0.10)
    where = text_rgba('압구정 딥하우즈  ·  22:00 — 02:10', KR, step(0), DIM)
    cond = text_rgba('9,900원  ·  1차 30명  ·  웰컴샷 포함', KR, step(0), DIM)
    t_end = beat(20)

    def frames():
        for i in range(NF):
            t = i / FPS
            # 어느 컷인가
            acc = 0.0
            for name, files, d in seqs:
                if t < acc + d or (name, files, d) == seqs[-1]:
                    k = (t - acc) / d
                    fi = min(len(files) - 1, int(k * d * FPS))
                    img = footage(files[fi], 1.0 + 0.045 * k)
                    break
                acc += d
            img *= 1.12
            darken(img, int(H * 0.14), int(H * 0.36), 0.40 * fade(t, 0.3, 0.6))
            darken(img, int(H * 0.72), H, 0.55)
            # 마지막 판이 뜨면 앞의 글자는 물러난다. 겹치면 둘 다 안 읽힌다
            hold = 1 - fade(t, t_end, 0.4)

            # 이름. 첫 박에 들어와서 위에 머문다
            k = fade(t, 0.3, 0.6)
            if k > 0:
                y = int(H * 0.22 + (1 - out_expo(k)) * 40)
                put(img, mark, (W - mark.shape[1]) // 2, y, k * hold)
            k = fade(t, beat(3), 0.5)
            if k > 0:
                put(img, date, (W - date.shape[1]) // 2, int(H * 0.22) + mark.shape[0] + U * 2, k * hold)
            k = fade(t, beat(11), 0.5)
            if k > 0:
                put(img, where, M, SAFE_BOT - U * 6 - cond.shape[0] - where.shape[0], k * hold)
            k = fade(t, beat(16), 0.5)
            if k > 0:
                put(img, cond, M, SAFE_BOT - U * 6 - cond.shape[0], k * hold)
            end_card(img, t, t_end)
            yield finish(img)

    encode('R1_장소', frames())


# ══════════════════════════════════════════════════════════
#  2. 라인업
# ══════════════════════════════════════════════════════════

def moon_bg(seed=1):
    img = sky(W, H, [(0.0, (0.030, 0.030, 0.040)),
                     (0.45, (0.058, 0.058, 0.074)),
                     (1.0, (0.022, 0.022, 0.030))])
    starfield(img, 0, int(H * 0.5), n=180, seed=seed)
    MR = int(W * 0.34)
    mf = moonface(MR)
    mf[..., :3] *= 0.72
    over(img, mf, W // 2 - MR, int(H * 0.30) - MR)
    bokeh(img, n=24, seed=seed * 5, y0=0.0, y1=0.5)
    bokeh(img, n=12, seed=seed * 9, y0=0.6, y1=1.0)
    return img


def _name_size():
    longest = max((n for n, _, _ in LINEUP), key=len)
    for sz in range(300, 80, -4):
        if tracked_w(longest, font(BRAND_FONT, sz), 0.06) <= W * 0.84:
            return sz
    return 80


NAME_SIZE = _name_size()


def dj_card(name, a, b, idx):
    """한 명짜리 판. 배경 없이 사람과 글자만 RGBA 로."""
    card = np.zeros((H, W, 4), np.float32)
    try:
        fig = crop_head(name, W, int(H * 0.50))
        al = np.clip((fig[..., 3] - 0.045) / 0.955, 0, 1).copy()
        px = sharpen(np.clip(fig[..., :3], 0, 1).copy(), 2.3, 0.6)
        al, px = melt(al, px, 0.30, len(name) * 31, 1.0)
        top = int(H * 0.22)
        n = min(H - top, al.shape[0])
        card[top:top + n, :, :3] = px[:n]
        card[top:top + n, :, 3] = al[:n]
    except (KeyError, FileNotFoundError):
        pass
    p = plate(name, NAME_SIZE, 0.06)
    y = int(H * 0.60)
    put(card, p, (W - p.shape[1]) // 2, y)
    tm = text_rgba(f'{a} — {b}', BRAND_FONT, step(2), INK, 0.08)
    put(card, tm, (W - tm.shape[1]) // 2, y + p.shape[0] + U * 3)
    num = text_rgba(f'{idx:02d} / {len(LINEUP):02d}', BRAND_FONT, step(-1), DIM, 0.20)
    put(card, num, W - M - num.shape[1], SAFE_TOP + U * 6)
    return card


def reel_lineup():
    bg = moon_bg()
    head = text_rgba(f'{TITLE}   ·   {DATE}', BRAND_FONT, step(-2), DIM, 0.24)
    lab = text_rgba('LINE UP', BRAND_FONT, step(-2), DIM, 0.40)
    cards = [dj_card(n, a, b, i + 1) for i, (n, a, b) in enumerate(LINEUP)]
    each = beat(4)                                    # 한 명에 네 박
    t_end = each * len(LINEUP)                         # 20박 = 10.5초

    def frames():
        for i in range(NF):
            t = i / FPS
            img = bg.copy()
            put(img, head, M, SAFE_TOP + U * 6)
            put(img, lab, M, SAFE_TOP + U * 6 + head.shape[0] + U)
            if t < t_end:
                j = min(len(cards) - 1, int(t / each))
                k = (t - j * each) / each
                # 들어올 때 오른쪽에서, 나갈 때 왼쪽으로. 0.35초씩
                x_in = (1 - out_expo(k / 0.30)) * W * 0.6 if k < 0.30 else 0
                x_out = -in_k(k) * W * 0.6
                dx = int(x_in + x_out)
                a = 1.0
                if k > 0.88:
                    a = 1 - (k - 0.88) / 0.12
                put(img, cards[j], dx, 0, a)
            end_card(img, t, t_end)
            yield finish(img)

    encode('R2_라인업', frames())


def in_k(k):
    """나가는 움직임. 마지막 12% 에서 가속."""
    if k < 0.88:
        return 0.0
    x = (k - 0.88) / 0.12
    return x * x


# ══════════════════════════════════════════════════════════
#  3. 예매
# ══════════════════════════════════════════════════════════

LINES = [
    (('추석에 혼자면',), '여기로 오세요'),
    (('9,900원',), '남녀 같은 값'),
    (('1차 30명',), '남녀 15명씩. 차는 쪽부터 닫혀요'),
    (('웰컴샷 한 잔',), '바에서 받으세요'),
]


def reel_book():
    crowd = clip_frames('crowd_still', 9.4, 0.2)[0]
    base = footage(crowd, 1.06)
    base = cv2.GaussianBlur(base, (0, 0), 6.0) * 0.72
    bokeh(base, n=20, seed=3, y0=0.0, y1=0.5)
    each = beat(5)                                    # 한 줄에 다섯 박
    t_end = each * len(LINES)                          # 20박
    bigs = [plate(big[0], 0, 0) if False else None for big, _ in LINES]
    # 한글 큰 줄은 굵은 한글로. 폭에 맞춘다
    bigs = []
    for (big,), sub in LINES:
        for sz in range(180, 60, -4):
            f = font(KRB, sz)
            if f.getlength(big) <= W - M * 2:
                break
        bigs.append((text_rgba(big, KRB, sz, INK), text_rgba(sub, KR, step(1), DIM)))
    head = text_rgba(f'{TITLE}   ·   {DATE}', BRAND_FONT, step(-2), DIM, 0.24)

    def frames():
        for i in range(NF):
            t = i / FPS
            img = base.copy()
            put(img, head, M, SAFE_TOP + U * 6)
            if t < t_end:
                j = min(len(bigs) - 1, int(t / each))
                k = (t - j * each) / each
                big, sub = bigs[j]
                a_in = out_cubic(k / 0.18) if k < 0.18 else 1.0
                a_out = 1 - (k - 0.90) / 0.10 if k > 0.90 else 1.0
                a = a_in * a_out
                s = 1.06 - 0.06 * out_expo(k / 0.25)
                bh, bw = big.shape[:2]
                big_s = cv2.resize(big, (int(bw * s), int(bh * s)))
                y = int(H * 0.46 - bh / 2)
                put(img, big_s, (W - big_s.shape[1]) // 2, y, a)
                put(img, sub, (W - sub.shape[1]) // 2, y + bh + U * 3, a * fade(k, 0.10, 0.2))
                # 지나간 줄은 위에 작게 쌓인다
                for q in range(j):
                    pb, _ = bigs[q]
                    small = cv2.resize(pb, (int(pb.shape[1] * 0.28), int(pb.shape[0] * 0.28)))
                    put(img, small, M, SAFE_TOP + U * 14 + q * (small.shape[0] + U), 0.55)
            end_card(img, t, t_end)
            yield finish(img)

    encode('R3_예매', frames())


# ══════════════════════════════════════════════════════════
#  커버 셋 — 격자에서 이어진다
# ══════════════════════════════════════════════════════════

BAND_H = 1350
BAND_Y = (H - BAND_H) // 2
WORDS = ['AFTER', 'MOON', '09.26']
LABELS = ['01  장소', '02  라인업', '03  예매']
COVER_SRC = [('sign', 2.3), ('crowd', 9.4), ('bar', 16.4)]


def covers():
    RW = W * 3
    band = np.zeros((BAND_H, RW, 3), np.float32)
    for i, (name, t) in enumerate(COVER_SRC):
        f = clip_frames(f'cov_{name}', t, 0.2)[0]
        im = Image.open(f).convert('RGB')
        # 4:5 가운데 띠. 간판은 위쪽, 사람들은 아래쪽을 남긴다
        w, h = im.size
        ch = int(w * BAND_H / W)
        fy = (0.94, 0.62, 0.60)[i]
        y0 = int((h - ch) * fy)
        im = im.crop((0, y0, w, y0 + ch)).resize((W, BAND_H), Image.LANCZOS)
        a = np.asarray(im, np.float32) / 255.0
        a = cv2.GaussianBlur(a, (0, 0), 0.9)
        band[:, i * W:(i + 1) * W] = a
    band = grade(band) * 1.22
    # 글자 뒤 띠와 아래
    yy = np.arange(BAND_H, dtype=np.float32)[:, None, None]
    band *= 1 - 0.30 * np.exp(-(((yy - BAND_H * 0.52) / (BAND_H * 0.13)) ** 2))
    band *= 1 - 0.40 * np.clip((yy - BAND_H * 0.72) / (BAND_H * 0.28), 0, 1)

    # 은색 가로선 하나가 셋을 꿴다
    ly = int(BAND_H * 0.52)
    line = np.zeros((BAND_H, RW), np.float32)
    cv2.line(line, (int(W * 0.08), ly), (RW - int(W * 0.08), ly), 1.0, 3, cv2.LINE_AA)
    line = cv2.GaussianBlur(line, (0, 0), 1.2)
    band += line[..., None] * np.float32([0.74, 0.77, 0.84]) * 0.9

    for sz in range(320, 80, -4):
        if all(tracked_w(w_, font(BRAND_FONT, sz), 0.08) <= W * 0.84 for w_ in WORDS):
            break
    tiles = []
    for i, word in enumerate(WORDS):
        tile = np.zeros((H, W, 3), np.float32)
        tile[BAND_Y:BAND_Y + BAND_H] = band[:, i * W:(i + 1) * W]
        # 위아래는 띠 끝 색을 늘려서 검게
        tile[:BAND_Y] = band[0:1, i * W:(i + 1) * W].mean(axis=(0, 1)) * 0.5
        tile[BAND_Y + BAND_H:] = band[-1:, i * W:(i + 1) * W].mean(axis=(0, 1)) * 0.5
        # 단어. 선 위에 올라탄다
        p = plate(word, sz, 0.08)
        put(tile, p, (W - p.shape[1]) // 2, BAND_Y + ly - p.shape[0] - U * 2)
        sub = text_rgba(('BLACKOUT CREW', 'SAT · 압구정 딥하우즈', '22:00 — 02:10')[i],
                        BRAND_FONT if i != 1 else KR, step(0), DIM, 0.16 if i != 1 else 0)
        put(tile, sub, (W - sub.shape[1]) // 2, BAND_Y + ly + U * 3)
        lab = text_rgba(LABELS[i], KR, step(-1), FAINT)
        put(tile, lab, M, BAND_Y + U * 8)
        cta = text_rgba(f'{CTA_KO}  {CTA}', BRAND_FONT, step(-1), DIM, 0.16)
        put(tile, cta, W - M - cta.shape[1], BAND_Y + BAND_H - U * 8 - cta.shape[0])
        if i == 0:
            lg = Image.open(LOGO).convert('RGBA')
            lw = int(W * 0.22)
            lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
            put(tile, np.asarray(lg, np.float32) / 255.0, W - M - lw, BAND_Y + U * 7)
        out = finish(tile)
        Image.fromarray(out).save(os.path.join(OUT, f'RC{i + 1}.jpg'), quality=94)
        tiles.append(Image.fromarray(out).crop((0, BAND_Y, W, BAND_Y + BAND_H)))

    g = Image.new('RGB', (W * 3 + 16, BAND_H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_릴스커버격자.jpg'), quality=92)
    print('커버 완료')


def main(argv):
    want = set(argv) or {'place', 'lineup', 'book', 'cover'}
    if 'place' in want:
        reel_place()
    if 'lineup' in want:
        reel_lineup()
    if 'book' in want:
        reel_book()
    if 'cover' in want:
        covers()


if __name__ == '__main__':
    main(sys.argv[1:])
