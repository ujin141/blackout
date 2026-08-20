"""
**DJ 한 명짜리 판.** 라인업 일곱 명을 각자 한 장씩.

    python poster_dj.py                  일곱 명 전부
    python poster_dj.py lynn heidy       골라서

크루 판(`poster_crew.py`)은 일곱을 한 장에 담느라 얼굴이 작습니다. 이 판은
반대로 **한 명이 판을 다 씁니다** — DJ 본인이 자기 계정에 올리는 게 목적이라
크루 판보다 이쪽이 실제로 더 많이 퍼집니다.

## 화려하게 간다

우리 자산은 흑백이 기본이지만, **이 판은 모객용이고 일곱 장이 한 세트로
피드에 걸립니다.** 전부 흑백이면 일곱 장이 한 장처럼 보여서 누가 누군지
안 남습니다. 그래서 사람마다 색을 하나씩 줍니다 — 피드에 일곱 색이 걸립니다.

화려함은 색만이 아니라 겹으로 만듭니다.

    이름 벽      뒤에 이름을 반복해 깐다. 아주 흐리게
    광선 · 후광  인물 뒤에서 퍼지는 빛과 고리 하나
    림라이트     누끼 가장자리에 자기 색을 한 줄. **이게 제일 크게 먹는다**
    큰 이름      인물 위로 겹쳐 올린다. 클럽 포스터의 그 맛이다

## night() 의 '너무 밝다' 는 여기서 무시합니다

이름이 큰 흰 글자라 밝은 픽셀이 원래 많습니다 — 글자 수에 그대로 비례합니다
(V 3.0% · TS 4.3% · HEIDY 8.1% · LYNN 12.8%). 그 검사는 **사진이 깔린 어두운
판**을 재려고 만든 것이고, 이 판의 주인공은 글자입니다. 인물 하이라이트를
눌러 봐도 13.1 → 12.8 밖에 안 움직였습니다 — 원인이 사람이 아니라 이름입니다.

## 사람마다 사진이 다르게 잘려 있다

머리 비율표(`poster_crew.CUT`)를 그대로 가져다 씁니다. **두 벌로 두면
한쪽만 고치게 됩니다** — 크루 판에서 TS 를 두 번 고친 값이 여기에도 필요합니다.
"""
import os
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, SIZES, tmask, paint, fit, rule, box, glow,
                        grain, sign, save, bloom)
from poster_crew import crop_head
from fest_kit import justify, night, vignette, sky, rays, torus, specks
from fonts import KR, KRB
from members import get
import event as EV

PAPER = np.float32([0.97, 0.97, 0.95])
DIM   = np.float32([0.58, 0.60, 0.64])

# 사람마다 색 하나. **일곱이 피드에 나란히 걸리는 걸 전제로 골랐습니다** —
# 옆자리와 안 겹치게 색상환을 돌렸습니다.
HUE = {
    'TS':    np.float32([0.20, 0.86, 1.00]),   # 시안
    'LYNN':  np.float32([1.00, 0.30, 0.64]),   # 핫핑크
    'V':     np.float32([0.62, 0.42, 1.00]),   # 보라
    'CHIPS': np.float32([0.74, 1.00, 0.26]),   # 라임
    'HEIDY': np.float32([0.18, 1.00, 0.78]),   # 아쿠아
    'DEMIC': np.float32([1.00, 0.56, 0.14]),   # 주황
    'AROS':  np.float32([1.00, 0.26, 0.22]),   # 적색
}

# 한 줄 소개. **본인 소개글에서 한 마디만 잘랐습니다** — 판에 문장을 그대로
# 넣으면 두 줄이 되고, 두 줄이 되면 아무도 안 읽습니다.
LINE = {
    'TS':    '오픈덱에서 시작했습니다',
    'LYNN':  '그날 플로어에 맞춰 갑니다',
    'V':     '장르 안 가립니다',
    'CHIPS': '월디페 느낌을 내고 싶다면',
    'HEIDY': '미친듯이 뛰어놀고 싶다면',
    'DEMIC': '무대를 가리지 않습니다',
    'AROS':  '받은 만큼 돌려줍니다',
}

SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}


def chips(name):
    """장르 칩. **DEMIC 은 장르를 못 받았습니다**(CLAUDE.md 미해결 목록).
    없으면 빈 채로 두고 대신 한 줄 소개가 그 자리를 씁니다 — 없는 걸
    지어내지 않습니다."""
    return get(name)['genres']['ko'][:4]


