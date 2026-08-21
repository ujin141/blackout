"""
**DJ 한 명짜리 판 — B안.** 색분해 · 대각 · 세로 이름.

    python poster_dj2.py                 일곱 명 전부
    python poster_dj2.py lynn chips      골라서

A안(`poster_dj.py`)은 가운데 정렬입니다. 고리 하나, 이름 하나, 전부 가운데 —
안정적이지만 **어디서 본 판**입니다. 이 판은 반대로 갑니다.

    비대칭      인물을 오른쪽으로 밀고 왼쪽을 통째로 이름에 준다
    세로 이름   가로로 눕히면 다섯 글자가 판을 가로지르고 끝이다.
                세워서 판 높이를 다 쓰면 그게 기둥이 된다
    색분해      누끼를 두 번 더 어긋나게 깔고 각각 다른 색을 준다.
                인쇄 어긋남이자 모니터 글리치다 — 클럽 판에서 제일 잘 먹는 한 겹
    대각        판을 가로지르는 띠 하나. 가로선은 얌전하고 대각선은 안 얌전하다

## 색을 두 개 쓴다

A안은 사람마다 색 하나였습니다. 여기서는 **자기 색 + 그 반대색** 둘을 씁니다 —
색분해가 두 색으로 갈려야 어긋난 게 보입니다. 한 색으로 하면 그냥 번진 것으로
읽힙니다.

머리 비율표는 A안과 같은 걸 씁니다(`poster_crew.CUT`). 사진이 바뀌면 거기만
고치면 세 판이 같이 따라옵니다.
"""
import sys
import numpy as np
import cv2
from PIL import Image
from poster_kit import (BRAND, SIZES, tmask, paint, rule, box, grain, save, sign)
from poster_crew import crop_head, crown, rimlight
from fest_kit import justify, night, vignette, sky, specks
from fonts import KR, KRB
from members import get
from poster_dj import HUE, LINE
import event as EV

PAPER = np.float32([0.97, 0.97, 0.95])
DIM   = np.float32([0.55, 0.57, 0.62])

# 짝색. **색분해는 두 색이라야 어긋난 게 보입니다** — 한 색이면 번진 것으로
# 읽힙니다. 자기 색의 반대편에서 하나씩 골랐습니다.
MATE = {
    'TS':    np.float32([1.00, 0.34, 0.52]),   # 시안 ↔ 자홍
    'LYNN':  np.float32([0.30, 0.92, 1.00]),   # 핑크 ↔ 시안
    'V':     np.float32([0.40, 1.00, 0.72]),   # 보라 ↔ 민트
    'CHIPS': np.float32([1.00, 0.30, 0.72]),   # 라임 ↔ 마젠타
    'HEIDY': np.float32([1.00, 0.42, 0.30]),   # 아쿠아 ↔ 코랄
    'DEMIC': np.float32([0.34, 0.72, 1.00]),   # 주황 ↔ 하늘
    'AROS':  np.float32([0.30, 0.86, 1.00]),   # 적색 ↔ 시안
}

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}


def vtext(img, text, x, y0, y1, size, color, a=1.0, track=0.02):
    """글자를 위에서 아래로 쌓는다. **가로로 눕히면 다섯 글자가 판을
    가로지르고 끝이다** — 세우면 그게 판의 기둥이 된다."""
    ms = [tmask(c, BRAND, size, 0.0) for c in text]
    hs = [m.shape[0] for m in ms]
    gap = size * track + size * 0.20
    total = sum(hs) + gap * (len(ms) - 1)
    y = y0 + max(0.0, ((y1 - y0) - total) / 2)
    for m, h in zip(ms, hs):
        paint(img, m, x, y + h / 2, color=color, a=a, anchor='c')
        y += h + gap


def vfit(text, height, track=0.02):
    """세로로 쌓았을 때 주어진 높이에 맞는 글자 크기. 글자마다 높이가
    달라서(대문자라도 O 와 T 가 다르다) 재 보고 줄인다."""
    size = int(height / max(len(text), 1))
    for _ in range(24):
        ms = [tmask(c, BRAND, size, 0.0) for c in text]
        total = sum(m.shape[0] for m in ms) + (size * track + size * 0.20) * (len(ms) - 1)
        if total <= height:
            return size
        size = int(size * height / total)
    return size


def ghost(dst, al, color, dx, dy, a):
    """색분해 한 겹 — 누끼 실루엣을 어긋나게 깔고 색을 준다."""
    h, w = al.shape
    m = np.zeros_like(al)
    x0, y0 = max(0, dx), max(0, dy)
    x1, y1 = min(w, w + dx), min(h, h + dy)
    m[y0:y1, x0:x1] = al[y0 - dy:y1 - dy, x0 - dx:x1 - dx]
    dst += m[..., None] * color * a


