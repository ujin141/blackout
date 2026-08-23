"""
**예약 전환형 판.** 1차·2차 SOLD OUT 을 시각 요소로 쓴다.

    python poster_fomo.py            피드 · 스토리 · 정사각
    python poster_fomo.py story      골라서

## 이 판이 파는 것

싸다는 게 아니라 **이미 사람들이 갔다**는 것이다. 앞의 두 차수가 닫혔다는
사실이 우리가 하는 어떤 말보다 세다 — 우리 말은 광고고 그건 증거다.

    0~1초   1차·2차 SOLD OUT. 읽는 게 아니라 보이는 크기로
    1~3초   3차 OPEN. 흰 판으로 반전시켜 유일하게 열린 문으로 보이게
    3~5초   무슨 파티인지 · 언제 · 어디 · 얼마
    5초~    80명 한정. 지금 안 하면 못 한다는 마지막 한 줄

## 왜 체크리스트인가

'3차 예약 오픈' 이라고만 쓰면 그냥 공지다. **세 줄을 위아래로 세우면
진행이 눈에 보인다** — 두 칸이 지워져 있고 한 칸만 열려 있는 그림은
설명이 필요 없다.

1·2차는 흐리게 + 취소선, 3차만 흰 판으로 반전한다. 색을 안 쓰고도
위계가 갈린다(브랜드가 흑백이라 색을 못 쓴다).

## 사진

**스톡 모델이 아니라 현장이다.** '나도 저기 가고 싶다' 는 잘 찍힌 한 사람이
아니라 **여럿이 이미 놀고 있는 그림**에서 나온다. 얼굴이 크게 잡히지 않는
와이드 컷이라 초상권도 안전하다.

`P1023234 @16.5` — 하트 네온 아래 풀에 사람이 가득하고 남녀가 섞여 있다.
0.5초마다 피부 덩어리를 세어 고른 구간이다(`reel_set` 참고).

## 값을 적는다

다른 판은 `SHOW_PRICE = False` 라 값을 안 적지만 **이 판은 예약이 목적**이라
적는다. 모바일에서 즉시 답해야 하는 네 가지가 무엇·언제·어디·얼마다.
"""
import os
import subprocess
import sys

import cv2
import numpy as np

import event as EV
from fest_kit import justify, night, specks, vignette
from fonts import KR, KRB, KRD
from poster_dj3 import chrome
from poster_dj4 import fringe
from poster_dj7 import PAPER, SILVER, STEEL, DIM
from poster_kit import (BRAND, tmask, paint, rule, box, glow, outline, grain,
                        logo, save)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), '숏폼')
CLIP, AT = 'P1023234', 16.5

SIZES = {'feed': (1080, 1350), 'story': (1080, 1920), 'sq': (1080, 1080)}


def photo(W, H):
    """현장 프레임 한 장. 원본은 2160×3840 세로다(회전 메타데이터)."""
    p = os.path.join(HERE, 'out', '_fomo_bg.png')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    r = subprocess.run(
        ['ffmpeg', '-v', 'error', '-ss', str(AT),
         '-i', os.path.join(SRC, f'{CLIP}.MOV'), '-frames:v', '1',
         # 사람 피부를 살리는 쪽. 채도를 올리면 먼저 타서 주황이 된다
         '-vf', "curves=master='0/0.016 0.25/0.22 0.5/0.52 0.75/0.80 1/0.98',"
                'vibrance=intensity=0.26,'
                'colorbalance=rm=0.02:gm=0.004:bm=0.006:rh=-0.01:bh=0.03,'
                'eq=contrast=1.12:saturation=1.04:gamma=0.98',
         '-y', p], capture_output=True, text=True, encoding='utf-8',
        errors='replace')
    if r.returncode:
        raise SystemExit(r.stderr[-800:])
    im = cv2.cvtColor(cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR),
                      cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    os.remove(p)
    h, w = im.shape[:2]
    # 판 비율에 맞춰 위아래를 자른다 — 사람이 아래쪽에 몰려 있어 위를 더 덜어낸다
    need_h = int(round(w * (H / W)))
    if need_h <= h:
        y0 = int((h - need_h) * 0.62)
        im = im[y0:y0 + need_h]
    else:
        need_w = int(round(h * (W / H)))
        x0 = int((w - need_w) * 0.5)
        im = im[:, x0:x0 + need_w]
    return cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)


def shade(img, H, W):
    """위아래를 떨군다. **가운데 한 구간은 안 건드린다** — 거기가 사진이
    사진으로 보이는 유일한 자리다.

    처음엔 위를 0.80 으로 눌렀는데 하트 네온이 밝아서 SOLD OUT 이 통째로
    묻혔다. **이 판에서 제일 중요한 글자가 안 보이면 판이 실패한 것**이라
    위쪽은 거의 검정까지 내린다 — 사진은 가운데와 아래에서 충분히 보인다."""
    y = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.955 * np.clip(1 - y / (H * 0.375), 0, 1) ** 0.85)
    img *= (1 - 0.90 * np.clip((y - H * 0.545) / (H * 0.30), 0, 1) ** 0.85)
    return img