def rim(dst, al, color, px, a=1.0):
    """누끼 가장자리에 색 한 줄. **이 판에서 제일 크게 먹는 한 겹입니다** —
    검은 옷을 입은 사람이 검은 판에서 떨어져 나옵니다."""
    k = np.ones((px, px), np.uint8)
    edge = cv2.dilate(al, k) - cv2.erode(al, k)
    edge = cv2.GaussianBlur(edge, (0, 0), px * 0.6)
    edge = np.clip(edge / max(edge.max(), 1e-6), 0, 1)
    dst += edge[..., None] * color * a


def wall(img, text, V, color, a=0.055):
    """뒤에 깔리는 이름 벽. 흐리게 반복해서 판이 비지 않게 한다."""
    H, W = img.shape[:2]
    m = tmask(text, BRAND, int(96 * V), 0.10)
    step_y = int(m.shape[0] * 2.35)
    row = 0
    y = int(H * 0.06)
    while y < H * 0.95:
        x = -int(m.shape[1] * (0.35 if row % 2 else 0.85))
        while x < W:
            paint(img, m, x, y, color=color, a=a, anchor='l', valign='c')
            x += m.shape[1] + int(70 * V)
        y += step_y
        row += 1


def build(name, W, H, story=False, safe=False):
    V = W / 1080.0
    C = HUE[name]
    y0, y1 = (H * 0.100, H * 0.868) if safe else (0.0, float(H))
    BH = y1 - y0

    # ── 판 ───────────────────────────────────────────────
    img = sky(W, H, [(0.0, (0.030, 0.031, 0.040)), (0.5, (0.020, 0.021, 0.028)),
                     (1.0, (0.012, 0.013, 0.018))])
    wall(img, name, V, PAPER, 0.035)

    hx, hy = W / 2, y0 + BH * 0.36                   # 인물 머리께 — 빛이 여기서 난다
    rays(img, hx, hy, 22, int(60 * V), int(BH * 0.85), C, 0.055, phase=0.18, duty=0.42)
    torus(img, hx, hy + BH * 0.03, BH * 0.235, max(2, int(3 * V)), C, 0.40, glow=18 * V)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - hx) / (W * 0.60)) ** 2
                    + ((yy - hy) / (BH * 0.36)) ** 2))[..., None] * C * 0.050

    # ── 사람 ─────────────────────────────────────────────
    top = y0 + BH * 0.150
    hero_h = int(BH * 0.615)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    g = (fig[..., 0] * .299 + fig[..., 1] * .587 + fig[..., 2] * .114)
    g = np.clip((g - 0.5) * 1.26 + 0.5, 0, 1)
    # 하이라이트만 누른다. 흰 니트·흰 셔츠가 날아가는 걸 되돌리는 정도고,
    # 중간톤은 건드리지 않는다
    g = np.where(g > 0.72, 0.72 + (g - 0.72) * 0.48, g)[..., None]
    # 흑백으로 두되 그늘만 자기 색으로 민다. 통째로 물들이면 사람이 아니라
    # 색판이 되고, 일곱 장이 전부 만화가 된다
    # 0.26 으로 뒀더니 얼굴색까지 바뀌었다 — 초록 계열(CHIPS·HEIDY)이 특히
    # 심했다. 0.18 이면 조명이 든 것으로 읽히고 살색은 살색으로 남는다
    px = (np.repeat(g, 3, 2) * (1 - 0.18 * (1 - g)) + C * (1 - g) * 0.18) * 0.88
    t0 = int(top)
    sl = (slice(t0, min(H, t0 + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    rim(img[sl], al[:n], C, max(3, int(5 * V)), 0.45)
    img[sl] = img[sl] * (1 - al[:n, ..., None]) + px[:n] * al[:n, ..., None]

    # 발치를 판에 녹인다 — 잘린 선이 보이면 스티커를 붙인 것처럼 읽힌다
    fade_h = int(BH * 0.16)
    fy0 = min(H, t0 + hero_h) - fade_h
    if fy0 > 0:
        t = np.linspace(0, 1, fade_h, dtype=np.float32)[:, None, None] ** 1.6
        img[fy0:fy0 + fade_h] *= (1 - t * 0.92)

    # ── 시간 배지 ────────────────────────────────────────
    s, e = SET_AT[name]
    bt = f'{s} — {e}'
    bm = tmask(bt, BRAND, int(20 * V), 0.22)
    bw, bh = bm.shape[1] + 46 * V, 52 * V
    bx, by = W / 2 - bw / 2, y0 + BH * 0.088
    box(img, int(bx), int(by - bh / 2), int(bx + bw), int(by + bh / 2), C * 0.16)
    rule(img, int(by - bh / 2), int(bx), int(bx + bw), C, 0.75, max(1, int(2 * V)))
    rule(img, int(by + bh / 2), int(bx), int(bx + bw), C, 0.75, max(1, int(2 * V)))
    paint(img, bm, W / 2, by, color=PAPER, anchor='c')

    # ── 이름 ─────────────────────────────────────────────
    # **인물 위로 겹쳐 올린다.** 아래로 비켜 놓으면 사진과 글자가 따로 논다
    # **발치가 겹쳤다.** 이름 → 칩 → 한 줄 → 계정이 아래로 쌓이는데,
    # 이름을 230px 까지 키웠더니 그 아래 네 줄이 행사 블록 위로 올라탔다.
    ny = y0 + BH * 0.672
    ns = justify(name, W * 0.86, 0.06, cap=int(200 * V))
    nm = tmask(name, BRAND, ns, 0.06)
    glow(img, nm, W / 2, ny, C, 0.32, int(26 * V), anchor='c')
    paint(img, nm, W / 2, ny, color=PAPER, anchor='c')

    gy = ny + ns * 0.62
    rule(img, gy, W * 0.5 - W * 0.30, W * 0.5 + W * 0.30, C, 0.55, max(1, int(2 * V)))

    cs = chips(name)
    if cs:
        paint(img, tmask('  ·  '.join(cs), KR, int(23 * V), 0.03), W / 2, gy + 34 * V,
              color=PAPER, a=0.88, anchor='c')
    paint(img, tmask(LINE[name], KRB, int(30 * V), 0.01), W / 2,
          gy + (76 if cs else 40) * V, color=C * 0.35 + PAPER * 0.65, anchor='c')

    # **계정은 브랜드 폰트로 찍지 않는다.** 영문 전용이라 마침표가 빠져
    # `@_1.ynn___` 이 `@_1 YNN___` 으로 나왔다 — 있는 그대로 찍어야 검색이 된다
    ig = get(name)['instagram']
    if ig:
        paint(img, tmask('@' + ig, KR, int(17 * V), 0.02), W / 2,
              gy + (118 if cs else 82) * V, color=DIM, a=0.85, anchor='c')

    # ── 행사 ─────────────────────────────────────────────
    ey = y1 - 118 * V
    rule(img, ey - 34 * V, W * 0.10, W * 0.90, PAPER, 0.16, max(1, int(1 * V)))
    paint(img, tmask(EV.NAME, BRAND, int(34 * V), 0.14), W / 2, ey, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.DATE_EN}   {EV.VENUE}', KR, int(18 * V), 0.02),
          W / 2, ey + 38 * V, color=DIM, a=0.92, anchor='c')
    sign(img, W / 2, y1 - 34 * V, size=int(14 * V), color=PAPER, a=0.80, anchor='c')

    # ── 마감 ─────────────────────────────────────────────
    # 얇은 테두리 한 줄. 판이 화면에서 끝나는 자리를 잡아 준다
    inset = int(26 * V)
    for yq in (int(y0) + inset, int(y1) - inset):
        rule(img, yq, inset, W - inset, C, 0.30, max(1, int(1 * V)))
    box(img, inset, int(y0) + inset, inset + max(1, int(1 * V)), int(y1) - inset, C * 0.30 + img[int(y0) + inset:int(y1) - inset, inset:inset + 1].mean(axis=(0, 1)) * 0.70)
    box(img, W - inset, int(y0) + inset, W - inset + max(1, int(1 * V)), int(y1) - inset, C * 0.30 + img[int(y0) + inset:int(y1) - inset, W - inset:W - inset + 1].mean(axis=(0, 1)) * 0.70)

    if safe:                       # UI 가 먹는 구간은 완전히 비운다
        img[:int(y0)] *= 0.0
        img[int(y1):] *= 0.0

    bloom(img, 0.76, 20 * V, 0.20, PAPER)
    specks(img, 90, int(y0), int(y1), PAPER, 0.16, seed=hash(name) % 97)
    vignette(img, 0.34, 2.3)
    grain(img, 0.006, 5)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or EV.LINEUP
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(EV.LINEUP)}')
        key = name.lower()
        # **9:16 을 두 벌 뽑지 않는다.** 안전영역 없는 세로 판은 쓸 데가 없고,
        # 일곱 명 × 세 벌이면 폴더에서 뭘 올릴지 못 고른다
        w, h, st = SIZES['feed']
        im = build(name, w, h, st)
        night(im, f'dj_{key}_feed')
        save(im, f'dj_{key}_feed')
        im = build(name, 1080, 1920, True, safe=True)
        night(im, f'dj_{key}_story_ig')
        save(im, f'dj_{key}_story_ig')
