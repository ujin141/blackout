"""
**AFTER MOON · 디제이 한 명짜리 판.** 누끼 위에 달과 은색.

    python poster_dj_moon.py              라인업 중 누끼 있는 사람 전부
    python poster_dj_moon.py lynn ts      골라서

    out/moon/DJ_<이름>_피드.jpg   1080×1350
    out/moon/DJ_<이름>_스토리.jpg 1080×1920
    out/moon/_DJ격자.jpg          피드 셋 나란히

## 이 판이 파는 것

라인업 포스터는 다섯 이름을 한 번에 보여 준다. 그건 "누가 오나" 다.
이 판은 한 사람을 크게 세운다 — "이 사람이 온다" 다. 디제이가 자기
계정에 올리는 판이라, 그 사람 팔로워가 처음 보는 AFTER MOON 이다.

## 겹

    하늘        검정. 별을 아주 흐리게
    달          머리 뒤에 크게. 달이 후광이다
    빛줄기      달 가운데서 뻗는다
    보케        위아래 두 겹
    은고리      달 둘레에 얇게 한 줄. 이게 판을 '만든 것' 으로 보이게 한다
    뒷그림자    같은 사람을 1.35배로 키워 흐리고 어둡게. 거리가 생긴다
    사람        누끼 그대로. 색은 여기에만 있다
    테두리빛    실루엣 가장자리에 은색. 검정 배경에서 사람을 뗀다
    이름        은색 금속판. 어깨를 살짝 덮는다 — 이름이 몸 앞에 서는 게
                클럽 포스터의 문법이다
    시간·장르   이름 아래. 그 사람이 트는 시간과 장르
    아래 띠     행사 조건. 다른 AFTER MOON 판과 같은 줄

## 색은 사람에게만

판은 검정 · 흰색 · 은색이다. 크루 색이 검정이라 그렇고, 그래야 누끼의
색이 유일한 색이 되어 사람이 튄다.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fest_kit import night, sky, specks, vignette
from fonts import KR, KRB
from poster_crew import crop_head, rimlight
from poster_dj4 import fringe, melt, sharpen
from poster_kit import bloom, fit, glow, grain, paint, tmask
from poster_lineup import LINEUP
from poster_lounge import bokeh
from poster_moon import (ARC_BOT, BRAND_FONT, CTA, CTA_KO, DATE, LOGO, OUT,
                         TITLE, godrays, metal, moonface, over, starfield)
import members

SILVER = np.float32([0.74, 0.77, 0.84])
INK = np.float32([0.96, 0.96, 0.98])
DIM = np.float32([0.62, 0.64, 0.70])
FAINT = np.float32([0.44, 0.46, 0.52])
RULE = np.float32([0.26, 0.27, 0.31])
STRIP = '22:00—02:10 · 9,900원 · 1차 30명 · 15:15 · 웰컴샷'

U = 12
BASE = 26

SIZES = {
    # (W, H, 위 안전선, 아래 안전선)
    '피드': (1080, 1350, 96, 1266),
    '스토리': (1080, 1920, 250, 1620),
}


def step(n):
    return int(round(BASE * 1.28 ** n))


def slot(name):
    """라인업에서 이 사람 차례. (번호, 시작, 끝). 없으면 None."""
    for i, (n, a, b) in enumerate(LINEUP):
        if n.upper() == name.upper():
            return i + 1, a, b
    return None


def ring(img, cx, cy, r, th, a):
    """달 둘레의 얇은 은고리. 덮지 않고 더한다."""
    H, W = img.shape[:2]
    layer = np.zeros((H, W), np.float32)
    cv2.circle(layer, (int(cx), int(cy)), int(r), 1.0, int(th), cv2.LINE_AA)
    layer = cv2.GaussianBlur(layer, (0, 0), th * 0.6)
    img += layer[..., None] * SILVER * a


def figure(name, W, base_h, mult, dx):
    """누끼 한 겹을 W 폭으로 잘라 온다. mult 로 키우면 가운데만 남긴다."""
    fig = crop_head(name, int(W * mult), int(base_h * mult))
    x0 = int((fig.shape[1] - W) / 2 - dx * W)
    fig = fig[:, max(0, x0):max(0, x0) + W]
    if fig.shape[1] < W:
        fig = np.pad(fig, ((0, 0), (0, W - fig.shape[1]), (0, 0)))
    return fig


def composite(img, top, a_, px):
    H = img.shape[0]
    n = min(H - top, a_.shape[0])
    if n <= 0:
        return
    sl = slice(top, top + n)
    al = a_[:n][..., None]
    img[sl] = img[sl] * (1 - al) + px[:n] * al


def build(name, W, H, top, bot, tag):
    V = W / 1080
    M = int(W * 0.082)
    m = members.get(name)
    sl = slot(name)

    # ── 글자 크기부터. 사람 크기는 글자가 남긴 자리에서 나온다 ──
    #
    # 앞 판에서 사람을 먼저 세우고 글자를 그 아래 붙였더니 시간·장르·계정이
    # 아래 띠를 밟았다. 순서를 뒤집는다. 아래 띠, 그 위의 글자 덩어리를
    # 먼저 재고, **남는 높이가 사람 자리다.**
    fstrip = tmask(STRIP, KR, step(-1))
    fcta = tmask(CTA, BRAND_FONT, step(0), 0.20)
    fko = tmask(CTA_KO, KR, step(-2))
    fgen = tmask(ARC_BOT, BRAND_FONT, step(-2), 0.10)
    lower = int(U * 3 + fstrip.shape[0] + U * 3 + 2 + U * 3 + fcta.shape[0])

    track = 0.06
    # **다섯 장이 한 세트다.** 이름마다 폭에 맞추면 TS 가 두 배가 된다.
    # 제일 긴 이름에 맞춘 크기를 전원이 쓴다
    longest = max((n for n, _, _ in LINEUP), key=len)
    size = min(fit(longest, BRAND_FONT, W - M * 2, track), int(300 * V))
    mask = tmask(name, BRAND_FONT, size, track)
    tm = tmask(f'{sl[1]} — {sl[2]}', BRAND_FONT, step(2), 0.06) if sl else None
    genres = ' · '.join(m['genres']['en'][:3]).upper()
    gm = tmask(genres, BRAND_FONT, step(-2), 0.16) if genres else None
    handle = m.get('instagram')
    hm = tmask(f'@{handle}', KR, step(-1), 0.02) if handle else None

    block = mask.shape[0]
    for x, gap in ((tm, U * 3), (gm, int(U * 1.5)), (hm, int(U * 1.2))):
        if x is not None:
            block += gap + x.shape[0]
    y_floor = bot - lower - U * 5
    ny = y_floor - block                         # 이름 윗선

    # 로고 줄 아래부터 이름 가운데까지가 머리·어깨 자리.
    # 이름이 어깨를 살짝 덮게 0.80 지점에 이름 가운데를 맞춘다
    lg = Image.open(LOGO).convert('RGBA')
    lw = int(W * 0.22)
    lg = lg.resize((lw, max(1, round(lg.height * lw / lg.width))), Image.LANCZOS)
    la = np.asarray(lg, np.float32) / 255.0
    lh = la.shape[0]
    head_top = top + lh + U * 8
    base_h = int((ny + mask.shape[0] * 0.55 - head_top) / 0.80)
    cx = W * 0.5

    # ── 하늘 ──
    img = sky(W, H, [(0.0, (0.030, 0.030, 0.040)),
                     (0.45, (0.058, 0.058, 0.074)),
                     (1.0, (0.022, 0.022, 0.030))])
    starfield(img, 0, int(H * 0.55), n=170, seed=len(name) * 7)

    # ── 달. 머리 뒤에서 후광. 고리는 얼굴을 안 가르게 머리 위쪽에 ──
    MR = int(W * 0.33)
    my = head_top + int(base_h * 0.20)
    mf = moonface(MR)
    mf[..., :3] *= 0.70
    over(img, mf, int(cx) - MR, my - MR)
    godrays(img, cx, my, MR, seed=len(name) * 3 + 1, a=0.16)
    bokeh(img, n=22, seed=len(name) * 5, y0=0.0, y1=0.45)
    bokeh(img, n=12, seed=len(name) * 9, y0=0.62, y1=1.0)
    ring(img, cx, my, MR + int(20 * V), max(2, int(2.0 * V)), 0.50)
    ring(img, cx, my, MR + int(54 * V), max(1, int(1.2 * V)), 0.18)

    # ── 뒷그림자 ──
    back = figure(name, W, base_h, 1.35, -0.08)
    ba = cv2.GaussianBlur(np.clip((back[..., 3] - 0.05) / 0.95, 0, 1), (0, 0), 9 * V)
    g = (back[..., 0] * .299 + back[..., 1] * .587 + back[..., 2] * .114)[..., None]
    bp = cv2.GaussianBlur(np.repeat(g, 3, 2) * SILVER * 0.34, (0, 0), 9 * V)
    composite(img, head_top - int(base_h * 0.06), ba * 0.55, bp)

    # ── 사람 ──
    fig = figure(name, W, base_h, 1.0, 0.0)
    a_ = np.clip((fig[..., 3] - 0.045) / 0.955, 0, 1).copy()
    px = sharpen(np.clip(fig[..., :3], 0, 1).copy(), 2.3 * V, 0.6)
    a_, px = melt(a_, px, 0.30, len(name) * 31, V)
    composite(img, head_top, a_, px)
    # 테두리빛은 **가늘게.** 3px 로 부풀렸더니 스티커 테두리가 됐다.
    # 실루엣을 배경에서 떼는 정도면 된다
    rim = rimlight(a_, V, 1.4, 2.2, 0.28)
    n = min(H - head_top, rim.shape[0])
    img[head_top:head_top + n] += rim[:n][..., None] * SILVER * 0.55

    # ── 이름 ──
    plate = metal(*mask.shape, mask.astype(np.float32) / 255.0)
    nx = int(cx - mask.shape[1] / 2)
    glow(img, mask, cx, ny + mask.shape[0] / 2, SILVER, 0.22, 26 * V, 'c', 'c')
    over(img, plate, nx, ny)
    y = ny + mask.shape[0]

    # ── 이름 아래: 시간 · 장르 · 계정 ──
    if tm is not None:
        y += U * 3
        paint(img, tm, cx, y + tm.shape[0] / 2, color=INK, anchor='c')
        y += tm.shape[0]
    if gm is not None:
        y += int(U * 1.5)
        paint(img, gm, cx, y + gm.shape[0] / 2, color=DIM, anchor='c')
        y += gm.shape[0]
    if hm is not None:
        y += int(U * 1.2)
        paint(img, hm, cx, y + hm.shape[0] / 2, color=FAINT, anchor='c')

    # ── 위: 로고 · 무슨 파티 · 차례 ──
    sl_y, sl_x = slice(top, top + lh), slice(M, M + lw)
    al = la[..., 3:4]
    img[sl_y, sl_x] = img[sl_y, sl_x] * (1 - al) + la[..., :3] * al
    # 로고와 같은 줄에 두면 로고 오른쪽 끝을 밟는다. 한 줄 아래 가운데
    lab = tmask(f'{TITLE}   ·   {DATE}', BRAND_FONT, step(-2), 0.24)
    paint(img, lab, cx, top + lh + U * 3, color=DIM, anchor='c')
    if sl:
        num = tmask(f'{sl[0]:02d} / {len(LINEUP):02d}', BRAND_FONT, step(-1), 0.20)
        paint(img, num, W - M, top + lh / 2, color=DIM, anchor='r')

    # ── 아래 띠 ──
    yb = bot - lower
    cv2.line(img, (M, yb), (W - M, yb), RULE.tolist(), 1, cv2.LINE_AA)
    yb += U * 3
    paint(img, fstrip, M, yb + fstrip.shape[0] / 2, color=DIM, anchor='l')
    yb += fstrip.shape[0] + U * 3
    cv2.line(img, (M, yb), (W - M, yb), RULE.tolist(), 1, cv2.LINE_AA)
    yb += 2 + U * 3
    paint(img, fgen, M, yb + fcta.shape[0] / 2, color=FAINT, anchor='l')
    paint(img, fcta, W - M, yb + fcta.shape[0] / 2, color=INK, anchor='r')
    paint(img, fko, W - M - fcta.shape[1] - U, yb + fcta.shape[0] / 2 + 2,
          color=FAINT, anchor='r')

    # ── 마감 ──
    specks(img, 70, int(H * 0.05), int(H * 0.60), SILVER, 0.55,
           seed=len(name) * 13, rmax=2.2 * V)
    bloom(img, 0.62, 22 * V, 0.28)
    fringe(img, 0.0016)
    vignette(img, 0.38, 2.0)
    grain(img, 0.011)
    out = np.clip(img, 0, 1)
    Image.fromarray((out * 255).astype(np.uint8)).save(
        os.path.join(OUT, f'{tag}.jpg'), quality=94)
    night(out, tag)
    return out


def main(argv):
    want = [a.upper() for a in argv] or [n for n, _, _ in LINEUP]
    tiles = []
    for name in want:
        try:
            members.get(name)
        except KeyError:
            print(f'{name}: 멤버 정보 없음. 건너뜀')
            continue
        try:
            crop_head(name, 100, 100)
        except (KeyError, FileNotFoundError):
            print(f'{name}: 누끼 없음. 건너뜀')
            continue
        for kind, (W, H, top, bot) in SIZES.items():
            out = build(name, W, H, top, bot, f'DJ_{name}_{kind}')
            if kind == '피드':
                tiles.append(Image.fromarray((out * 255).astype(np.uint8)))
    if tiles:
        W, H = tiles[0].size
        g = Image.new('RGB', (W * len(tiles) + 8 * (len(tiles) - 1), H), (255, 255, 255))
        for i, t in enumerate(tiles):
            g.paste(t, (i * (W + 8), 0))
        g.resize((g.width // 3, g.height // 3), Image.LANCZOS).save(
            os.path.join(OUT, '_DJ격자.jpg'), quality=92)
    print('완료:', OUT)


if __name__ == '__main__':
    main(sys.argv[1:])
