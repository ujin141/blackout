"""
**AFTER MOON 티저 피드 3장.** 매장 영상에서 뽑은 장면 셋에 이름을 얹는다.

    python feed_teaser.py   →  out/moon/T1~T3.jpg · _티저격자.jpg

## 무엇으로 잇는가

앞의 라인업 3장은 시간 막대로 이었다. 여기는 사진이 셋 다 다르니
그럴 게 없다. 대신 **AFTER MOON 을 세 칸에 걸쳐 한 번 쓴다.** 격자에서
붙여 보면 한 단어고, 한 장씩 보면 글자 몇 개가 잘려 있다. 잘린 글자는
옆 칸이 있다는 표시다 — 그래서 올리는 순서가 강제된다.

한 장씩 봐도 뭔지 알아야 하니 칸마다 작은 머리글을 따로 단다.

## 원본이 작다

카톡을 거친 파일이라 406×720 이다. 1080 으로 키우면 2.7배라 흐릿하다.
어두운 판이고 마지막에 입자를 얹으니 어느 정도 묻히지만, 원본을
받으면 다시 뽑는 게 맞다. 여기서는 살짝 흐린 뒤 입자를 얹어 **키운
티를 입자 뒤에 숨긴다.**

## 장면 고르기

초 단위로 찍어 보면 그 순간 손이 흔들렸는지 모른다. 목표 시각 앞뒤
1초를 24장으로 풀고 라플라시안 분산이 제일 큰 장을 쓴다.

## 색

매장은 붉은 네온이다. 크루 색은 검정이라 전부 흑백으로 눌러 볼까
했는데, 간판이 이 영상에서 제일 센 그림이다. 색은 두고 검정을 더
내리고 채도만 조금 뺀다. 은색 글자가 붉은 바닥 위에 서도 된다.
"""
import glob
import os
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from fest_kit import night
from fonts import KR
from poster_kit import grain
from poster_moon import (CTA, CTA_KO, DATE, LEAD, LOGO, OUT, TITLE, metal,
                         tracked, tracked_w)

BRAND_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'assets', 'Michroma-Regular.ttf')
SRC = r'C:\Users\ujin1\Desktop\KakaoTalk_20260903_235710206.mp4'
CACHE = os.path.join(OUT, 'teaser_src')

# (파일, 가운데 초). 간판 → 바 → 사람들. 들어와서, 마시고, 논다
SCENES = [('sign', 2.3), ('bar', 12.6), ('crowd', 16.4)]

U = 12
BASE = 26
INK = (244, 245, 248, 255)
DIM = (176, 179, 188, 255)
FAINT = (132, 135, 144, 255)
RULE = (92, 95, 104, 255)
STRIP = '22:00 — 02:10 · 9,900원 · 1차 30명 · 남녀 15:15 · 웰컴샷'

W, H = 1080, 1350
COLS = 3
RW = W * COLS
M = int(W * 0.082)

probe = ImageDraw.Draw(Image.new('L', (8, 8)))


def step(n):
    return int(round(BASE * 1.28 ** n))


def font(p, s):
    return ImageFont.truetype(p, s)


def hh(t, f):
    return probe.textbbox((0, 0), t, font=f)[3]


# ── 프레임 ─────────────────────────────────────────────

def frame(name, t):
    """목표 시각 앞뒤에서 제일 선명한 장. 한 번 뽑으면 캐시를 쓴다."""
    os.makedirs(CACHE, exist_ok=True)
    dst = os.path.join(CACHE, f'{name}.png')
    if os.path.exists(dst):
        return Image.open(dst).convert('RGB')
    win = os.path.join(CACHE, f'_{name}')
    os.makedirs(win, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t - 0.5:.2f}',
                    '-t', '1.0', '-i', SRC, '-vf', 'fps=24',
                    os.path.join(win, '%02d.png')], check=True)
    best, bv = None, -1.0
    for f in sorted(glob.glob(os.path.join(win, '*.png'))):
        v = cv2.Laplacian(cv2.imread(f, cv2.IMREAD_GRAYSCALE), cv2.CV_64F).var()
        if v > bv:
            best, bv = f, v
    Image.open(best).save(dst)
    return Image.open(dst).convert('RGB')


def fill(im, w, h, fy=0.5):
    """4:5 로 자르고 키운다. fy 는 세로 어디를 남길지 (0 위, 1 아래)."""
    sw, sh = im.size
    s = max(w / sw, h / sh)
    im = im.resize((round(sw * s), round(sh * s)), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * fy)
    im = im.crop((x, y, x + w, y + h))
    # 키운 티를 뭉갠다. 입자는 맨 끝에 한 번만
    return im.filter(ImageFilter.GaussianBlur(0.9))


def grade(a):
    """검정을 내리고 채도를 뺀다. 붉은 간판은 살아남을 만큼만."""
    lum = a @ np.float32([0.299, 0.587, 0.114])
    a = a * 0.70 + lum[..., None] * 0.30
    a = np.clip((a - 0.05) / 0.95, 0, 1) ** 1.22
    return a * 0.86