def diag(img, y_at_left, y_at_right, th, color, a):
    """판을 가로지르는 대각 띠. **가로선은 얌전하다.**"""
    H, W = img.shape[:2]
    layer = np.zeros((H, W), np.float32)
    pts = np.array([[0, y_at_left], [W, y_at_right],
                    [W, y_at_right + th], [0, y_at_left + th]], np.int32)
    cv2.fillPoly(layer, [pts], 1.0)
    img += layer[..., None] * color * a
    return layer


def band_text(img, text, mask, y_at_left, y_at_right, th, size, color, a):
    """대각 띠 **안에** 반복해서 새기는 글자.

    처음엔 띠 마스크를 안 쓰고 그냥 얹었더니, 글자가 띠 위아래로 삐져나가
    **검은 글자가 검은 판 위에 놓였다** — 안 보이는 게 아니라 지저분했다.
    띠 모양으로 잘라야 판에 새긴 것으로 읽힌다."""
    H, W = img.shape[:2]
    ang = np.degrees(np.arctan2(y_at_right - y_at_left, W))
    unit = tmask(text, BRAND, size, 0.30)
    gap = int(size * 0.9)
    n = int(W * 2.2 / (unit.shape[1] + gap)) + 2
    strip = np.zeros((unit.shape[0], (unit.shape[1] + gap) * n), np.float32)
    x = 0
    for _ in range(n):
        strip[:, x:x + unit.shape[1]] = np.maximum(strip[:, x:x + unit.shape[1]], unit)
        x += unit.shape[1] + gap
    pad = strip.shape[0] * 3
    can = np.zeros((strip.shape[0] + pad * 2, strip.shape[1]), np.float32)
    can[pad:pad + strip.shape[0]] = strip
    Mr = cv2.getRotationMatrix2D((can.shape[1] / 2, can.shape[0] / 2), -ang, 1.0)
    can = cv2.warpAffine(can, Mr, (can.shape[1], can.shape[0]), flags=cv2.INTER_LINEAR)

    # paint() 는 색을 곱해 더한다. 여기서 필요한 건 마스크뿐이라 직접 얹는다
    layer = np.zeros((H, W), np.float32)
    cy = (y_at_left + y_at_right) / 2 + th / 2
    y0 = int(cy - can.shape[0] / 2)
    x0 = int(W / 2 - can.shape[1] / 2)
    sy0, sx0 = max(0, y0), max(0, x0)
    sy1, sx1 = min(H, y0 + can.shape[0]), min(W, x0 + can.shape[1])
    if sy1 > sy0 and sx1 > sx0:
        layer[sy0:sy1, sx0:sx1] = can[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
    img -= (layer * mask)[..., None] * color * a


def scan(img, step, amt):
    """스캔라인. 판에 결이 생겨서 그냥 어두운 면이 아니게 된다."""
    img[::step] *= (1 - amt)


def build(name, W, H, safe=False):
    V = W / 1080.0
    C, C2 = HUE[name], MATE[name]
    y0, y1 = (H * 0.100, H * 0.868) if safe else (0.0, float(H))
    BH = y1 - y0
    M = int(W * 0.062)

    img = sky(W, H, [(0.0, (0.036, 0.030, 0.046)), (0.55, (0.018, 0.017, 0.026)),
                     (1.0, (0.010, 0.010, 0.016))])
    # 판 뒤 대각 격자 — 비어 보이지 않게만
    for k in range(-8, 26):
        x = int(k * W * 0.115)
        cv2.line(img, (x, int(y1)), (x + int(BH * 0.42), int(y0)),
                 tuple((C * 0.055).tolist()), max(1, int(1.6 * V)))

    # 인물 뒤 빛. 오른쪽에 인물이 서니 빛도 오른쪽에서 난다
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    img += np.exp(-(((xx - W * 0.66) / (W * 0.46)) ** 2
                    + ((yy - (y0 + BH * 0.42)) / (BH * 0.40)) ** 2))[..., None] * C * 0.10

    # ── 세로 이름 ────────────────────────────────────────
    # **사람보다 먼저 그린다.** 위에 얹으면 스티커처럼 붙어 보이고,
    # 뒤에 두면 사람이 글자를 가리면서 깊이가 생긴다 — 판이 한 장면이 된다
    nx = M + W * 0.085
    ny0, ny1 = y0 + BH * 0.140, y0 + BH * 0.790
    # **짧은 이름은 상한을 올린다.** 210 으로 묶었더니 V 는 한 글자가
    # 기둥 한가운데 떠 있고, TS 는 둘이 붙어 있는 꼴이 됐다
    cap = (210 + 78 * max(0, 3 - len(name))) * V
    ns = min(int(vfit(name, ny1 - ny0)), int(cap))
    vtext(img, name, nx, ny0, ny1, ns, C2, a=0.32)          # 어긋난 그림자
    vtext(img, name, nx - 5 * V, ny0 - 5 * V, ny1 - 5 * V, ns, PAPER)

    # ── 사람 ─────────────────────────────────────────────
    # **오른쪽으로 민다.** 넓은 판에 그려서 필요한 만큼만 잘라 오면
    # 머리 중심을 원하는 x 에 정확히 세울 수 있다
    hero_h = int(BH * 0.700)
    wide = int(W * 1.7)
    fig = crop_head(name, wide, hero_h)
    x_from = int(wide * 0.5 - W * 0.635)
    fig = fig[:, max(0, x_from):max(0, x_from) + W]
    if fig.shape[1] < W:
        fig = np.pad(fig, ((0, 0), (0, W - fig.shape[1]), (0, 0)))
    al = fig[..., 3]
    al = crown(al)          # 정수리를 녹인다

    top = int(y0 + BH * 0.158)
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = al[:n]

    d = int(14 * V)
    ghost(img[sl], a_, C, d, -int(d * 0.4), 0.62)
    ghost(img[sl], a_, C2, -d, int(d * 0.4), 0.62)

    g = (fig[..., 0] * .299 + fig[..., 1] * .587 + fig[..., 2] * .114)
    g = np.clip((g - 0.5) * 1.34 + 0.5, 0, 1)
    g = np.where(g > 0.72, 0.72 + (g - 0.72) * 0.48, g)[..., None]
    px = (np.repeat(g, 3, 2) * (1 - 0.16 * (1 - g)) + C * (1 - g) * 0.16) * 0.90
    img[sl] = img[sl] * (1 - a_[..., None]) + px[:n] * a_[..., None]

    fade = int(BH * 0.14)
    fy = min(H, top + hero_h) - fade
    if fy > 0:
        t = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None] ** 1.5
        img[fy:fy + fade] *= (1 - t * 0.94)

    # ── 대각 띠 ──────────────────────────────────────────
    # 인물 아래를 가로지른다. 글자 블록 위에 놓으면 읽는 걸 방해한다
    bl, br, bth = y0 + BH * 0.788, y0 + BH * 0.742, int(46 * V)
    mask = diag(img, int(bl), int(br), bth, C, 0.92)
    band_text(img, f'{name}   ', mask, int(bl), int(br), bth, int(19 * V), C * 0.92, 0.85)

    # ── 곁들이 ───────────────────────────────────────────
    s, e = SET_AT[name]
    no = f'{ORDER.index(name) + 1:02d}'
    paint(img, tmask(no, BRAND, int(64 * V), 0.04), M, y0 + BH * 0.072,
          color=C, a=0.95, anchor='l')
    # **로고와 크루 계정은 항상 같이 간다**(poster_kit.sign). 글자만 두면
    # 같은 크루가 만든 판으로 안 보인다 — DJ 개인 계정은 아래 따로 있다
    sign(img, W - M, y0 + BH * 0.058, size=int(13 * V), color=DIM, a=0.88, anchor='r')
    paint(img, tmask(f'{s} — {e}', BRAND, int(24 * V), 0.20), W - M,
          y0 + BH * 0.092, color=PAPER, anchor='r')

    gs = get(name)['genres']['ko'][:4]
    ig = get(name)['instagram']
    ty = y0 + BH * 0.872
    paint(img, tmask(LINE[name], KRB, int(31 * V), 0.01), M, ty, color=PAPER, anchor='l')
    if gs:
        paint(img, tmask('  /  '.join(gs), KR, int(19 * V), 0.02), M, ty + 38 * V,
              color=C * 0.45 + PAPER * 0.55, anchor='l')
    if ig:
        # 띠 위에 놓았더니 안 읽혔다 — 장르 줄과 같은 높이, 반대쪽으로
        paint(img, tmask('@' + ig, KR, int(17 * V), 0.02), W - M, ty + 38 * V,
              color=DIM, a=0.90, anchor='r')

    # ── 발치 ─────────────────────────────────────────────
    fy2 = y1 - 52 * V
    rule(img, fy2 - 34 * V, M, W - M, PAPER, 0.18, max(1, int(1 * V)))
    paint(img, tmask(EV.NAME, BRAND, int(26 * V), 0.16), M, fy2, color=PAPER, anchor='l')
    paint(img, tmask(f'{EV.DATE_EN}  ·  {EV.VENUE}', KR, int(17 * V), 0.02),
          W - M, fy2, color=DIM, a=0.92, anchor='r')

    if safe:
        img[:int(y0)] *= 0.0
        img[int(y1):] *= 0.0

    # 판 가장자리 한 줄. 끝나는 자리를 잡아 준다
    ins = int(20 * V)
    rule(img, int(y0) + ins, ins, W - ins, C, 0.26, max(1, int(1 * V)))
    rule(img, int(y1) - ins, ins, W - ins, C, 0.26, max(1, int(1 * V)))

    scan(img, 3, 0.055)
    specks(img, 70, int(y0), int(y1), PAPER, 0.14, seed=len(name) * 7 + 3)
    vignette(img, 0.36, 2.2)
    grain(img, 0.007, 9)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        w, h, _ = SIZES['feed']
        im = build(name, w, h)
        night(im, f'dj2_{key}_feed')
        save(im, f'dj2_{key}_feed')
        im = build(name, 1080, 1920, safe=True)
        night(im, f'dj2_{key}_story_ig')
        save(im, f'dj2_{key}_story_ig')
