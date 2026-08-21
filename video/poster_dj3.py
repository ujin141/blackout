"""
**DJ 한 명짜리 판 — C안.** 강남 클럽 게스트 포스터 문법.

    python poster_dj3.py                 일곱 명 전부
    python poster_dj3.py lynn chips      골라서

우진이 준 레퍼런스는 **Arkins** 판입니다 — 강남 클럽씬 로컬 1군, 월디페·워터밤·
S2O 라인업에 이름이 걸리는 DJ입니다. 그 판들의 문법은 우리 A·B안과 다릅니다.

    이름이 제일 크다      인물보다 크다. 판을 좌우로 넘칠 만큼 굵고 크게
    크롬                  글자를 단색으로 안 채운다. 위아래로 빛이 흐르는 금속
    빛이 뒤에서 온다      백라이트 · 부챗살 빔 · 렌즈 플레어. 무대 위에 선 사진처럼
    색이 두 개 부딪힌다   한쪽에서 자기 색, 반대쪽에서 짝색이 인물을 때린다
    반짝임                파티클. 없으면 그냥 어두운 판이다

A안은 얌전하고 B안은 편집 디자인 쪽입니다. **이건 클럽 판입니다** — 셋 중
제일 시끄럽고, 이 행사가 파는 게 그겁니다.

## 크롬 글자를 어떻게 만드나

폰트가 한 벌(Michroma Regular)뿐이라 굵은 글자가 없습니다. 마스크를 부풀려서
(`cv2.dilate`) 굵기를 만들고, 그 안을 **세로 그라데이션**으로 채웁니다 —
위 밝음 → 가운데 어두움 → 아래 밝음이 금속으로 읽히는 최소 조건입니다.
단색으로 채우면 그냥 흰 글자입니다.
"""
import sys
import numpy as np
import cv2
from poster_kit import (BRAND, SIZES, tmask, paint, fit, rule, glow, outline,
                        grain, save, sign, bloom, add)
from poster_crew import crop_head, crown
from fest_kit import justify, night, vignette, sky, beams, specks
from fonts import KR, KRB
from members import get
from poster_dj import HUE, LINE
from poster_dj2 import MATE
import event as EV

PAPER = np.float32([0.97, 0.97, 0.95])
DIM   = np.float32([0.62, 0.64, 0.68])

ORDER = EV.LINEUP
SET_AT = {n: (s, e) for s, e, n in EV.TIMETABLE}

# 크롬 램프. (세로 위치, 밝기) — 위 밝음 → 가운데 어두움 → 아래 다시 밝음.
# **가운데가 어두워야 금속이다.** 위아래만 밝게 하면 그냥 흐린 글자가 된다.
CHROME = [(0.00, 1.00), (0.30, 0.86), (0.46, 0.30), (0.54, 0.34),
          (0.72, 0.95), (1.00, 0.66)]


def ramp(h, stops, tint_hi, tint_lo):
    """세로 그라데이션 한 줄. 밝은 데는 흰빛, 어두운 데는 색이 돈다."""
    ys = np.linspace(0, 1, h, dtype=np.float32)
    v = np.interp(ys, [s for s, _ in stops], [t for _, t in stops]).astype(np.float32)
    return (tint_lo[None, :] * (1 - v[:, None]) + tint_hi[None, :] * v[:, None]) * \
           (0.35 + 0.65 * v[:, None])


def chrome(dst, m, x, y, tint_hi, tint_lo, anchor='c', valign='c'):
    """글자 마스크를 세로 그라데이션으로 채운다. paint() 는 단색이라 직접 얹는다."""
    H, W = dst.shape[:2]
    a = m.astype(np.float32) / 255.0
    h, w = a.shape
    col = ramp(h, CHROME, tint_hi, tint_lo)[:, None, :]
    x0 = int(x) if anchor == 'l' else (int(x - w) if anchor == 'r' else int(x - w / 2))
    y0 = int(y) if valign == 't' else int(y - h / 2)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(W, x0 + w), min(H, y0 + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    sub = a[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0][..., None]
    c = np.broadcast_to(col[sy0 - y0:sy1 - y0], (sy1 - sy0, sx1 - sx0, 3))
    dst[sy0:sy1, sx0:sx1] = dst[sy0:sy1, sx0:sx1] * (1 - sub) + c * sub


def bold(m, th):
    """마스크를 부풀려 굵게. **폰트가 한 벌이라 굵기를 직접 만든다.**"""
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (th * 2 + 1, th * 2 + 1))
    return cv2.dilate(m, k)