def band(a, cy, sig, amt):
    """글자 뒤 가로 띠. 사진이 밝은 자리에 은색 글자를 올리면 안 읽힌다."""
    yy = np.arange(a.shape[0], dtype=np.float32)[:, None, None]
    a *= 1 - amt * np.exp(-(((yy - cy) / sig) ** 2))
    return a


def floor(a, y0, amt):
    """아래로 갈수록 어둡게. 정보 줄이 서는 자리."""
    yy = np.arange(a.shape[0], dtype=np.float32)
    k = np.clip((yy - y0) / (a.shape[0] - y0), 0, 1)[:, None, None]
    a *= 1 - amt * k
    return a


def silver(text, f, track):
    asc, desc = f.getmetrics()
    im = Image.new('L', (int(tracked_w(text, f, track)) + 24, asc + desc), 0)
    tracked(ImageDraw.Draw(im), (12, 0), text, f, track, 255)
    m = np.asarray(im)
    ys, xs = np.where(m > 0)
    m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32) / 255.0
    return metal(*m.shape, m)


def fit(text, room, track, cap=460):
    for sz in range(cap, 40, -4):
        f = font(BRAND_FONT, sz)
        if tracked_w(text, f, track) <= room:
            return f
    return font(BRAND_FONT, 40)


# ── 판 ─────────────────────────────────────────────────

def sheet():
    """세 칸을 한 장으로 만든다. 사진 셋을 이어 붙이고 그 위에 이름."""
    a = np.zeros((H, RW, 3), np.float32)
    # 간판은 머리글 바로 아래에 오게 잘라서 이름과 안 겹치게 한다.
    # 바와 사람들은 가운데 조금 아래를 남긴다
    for i, ((name, t), fy) in enumerate(zip(SCENES, (0.75, 0.55, 0.55))):
        im = fill(frame(name, t), W, H, fy)
        a[:, i * W:(i + 1) * W] = np.asarray(im, np.float32) / 255.0
    a = grade(a)
    a = band(a, H * 0.56, H * 0.12, 0.44)
    a = floor(a, H * 0.72, 0.62)

    pil = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert('RGBA')

    # 이름 한 번. 세 칸 폭에 맞춘다
    f = fit(TITLE, RW - M * 4, 0.10)
    mark = silver(TITLE, f, 0.10)
    x = (RW - mark.shape[1]) // 2
    y = int(H * 0.56 - mark.shape[0] / 2)
    pil.alpha_composite(
        Image.fromarray((np.clip(mark, 0, 1) * 255).astype(np.uint8), 'RGBA'),
        (x, y))
    return pil


def panel(sh, col):
    tile = sh.crop((col * W, 0, (col + 1) * W, H)).convert('RGBA')
    d = ImageDraw.Draw(tile)

    # 칸마다 머리글. 한 장씩 볼 때 이걸로 뭔지 안다
    fe = font(BRAND_FONT, step(-2))
    tracked(d, (M, 150), f'{TITLE}   ·   {DATE}', fe, 0.22, DIM)
    d.text((M, 150 + hh(TITLE, fe) + U * 2), LEAD, font=font(KR, step(-1)),
           fill=FAINT)
    if col == 0:
        lg = Image.open(LOGO).convert('RGBA')
        lw = int(W * 0.24)
        lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
        tile.alpha_composite(lg, (W - M - lw, 150 - U))

    # 아래. 세 칸에 같은 줄 — 타임라인에서는 한 칸만 보인다
    fstrip = font(KR, step(-1))
    fcta = font(BRAND_FONT, step(0))
    ffoot = font(KR, step(-2))
    y = H - 150 - hh(CTA, fcta) - U * 3 - 2 - U * 3 - hh(STRIP, fstrip)
    d.line([(M, y - U * 3), (W - M, y - U * 3)], fill=RULE, width=1)
    d.text((M, y), STRIP, font=fstrip, fill=DIM)
    y += hh(STRIP, fstrip) + U * 3
    d.line([(M, y), (W - M, y)], fill=RULE, width=1)
    y += 2 + U * 3
    fdate = font(BRAND_FONT, step(1))
    tracked(d, (M, y + (hh(CTA, fcta) - hh(DATE, fdate)) // 2), DATE, fdate,
            0.08, INK)
    wc = tracked_w(CTA, fcta, 0.20)
    wk = probe.textlength(CTA_KO + ' ', font=ffoot)
    d.text((W - M - wc - wk, y + hh(CTA, fcta) - hh(CTA_KO, ffoot)), CTA_KO,
           font=ffoot, fill=FAINT)
    tracked(d, (W - M - wc, y), CTA, fcta, 0.20, (214, 217, 226, 255))

    out = np.asarray(tile.convert('RGB'), np.float32) / 255.0
    grain(out, 0.014)
    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    im.save(os.path.join(OUT, f'T{col + 1}.jpg'), quality=94)
    night(out, f'T{col + 1}')
    return im


def main():
    sh = sheet()
    tiles = [panel(sh, c) for c in range(COLS)]
    g = Image.new('RGB', (W * 3 + 16, H), (255, 255, 255))
    for i, t in enumerate(tiles):
        g.paste(t, (i * (W + 8), 0))
    g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
        os.path.join(OUT, '_티저격자.jpg'), quality=92)
    print('완료:', OUT)


if __name__ == '__main__':
    main()