def steps(img, W, V, y, M):
    """차수 세 줄. **두 칸이 지워져 있고 한 칸만 열린 그림**이 이 판의 전부다."""
    rows = [(n, got >= cap) for n, cap, got, _ in EV.WAVES]
    h = int(74 * V)
    for name, done in rows:
        if done:
            paint(img, tmask(name, KRD, int(46 * V), 0.01), M, y + h * 0.5,
                  color=PAPER, a=0.72, anchor='l')
            t = tmask('SOLD OUT', BRAND, int(38 * V), 0.16)
            paint(img, t, W - M, y + h * 0.5, color=PAPER, a=0.74, anchor='r')
            # 취소선 — 끝났다는 걸 글자 스스로 말한다
            rule(img, y + h * 0.5, W - M - t.shape[1], W - M, PAPER, 0.80,
                 max(3, int(4 * V)))
        else:
            box(img, M - 14 * V, y + 2 * V, W - M + 14 * V, y + h - 2 * V,
                PAPER, 0.97)
            paint(img, tmask(name, KRD, int(46 * V), 0.01), M, y + h * 0.5,
                  color=np.float32([0.02, 0.02, 0.03]), anchor='l')
            paint(img, tmask('OPEN', BRAND, int(40 * V), 0.18), W - M,
                  y + h * 0.5, color=np.float32([0.02, 0.02, 0.03]), anchor='r')
        y += h + int(12 * V)
    return y


def build(W, H, story=False):
    V = W / 1080.0
    M = int(W * 0.088)
    y0, y1 = (H * 0.085, H * 0.876) if story else (H * 0.028, H * 0.974)

    img = shade(photo(W, H), H, W)

    # ── 머리 ─────────────────────────────────────────────
    paint(img, tmask('BLACKOUT CREW', BRAND, int(15 * V), 0.34), M, y0 + 34 * V,
          color=SILVER, a=0.88, anchor='l')
    paint(img, tmask(EV.DATE_EN, BRAND, int(15 * V), 0.22), W - M, y0 + 34 * V,
          color=SILVER, a=0.88, anchor='r')

    # ── 차수 — 최우선 ────────────────────────────────────
    y = steps(img, W, V, y0 + 74 * V, M)

    # ── 무슨 파티인가 ────────────────────────────────────
    ny = y + 96 * V
    ns = justify(EV.NAME, W - M * 2, 0.06, cap=int(104 * V))
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    img *= (1 - 0.38 * np.exp(-((yy - ny) / (ns * 0.80)) ** 2))
    nm = tmask(EV.NAME, BRAND, ns, 0.06)
    glow(img, nm, W / 2, ny, SILVER, 0.22, int(24 * V), anchor='c')
    chrome(img, nm, W / 2, ny, PAPER, STEEL)
    paint(img, outline(nm, max(2, int(2.4 * V))), W / 2, ny, color=PAPER,
          a=0.92, anchor='c')
    paint(img, tmask(EV.FORMAT, BRAND, int(19 * V), 0.32), W / 2, ny + ns * 0.70,
          color=SILVER, a=0.90, anchor='c')
    paint(img, tmask('혼자 와도, 친구랑 와도', KRB, int(29 * V), 0.01), W / 2,
          ny + ns * 0.70 + 62 * V, color=PAPER, a=0.96, anchor='c')

    # ── 언제 · 어디 ──────────────────────────────────────
    fy = y1 - (208 if story else 196) * V
    paint(img, tmask(f'{EV.DATE}  ·  {EV.TIME}', KRD, int(38 * V), 0.01),
          W / 2, fy - 168 * V, color=PAPER, anchor='c')
    paint(img, tmask(f'{EV.VENUE}  ·  양재', KRB, int(27 * V), 0.01),
          W / 2, fy - 118 * V, color=SILVER, a=0.94, anchor='c')

    # ── 얼마 ─────────────────────────────────────────────
    # **다른 판은 값을 안 적는다.** 이 판만 적는다 — 예약이 목적이라
    # 모바일에서 '얼마' 에 즉시 답해야 한다
    pr = EV.PRICE.get(EV.OPEN_WAVE[0]) if EV.OPEN_WAVE else None
    if pr:
        paint(img, tmask(f"여 {pr['여']:,}   ·   남 {pr['남']:,}", KRD,
                         int(34 * V), 0.01), W / 2, fy - 58 * V,
              color=PAPER, anchor='c')
    rule(img, fy - 16 * V, M, W - M, SILVER, 0.30, max(1, int(2 * V)))

    # ── 한정 · 혜택 ──────────────────────────────────────
    paint(img, tmask(f'{EV.CAP}명 한정  ·  {EV.PERKS} 포함', KRB, int(24 * V),
                     0.01), W / 2, fy + 28 * V, color=SILVER, a=0.94, anchor='c')

    # ── 예약 ─────────────────────────────────────────────
    bh = int(72 * V)
    by = fy + 66 * V
    box(img, M, by, W - M, by + bh, PAPER, 0.97)
    paint(img, tmask(f'{EV.OPEN_WAVE[0]} 사전예약 OPEN', KRD, int(31 * V), 0.01),
          W / 2, by + bh * 0.5, color=np.float32([0.02, 0.02, 0.03]), anchor='c')
    paint(img, tmask(EV.RESERVE, KRB, int(19 * V), 0.01), W / 2, by + bh + 34 * V,
          color=SILVER, a=0.90, anchor='c')

    if story:
        rule(img, int(y1), 0, W, SILVER, 0.28, max(1, int(2 * V)))

    specks(img, 70, 0, int(H * 0.30), PAPER, 0.10, seed=67, rmax=2.0)
    fringe(img, 0.0010)
    vignette(img, 0.32, 2.4)
    grain(img, 0.005, 31)
    return np.clip(img, 0, 1)


if __name__ == '__main__':
    want = [a.lower() for a in sys.argv[1:]] or list(SIZES)
    for k in want:
        if k not in SIZES:
            raise SystemExit(f'{k} 은 없는 크기입니다 — {", ".join(SIZES)}')
        w, h = SIZES[k]
        im = build(w, h, story=(k == 'story'))
        night(im, f'fomo_{k}')
        save(im, f'fomo_{k}')