def flare(img, cx, cy, r, color, a):
    """렌즈 플레어 한 점 — 가로로 길게 늘인 빛."""
    H, W = img.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    core = np.exp(-(((xx - cx) / (r * 0.30)) ** 2 + ((yy - cy) / (r * 0.30)) ** 2))
    streak = np.exp(-(((xx - cx) / (r * 2.6)) ** 2 + ((yy - cy) / (r * 0.055)) ** 2))
    img += (core * 0.75 + streak)[..., None] * color * a


def rim(dst, al, color, dx, a, px):
    """한쪽에서 때리는 빛. 실루엣을 밀어서 겹치지 않는 쪽만 남긴다."""
    k = np.ones((px, px), np.uint8)
    edge = np.clip(cv2.dilate(al, k) - al, 0, 1)
    m = np.zeros_like(edge)
    if dx >= 0:
        m[:, dx:] = edge[:, :edge.shape[1] - dx] if dx else edge
    else:
        m[:, :dx] = edge[:, -dx:]
    m = cv2.GaussianBlur(m, (0, 0), px * 0.8)
    dst += (m / max(m.max(), 1e-6))[..., None] * color * a


def build(name, W, H, safe=False):
    V = W / 1080.0
    C, C2 = HUE[name], MATE[name]
    y0, y1 = (H * 0.100, H * 0.868) if safe else (0.0, float(H))
    BH = y1 - y0
    M = int(W * 0.070)

    # ── 판 ───────────────────────────────────────────────
    img = sky(W, H, [(0.0, (0.020, 0.020, 0.030)), (0.42, (0.036, 0.030, 0.052)),
                     (1.0, (0.012, 0.012, 0.020))])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # 두 색이 좌우에서 부딪힌다
    img += np.exp(-(((xx - W * 0.14) / (W * 0.52)) ** 2
                    + ((yy - (y0 + BH * 0.40)) / (BH * 0.52)) ** 2))[..., None] * C2 * 0.085
    img += np.exp(-(((xx - W * 0.90) / (W * 0.52)) ** 2
                    + ((yy - (y0 + BH * 0.34)) / (BH * 0.50)) ** 2))[..., None] * C * 0.10

    # 뒤에서 내려오는 부챗살. **빔이 있어야 무대 위로 읽힌다**
    beams(img, W * 0.50, y0 + BH * 0.10, 13, 0.72, BH * 0.92, C, 0.10, seed=len(name) + 5)
    flare(img, W * 0.50, y0 + BH * 0.245, W * 0.34, C * 0.5 + PAPER * 0.5, 0.16)

    # ── 사람 ─────────────────────────────────────────────
    hero_h = int(BH * 0.640)
    top = int(y0 + BH * 0.202)
    fig = crop_head(name, W, hero_h)
    al = fig[..., 3]
    al = crown(al)          # 정수리를 녹인다
    sl = (slice(top, min(H, top + hero_h)), slice(0, W))
    n = sl[0].stop - sl[0].start
    a_ = al[:n]

    rim(img[sl], a_, C, int(9 * V), 0.85, max(3, int(7 * V)))
    rim(img[sl], a_, C2, -int(9 * V), 0.85, max(3, int(7 * V)))

    g = (fig[..., 0] * .299 + fig[..., 1] * .587 + fig[..., 2] * .114)
    g = np.clip((g - 0.5) * 1.30 + 0.5, 0, 1)
    g = np.where(g > 0.74, 0.74 + (g - 0.74) * 0.46, g)[..., None]
    px = (np.repeat(g, 3, 2) * (1 - 0.20 * (1 - g)) + C * (1 - g) * 0.20) * 0.92
    img[sl] = img[sl] * (1 - a_[..., None]) + px[:n] * a_[..., None]

    fade = int(BH * 0.15)
    fy = min(H, top + hero_h) - fade
    if fy > 0:
        t = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None] ** 1.5
        img[fy:fy + fade] *= (1 - t * 0.95)

    # ── 아래 블록 ────────────────────────────────────────
    # **아래에서부터 쌓는다.** 처음엔 이름 크기에서 아래로 내려갔는데,
    # 이름이 250px 까지 커지자 계정 줄이 AFTER SUNSET 위로 올라탔다 —
    # 줄 수가 사람마다 다르니(DEMIC 은 장르가 없다) 바닥을 기준으로 잡는다
    s, e = SET_AT[name]
    gs = get(name)['genres']['ko'][:4]
    ig = get(name)['instagram']

    yb = y1 - 30 * V
    paint(img, tmask(f'{EV.DATE_EN}  ·  {EV.VENUE}  ·  {EV.ADDR}', KR, int(16 * V), 0.02),
          W / 2, yb, color=DIM, a=0.88, anchor='c')
    yb -= 36 * V
    paint(img, tmask(EV.NAME, BRAND, int(30 * V), 0.16), W / 2, yb, color=PAPER, anchor='c')
    if ig:
        yb -= 40 * V
        paint(img, tmask('@' + ig, KR, int(17 * V), 0.02), W / 2, yb, color=DIM,
              a=0.90, anchor='c')
    if gs:
        yb -= 34 * V
        paint(img, tmask('  /  '.join(gs), KR, int(20 * V), 0.02), W / 2, yb,
              color=C * 0.45 + PAPER * 0.55, anchor='c')
    yb -= 44 * V
    paint(img, tmask(LINE[name], KRB, int(32 * V), 0.01), W / 2, yb, color=PAPER, anchor='c')
    yb -= 30 * V
    rule(img, yb, W * 0.18, W * 0.82, C, 0.55, max(1, int(2 * V)))

    # ── 이름 ─────────────────────────────────────────────
    # **인물보다 크다.** 클럽 판에서 제일 큰 건 언제나 이름이다
    ns = justify(name, W * 0.94, 0.02, cap=int(250 * V))
    ny = yb - ns * 0.52
    raw = tmask(name, BRAND, ns, 0.02)
    m = bold(raw, max(2, int(ns * 0.030)))
    glow(img, m, W / 2, ny, C, 0.50, int(34 * V), anchor='c')
    paint(img, outline(m, max(2, int(4 * V))), W / 2, ny, color=C2, a=0.85, anchor='c')
    chrome(img, m, W / 2, ny, PAPER, C * 0.55 + np.float32([0.05, 0.05, 0.08]))

    # ── 머리 ─────────────────────────────────────────────
    sign(img, M, y0 + BH * 0.058, size=int(13 * V), color=DIM, a=0.90, anchor='l')
    paint(img, tmask(f'{s} — {e}', BRAND, int(23 * V), 0.20), W - M, y0 + BH * 0.058,
          color=PAPER, anchor='r')

    if safe:
        img[:int(y0)] *= 0.0
        img[int(y1):] *= 0.0

    specks(img, 150, int(y0), int(y1), PAPER, 0.22, seed=len(name) * 11 + 2, rmax=3.0)
    bloom(img, 0.80, 18 * V, 0.26, PAPER)
    vignette(img, 0.40, 2.1)
    grain(img, 0.005, 11)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.upper() for a in sys.argv[1:]] or ORDER
    for name in want:
        if name not in HUE:
            raise SystemExit(f'{name} 은 라인업에 없습니다 — {", ".join(ORDER)}')
        key = name.lower()
        w, h, _ = SIZES['feed']
        im = build(name, w, h)
        night(im, f'dj3_{key}_feed')
        save(im, f'dj3_{key}_feed')
        im = build(name, 1080, 1920, safe=True)
        night(im, f'dj3_{key}_story_ig')
        save(im, f'dj3_{key}_story_ig')
